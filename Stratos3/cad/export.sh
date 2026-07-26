#!/usr/bin/env bash
# Export every STRATOS 3 part to stl/ (and previews to preview/).
set -e
cd "$(dirname "$0")"; mkdir -p stl preview
PARTS="bottom_plate top_plate tpu_cam_mount_top tpu_cam_mount_bottom tpu_rear_bay \
tpu_cap_holder tpu_rx_holder tpu_gps_mount tpu_arm_guard tpu_batt_pad \
side_panel_a side_panel_b side_panel_c side_panel_d side_panel_e"
for P in $PARTS; do
  echo "  $P"
  xvfb-run -a openscad -o "stl/$P.stl" --export-format binstl -D "PART=\"$P\"" frame3.scad
done
# carbon plates also as DXF, for the CNC/laser shop
for P in bottom_plate top_plate; do
  xvfb-run -a openscad -o "dxf/$P.dxf" -D "PART=\"$P\"" -D '$fn=64' \
    <(echo "projection(cut=false) import(\"stl/$P.stl\");") 2>/dev/null || true
done
echo "done -> stl/"
