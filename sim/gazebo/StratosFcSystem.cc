/* StratosFcSystem — Gazebo Harmonic (gz-sim8) system plugin that embeds the
 * STRATOSDRONE flight core and exposes the Tello SDK 2.0 UDP surface.
 *
 * One instance per drone model:
 *
 *   <plugin filename="StratosFcSystem" name="stratos::StratosFcSystem">
 *     <bind_ip>127.0.0.2</bind_ip>   <!-- unique per drone (loopback swarm) -->
 *     <link_name>base_link</link_name>
 *     <seed>7</seed>
 *   </plugin>
 *
 * Physics contract: world step <= 1 ms (the control loop runs per step).
 * Rotor thrust uses the same first-order-lag linear model as the SIL plant
 * (fc_core/test/sil_plant.c) so controller behavior matches the host tests;
 * forces are applied directly to the base link. Flow/ToF/baro are synthesized
 * from ground truth with the same noise models — fully headless, no rendering
 * or GPU needed.
 * SPDX-License-Identifier: MIT */
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <atomic>
#include <chrono>
#include <cstring>
#include <deque>
#include <mutex>
#include <random>
#include <string>
#include <thread>

#include <gz/math/Pose3.hh>
#include <gz/math/Vector3.hh>
#include <gz/plugin/Register.hh>
#include <gz/sim/Link.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/System.hh>
#include <gz/sim/Util.hh>

extern "C" {
#include "fc_core/fc_core.h"
#include "fc_core/fc_sdk.h"
}

