/* gz_video_bridge — stream a Gazebo camera as Tello-format video.
 *
 * Subscribes to a gz camera image topic, encodes H.264 (libx264, zerolatency,
 * repeated headers) and sends raw Annex-B over UDP to <client>:11111 — the
 * exact wire format a real Tello (and the STRATOSDRONE firmware) produces, so
 * djitellopy's get_frame_read() works against the simulator.
 *
 *   ./gz_video_bridge --topic /world/playground/.../camera/image \
 *                     --client 127.0.0.1 [--port 11111] [--bitrate 2000]
 *
 * Requires a world with the sensors system (rendering); see playground.sdf.
 * SPDX-License-Identifier: MIT */
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <atomic>
#include <csignal>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <mutex>
#include <string>
#include <vector>

#include <gz/msgs/image.pb.h>
#include <gz/transport/Node.hh>

extern "C" {
#include <stdint.h>
#include <x264.h>
}

static std::atomic<bool> g_stop{false};
static void OnSig(int) { g_stop = true; }

class Encoder
{
public:
  bool Init(int w, int h, int fps, int kbps)
  {
    x264_param_t p;
    x264_param_default_preset(&p, "ultrafast", "zerolatency");
    p.i_width = w;
    p.i_height = h;
    p.i_csp = X264_CSP_I420;
    p.i_fps_num = fps;
    p.i_fps_den = 1;
    p.i_keyint_max = fps;            /* one IDR per second */
    p.b_repeat_headers = 1;          /* SPS/PPS with every keyframe */
    p.b_annexb = 1;
    p.rc.i_rc_method = X264_RC_ABR;
    p.rc.i_bitrate = kbps;
    p.rc.i_vbv_max_bitrate = kbps * 3 / 2;
    p.rc.i_vbv_buffer_size = kbps;
    x264_param_apply_profile(&p, "baseline");
    enc = x264_encoder_open(&p);
    if (!enc)
      return false;
    x264_picture_alloc(&pic, X264_CSP_I420, w, h);
    width = w;
    height = h;
    return true;
  }

  /* RGB888 -> I420 -> H.264 access units (Annex-B) */
  bool Encode(const uint8_t *rgb, std::vector<uint8_t> &out)
  {
    const int w = width, h = height;
    uint8_t *Y = pic.img.plane[0], *U = pic.img.plane[1], *V = pic.img.plane[2];
    const int sy = pic.img.i_stride[0], su = pic.img.i_stride[1], sv = pic.img.i_stride[2];
    for (int j = 0; j < h; j++) {
      for (int i = 0; i < w; i++) {
        const uint8_t *px = rgb + 3 * (j * w + i);
        const int r = px[0], g = px[1], b = px[2];
        Y[j * sy + i] = uint8_t(((66 * r + 129 * g + 25 * b + 128) >> 8) + 16);
        if ((i & 1) == 0 && (j & 1) == 0) {
          U[(j / 2) * su + i / 2] = uint8_t(((-38 * r - 74 * g + 112 * b + 128) >> 8) + 128);
          V[(j / 2) * sv + i / 2] = uint8_t(((112 * r - 94 * g - 18 * b + 128) >> 8) + 128);
        }
      }
    }
    pic.i_pts = pts++;
    x264_nal_t *nal = nullptr;
    int n = 0;
    x264_picture_t out_pic;
    const int sz = x264_encoder_encode(enc, &nal, &n, &pic, &out_pic);
    if (sz < 0)
      return false;
    out.clear();
    for (int i = 0; i < n; i++)
      out.insert(out.end(), nal[i].p_payload, nal[i].p_payload + nal[i].i_payload);
    return !out.empty();
  }

private:
  x264_t *enc{nullptr};
  x264_picture_t pic{};
  int64_t pts{0};
  int width{0}, height{0};
};

int main(int argc, char **argv)
{
  std::string topic, client = "127.0.0.1";
  int port = 11111, kbps = 2000;
  for (int i = 1; i < argc - 1; i++) {
    std::string a = argv[i];
    if (a == "--topic") topic = argv[++i];
    else if (a == "--client") client = argv[++i];
    else if (a == "--port") port = atoi(argv[++i]);
    else if (a == "--bitrate") kbps = atoi(argv[++i]);
  }
  if (topic.empty()) {
    std::cerr << "usage: gz_video_bridge --topic <gz image topic> [--client IP]"
                 " [--port 11111] [--bitrate kbps]\n";
    return 1;
  }
  std::signal(SIGINT, OnSig);
  std::signal(SIGTERM, OnSig);

  int sock = socket(AF_INET, SOCK_DGRAM, 0);
  sockaddr_in dst{};
  dst.sin_family = AF_INET;
  dst.sin_port = htons(uint16_t(port));
  inet_pton(AF_INET, client.c_str(), &dst.sin_addr);

  Encoder enc;
  std::mutex m;
  bool inited = false;

  gz::transport::Node node;
  auto cb = [&](const gz::msgs::Image &img) {
    if (img.pixel_format_type() != gz::msgs::PixelFormatType::RGB_INT8)
      return;
    std::lock_guard<std::mutex> lk(m);
    if (!inited) {
      if (!enc.Init(int(img.width()), int(img.height()), 30, kbps)) {
        std::cerr << "x264 init failed\n";
        g_stop = true;
        return;
      }
      std::cout << "[bridge] " << img.width() << "x" << img.height()
                << " -> " << client << ":" << port << " @" << kbps << " kbps\n";
      inited = true;
    }
    std::vector<uint8_t> au;
    if (!enc.Encode(reinterpret_cast<const uint8_t *>(img.data().data()), au))
      return;
    /* Tello-style: raw Annex-B stream chopped into <=1460-byte datagrams */
    const size_t chunk = 1460;
    for (size_t off = 0; off < au.size(); off += chunk) {
      const size_t len = std::min(chunk, au.size() - off);
      sendto(sock, au.data() + off, len, 0,
             reinterpret_cast<sockaddr *>(&dst), sizeof(dst));
    }
  };

  if (!node.Subscribe(topic, std::function<void(const gz::msgs::Image &)>(cb))) {
    std::cerr << "cannot subscribe " << topic << "\n";
    return 1;
  }
  std::cout << "[bridge] subscribed to " << topic << "\n";
  while (!g_stop)
    usleep(100000);
  close(sock);
  return 0;
}
