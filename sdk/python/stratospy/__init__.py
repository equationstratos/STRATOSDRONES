"""stratospy — thin helper layer over djitellopy for STRATOSDRONE.

A STRATOSDRONE speaks the Tello SDK 2.0 wire protocol, so plain djitellopy
works as-is over Wi-Fi. This package adds:

  * enable_sim()    — socket accommodation to fly simulated drones (SITL or
                      Gazebo) living on loopback IPs of the same machine
  * StratosDrone    — djitellopy.Tello subclass exposing STRATOS extensions
                      (video resolution switch, parameter get/set, RGB LED)
  * sim helpers     — spawn/stop local SITL instances for tests and demos
  * lora            — the TinyHoop MK1 LoRa fleet transport (LoRaLink,
                      StratosLoRaDrone) — mirrors fc_core/src/fc_lorap.c
  * show            — drone-show choreography (author / safety-check / upload
                      to sim over UDP or to the fleet over LoRa)
"""
from .stratos import StratosDrone, enable_sim
from .sim import SitlInstance, spawn_sitl, wait_drone_ready
from .show import Show, Track
from . import lora

__all__ = ["StratosDrone", "enable_sim", "SitlInstance", "spawn_sitl",
           "wait_drone_ready", "Show", "Track", "lora"]
__version__ = "0.1.0"