namespace stratos
{

class StratosFcSystem : public gz::sim::System,
                        public gz::sim::ISystemConfigure,
                        public gz::sim::ISystemPreUpdate
{
public:
  ~StratosFcSystem() override
  {
    this->stop = true;
    if (this->netThread.joinable())
      this->netThread.join();
    if (this->sock >= 0)
      close(this->sock);
  }

  void Configure(const gz::sim::Entity &entity,
                 const std::shared_ptr<const sdf::Element> &sdf,
                 gz::sim::EntityComponentManager &ecm,
                 gz::sim::EventManager &) override
  {
    this->model = gz::sim::Model(entity);
    const std::string linkName = sdf->Get<std::string>("link_name", "base_link").first;
    this->link = gz::sim::Link(this->model.LinkByName(ecm, linkName));
    if (!this->link.Valid(ecm)) {
      gzerr << "[stratos] link '" << linkName << "' not found\n";
      return;
    }
    this->link.EnableVelocityChecks(ecm, true);
    this->link.EnableAccelerationChecks(ecm, true);

    this->bindIp = sdf->Get<std::string>("bind_ip", "127.0.0.2").first;
    unsigned seed = sdf->Get<unsigned>("seed", 42).first;
    this->rng.seed(seed);
    this->sn = "STRATOSGZ" + this->bindIp.substr(this->bindIp.rfind('.') + 1);

    fc_core_init(&this->fc);
    static const fc_sdk_platform_t plat = {
        /* send_reply  */ [](void *u, const char *m) { static_cast<StratosFcSystem *>(u)->SendReply(m); },
        /* video_ctrl  */ [](void *u, bool on, int h) { static_cast<StratosFcSystem *>(u)->VideoCtrl(on, h); },
        /* set_led     */ [](void *u, uint8_t r, uint8_t g, uint8_t b) {
                            gzmsg << "[stratos " << static_cast<StratosFcSystem *>(u)->bindIp
                                  << "] led " << int(r) << " " << int(g) << " " << int(b) << "\n"; },
        /* wifi_config */ nullptr,
        /* get_sn      */ [](void *u) -> const char * { return static_cast<StratosFcSystem *>(u)->sn.c_str(); },
        /* get_wifi_snr*/ [](void *u) -> int { (void)u; return 90; },
    };
    fc_sdk_init(&this->sdk, &this->fc, &plat, this);

    this->OpenSocket();
    if (this->sock >= 0)
      this->netThread = std::thread([this] { this->NetLoop(); });
    gzdbg << "[stratos] instance " << this << " entity " << entity
          << " model '" << this->model.Name(ecm)
          << "' SDK on " << this->bindIp << ":8889\n";
  }

  void PreUpdate(const gz::sim::UpdateInfo &info,
                 gz::sim::EntityComponentManager &ecm) override
  {
    if (info.paused || !this->link.Valid(ecm))
      return;
    const double dt = std::chrono::duration<double>(info.dt).count();
    if (dt <= 0.0)
      return;

    /* ---------------- ground truth ---------------- */
    const auto poseOpt = this->link.WorldPose(ecm);
    const auto velOpt = this->link.WorldLinearVelocity(ecm);
    const auto omgOpt = this->link.WorldAngularVelocity(ecm);
    const auto accOpt = this->link.WorldLinearAcceleration(ecm);
    if (!poseOpt)
      return;
    const gz::math::Pose3d pose = *poseOpt;
    const gz::math::Vector3d vw = velOpt.value_or(gz::math::Vector3d::Zero);
    const gz::math::Vector3d ww = omgOpt.value_or(gz::math::Vector3d::Zero);
    const gz::math::Vector3d aw = accOpt.value_or(gz::math::Vector3d::Zero);
    const gz::math::Quaterniond &q = pose.Rot();

    /* ---------------- IMU (body frame, with noise + bias) ---------------- */
    const gz::math::Vector3d gyroB = q.RotateVectorReverse(ww);
    /* specific force f = a - g; gz acceleration includes gravity effects */
    const gz::math::Vector3d fW = aw + gz::math::Vector3d(0, 0, FC_G);
    const gz::math::Vector3d accB = q.RotateVectorReverse(fW);
    fc_imu_t imu;
    imu.gyro[0] = float(gyroB.X()) + this->gyroBias[0] + this->Gauss(0.015f);
    imu.gyro[1] = float(gyroB.Y()) + this->gyroBias[1] + this->Gauss(0.015f);
    imu.gyro[2] = float(gyroB.Z()) + this->gyroBias[2] + this->Gauss(0.015f);
    imu.accel[0] = float(accB.X()) + this->Gauss(0.25f);
    imu.accel[1] = float(accB.Y()) + this->Gauss(0.25f);
    imu.accel[2] = float(accB.Z()) + this->Gauss(0.25f);
    fc_core_imu_update(&this->fc, &imu, float(dt));

    /* ---------------- decimated sensors (same models as SIL) ------------- */
    const double z = pose.Pos().Z();
    if (this->tick % 10 == 3) { /* 100 Hz optical flow */
      const double h = z > 0.03 ? z : 0.03;
      const gz::math::Vector3d vB = q.RotateVectorReverse(vw);
      const double fx = gyroB.Y() - vB.X() / h;
      const double fy = -gyroB.X() - vB.Y() / h;
      const float dtf = 0.010f;
      fc_flow_t fl;
      const float cpr = this->fc.par.flow_cpr;
      fl.dx = int16_t(fc_clampf(float(fx) * cpr * dtf + this->Gauss(1.2f), -32000.f, 32000.f));
      fl.dy = int16_t(fc_clampf(float(fy) * cpr * dtf + this->Gauss(1.2f), -32000.f, 32000.f));
      const double tiltCos = 1.0 - 2.0 * (q.X() * q.X() + q.Y() * q.Y());
      fl.quality = uint8_t((z > 0.06 && z < 3.5 && tiltCos > 0.75) ? 120 : 25);
      fc_core_flow_update(&this->fc, &fl, dtf);
    }
    if (this->tick % 20 == 7) { /* 50 Hz ToF */
      const double tiltCos = 1.0 - 2.0 * (q.X() * q.X() + q.Y() * q.Y());
      bool valid = tiltCos > 0.5 && z < 3.9;
      float range = valid ? float(z / tiltCos) + this->Gauss(0.008f) : 8.19f;
      fc_core_tof_update(&this->fc, range < 0.f ? 0.f : range, valid);
    }
    if (this->tick % 20 == 13) { /* 50 Hz baro */
      const double alt = 35.0 + z + this->Gauss(0.35f);
      const double pa = 101325.0 * std::pow(1.0 - 2.25577e-5 * alt, 5.25588);
      fc_core_baro_update(&this->fc, float(pa));
    }
    if (this->tick % 100 == 51)
      fc_core_battery_update(&this->fc, 4.12f);

    /* ---------------- SDK pump ---------------- */
    {
      std::lock_guard<std::mutex> lk(this->qMutex);
      while (!this->cmdQueue.empty()) {
        fc_sdk_handle_line(&this->sdk, this->cmdQueue.front().c_str());
        this->cmdQueue.pop_front();
      }
    }
    if (this->tick % 5 == 0)
      fc_sdk_poll(&this->sdk);
    if (this->tick % 100 == 0 && this->haveClient.load()) {
      char st[256];
      const int len = fc_sdk_state_string(&this->sdk, st, sizeof(st));
      sockaddr_in dst{};
      {
        std::lock_guard<std::mutex> lk(this->clientMutex);
        dst = this->client;
      }
      dst.sin_port = htons(8890);
      sendto(this->sock, st, size_t(len), 0,
             reinterpret_cast<sockaddr *>(&dst), sizeof(dst));
    }

    /* ---------------- motors -> wrench on base link ---------------- */
    float duty[4];
    fc_core_get_motors(&this->fc, duty);
    /* geometry/coefficients mirror fc_core/test/sil_plant.c */
    static const double kMx[4] = {+1, -1, -1, +1};
    static const double kMy[4] = {-1, -1, +1, +1};
    static const double kCw[4] = {-1, +1, -1, +1};
    const double arm = 0.0417, kT = 0.42, cQ = 0.006, tau = 0.06;
    double Ftot = 0;
    gz::math::Vector3d tq(0, 0, 0);
    for (int i = 0; i < 4; i++) {
      this->thrLag[i] += (double(duty[i]) - this->thrLag[i]) * dt / tau;
      const double F = kT * this->thrLag[i];
      Ftot += F;
      tq.X() += kMy[i] * arm * F;
      tq.Y() += -kMx[i] * arm * F;
      tq.Z() += kCw[i] * cQ * F;
    }
    /* linear aero drag, as in the SIL plant */
    const gz::math::Vector3d dragW = -0.06 * vw;
    const gz::math::Vector3d forceW = q.RotateVector(gz::math::Vector3d(0, 0, Ftot)) + dragW;
    const gz::math::Vector3d torqueW = q.RotateVector(tq);
    this->link.AddWorldWrench(ecm, forceW, torqueW);

    this->tick++;
  }

private:
  float Gauss(float sigma)
  {
    return sigma * this->gauss(this->rng);
  }

  void OpenSocket()
  {
    this->sock = socket(AF_INET, SOCK_DGRAM, 0);
    int one = 1;
    setsockopt(this->sock, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    timeval tv{0, 100000}; /* 100 ms recv timeout so the thread can exit */
    setsockopt(this->sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(8889);
    if (inet_pton(AF_INET, this->bindIp.c_str(), &addr.sin_addr) != 1 ||
        bind(this->sock, reinterpret_cast<sockaddr *>(&addr), sizeof(addr)) != 0) {
      gzerr << "[stratos] cannot bind " << this->bindIp << ":8889 — "
            << std::strerror(errno) << "\n";
      close(this->sock);
      this->sock = -1;
    }
  }

  void NetLoop()
  {
    char buf[256];
    while (!this->stop) {
      sockaddr_in src{};
      socklen_t slen = sizeof(src);
      const ssize_t r = recvfrom(this->sock, buf, sizeof(buf) - 1, 0,
                                 reinterpret_cast<sockaddr *>(&src), &slen);
      if (r <= 0)
        continue;
      buf[r] = '\0';
      {
        std::lock_guard<std::mutex> lk(this->clientMutex);
        this->client = src;
      }
      this->haveClient = true;
      {
        std::lock_guard<std::mutex> lk(this->qMutex);
        this->cmdQueue.emplace_back(buf);
      }
    }
  }

  void SendReply(const char *msg)
  {
    if (!this->haveClient.load() || this->sock < 0)
      return;
    sockaddr_in dst{};
    {
      std::lock_guard<std::mutex> lk(this->clientMutex);
      dst = this->client;
    }
    sendto(this->sock, msg, std::strlen(msg), 0,
           reinterpret_cast<sockaddr *>(&dst), sizeof(dst));
  }

  void VideoCtrl(bool on, int height)
  {
    gzmsg << "[stratos " << this->bindIp << "] video " << (on ? "on" : "off")
          << " " << height << "p (run gz_video_bridge for the stream)\n";
  }

  gz::sim::Model model{gz::sim::kNullEntity};
  gz::sim::Link link{gz::sim::kNullEntity};
  std::string bindIp{"127.0.0.2"};
  std::string sn;

  fc_core_t fc{};
  fc_sdk_t sdk{};
  uint64_t tick{0};
  double thrLag[4]{0, 0, 0, 0};
  float gyroBias[3]{0.008f, -0.006f, 0.004f};

  std::mt19937 rng;
  std::normal_distribution<float> gauss{0.0f, 1.0f};

  int sock{-1};
  std::thread netThread;
  std::atomic<bool> stop{false};
  std::atomic<bool> haveClient{false};
  std::mutex clientMutex, qMutex;
  sockaddr_in client{};
  std::deque<std::string> cmdQueue;
};

}  // namespace stratos

GZ_ADD_PLUGIN(stratos::StratosFcSystem, gz::sim::System,
              stratos::StratosFcSystem::ISystemConfigure,
              stratos::StratosFcSystem::ISystemPreUpdate)
GZ_ADD_PLUGIN_ALIAS(stratos::StratosFcSystem, "stratos::StratosFcSystem")
