"""stratospy — thin helper layer over djitellopy for STRATOSDRONE.

A STRATOSDRONE speaks the Tello SDK 2.0 wire protocol, so plain djitellopy
works as-is over Wi-Fi. This package adds:

  * enable_sim()    — socket accommodation to fly simulated drones (SITL or
                      Gazebo) living on loopback IPs of the same machine
  * StratosDrone    — djitellopy.Tello subclass exposing STRATOS extensions
                      (video resolution switch, parameter get/set, RGB LED)
  * sim helpers     — spawn/stop local SITL instances for tests and demos
"""
from .stratos import StratosDrone, enable_sim
from .sim import SitlInstance, spawn_sitl

__all__ = ["StratosDrone", "enable_sim", "SitlInstance", "spawn_sitl"]
__version__ = "0.1.0"
