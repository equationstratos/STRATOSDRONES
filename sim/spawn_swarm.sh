#!/usr/bin/env bash
# Launch a Gazebo Harmonic world with N STRATOSDRONEs on 127.0.0.2..(N+1).
#
#   ./spawn_swarm.sh           # 1 drone, headless server, RTF 1
#   ./spawn_swarm.sh 3         # 3 drones
#   GUI=1 ./spawn_swarm.sh 2   # with the Gazebo GUI
#   RTF=4 ./spawn_swarm.sh 3   # accelerated (CI-style)
#
# Then fly with djitellopy / stratospy:
#   python sdk/python/examples/03_swarm.py        (after editing IPs if needed)
set -euo pipefail
N="${1:-1}"
RTF="${RTF:-1}"
GUI="${GUI:-0}"

HERE="$(cd "$(dirname "$0")" && pwd)"
GZ_BIN="${GZ_BIN:-$(command -v gz || echo /opt/gzenv/bin/gz)}"
export GZ_SIM_SYSTEM_PLUGIN_PATH="$HERE/build"
export GZ_SIM_RESOURCE_PATH="$HERE/models"
if [ -d /opt/gzenv/lib ] && [[ "$GZ_BIN" == /opt/gzenv/* ]]; then
    export LD_LIBRARY_PATH="/opt/gzenv/lib:${LD_LIBRARY_PATH:-}"
fi

WORLD="$(mktemp /tmp/stratos_swarm_XXXX.sdf)"
{
cat <<EOF
<?xml version="1.0"?>
<sdf version="1.9">
  <world name="swarm">
    <physics name="p" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>$RTF</real_time_factor>
    </physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <gravity>0 0 -9.80665</gravity>
    <model name="ground"><static>true</static><link name="l">
      <collision name="c"><geometry><plane><normal>0 0 1</normal><size>60 60</size></plane></geometry></collision>
      <visual name="v"><geometry><plane><normal>0 0 1</normal><size>60 60</size></plane></geometry>
        <material><ambient>0.55 0.6 0.55 1</ambient><diffuse>0.6 0.65 0.6 1</diffuse></material></visual>
    </link></model>
EOF
for i in $(seq 1 "$N"); do
    IP="127.0.0.$((i + 1))"
    Y=$(echo "$i" | awk '{printf "%.1f", ($1 - 1) * 0.8}')
    cat <<EOF
    <include>
      <uri>model://stratosdrone</uri><name>drone_$i</name><pose>0 $Y 0.025 0 0 0</pose>
      <plugin filename="StratosFcSystem" name="stratos::StratosFcSystem">
        <bind_ip>$IP</bind_ip><seed>$((i * 7))</seed>
      </plugin>
    </include>
EOF
done
echo "  </world></sdf>"
} > "$WORLD"

echo "[spawn_swarm] $N drone(s) on 127.0.0.2..$((N + 1)) — world: $WORLD (RTF $RTF)"
ARGS=(sim -r "$WORLD")
[ "$GUI" = "1" ] || ARGS=(sim -s -r "$WORLD")
trap 'kill 0' EXIT INT TERM
exec "$GZ_BIN" "${ARGS[@]}"
