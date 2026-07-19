# fpv85 firmware — shared verbatim vs specified

**Shared verbatim (zero changes):** `fc_core` (mixer/PIDs/commander —
`fc_core_get_motors` already abstracts the 4 outputs), `net_task`/SDK verbs,
`video_task` H.264-over-Wi-Fi (if the optional MIPI cam is fitted), the
Android app, the Python SDK.

**Specified, NOT implemented (see ../DESIGN.md §5, deploy-verb precedent):**

| Piece | Spec |
|---|---|
| `outputs_dshot.c` | DShot600 ×4 on P4 RMT, GPIO45-48 (same pins as brushed PWM); OneShot/PWM fallback for first spins |
| `crsf_task.c` | UART GPIO4/5 @420 kbaud → CRSF channels → `fc_cmd_rc()`; **300 ms failsafe → `fc_cmd_emergency()`**; CH5 arm |
| pinmap | generated reference: `../../hardware/pcb_fpv/out/board_pinmap_fpv.h` |

The analog FPV chain (cam → VTX) is pure hardware — flies with zero firmware.
