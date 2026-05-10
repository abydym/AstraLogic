# blocks/ — Reusable AFSIM Code Blocks

These are extracted, verified AFSIM definition blocks from official demos.
Copy-paste the content you need into your project files.

## Index

### Launchers
| File | What it contains |
|------|-----------------|
| launcher_ballistic.txt | Ballistic missile launcher (SRBM/MRBM types) |
| launcher_sam.txt | SAM launcher with radar + weapon + processors |
| launcher_tbm.txt | TBM launcher types 1-3 |

### Missiles
| File | What it contains |
|------|-----------------|
| missile_ballistic.txt | SRBM/MRBM full stack: aero, mover, guidance phases, LC |
| missile_sam.txt | SAM missile: aero + 4-stage guided mover + weapon |
| missile_tbm.txt | TBM missiles with single/dual stage |

### Sensors
| File | What it contains |
|------|-----------------|
| sensor_bistatic.txt | Bistatic radar with jamming variants |
| sensor_clutter.txt | Clutter model generation |
| sensor_coherent.txt | Coherent sensor processor |
| sensor_composite.txt | Composite sensor fusion |
| sensor_eoir.txt | EO/IR sensor |
| sensor_esm.txt | ESM passive RF sensor |
| sensor_jamming.txt | Jamming effects |
| sensor_nav.txt | Navigation radar |
| sensor_radar_ew.txt | EW radar with jamming |
| sensor_sar.txt | SAR sensor |
| sensor_spin_scheduler.txt | Spin scheduler demo |
| adar_sam.txt | SAM fire control radar |
| adar_tracker.txt | Generic tracker radar |

### Platforms
| File | What it contains |
|------|-----------------|
| platform_air_target.txt | Simple air target (WSF_AIR_MOVER) |
| platform_ground_target.txt | Simple ground target |
| platform_naval_ship.txt | Naval ship with SAM/ASM/SSM |
| platform_types.txt | General platform_type syntax |
| satellite_leo.txt | LEO communication satellite |
| station_ground_leo.txt | Satellite ground station |

### Processors
| File | What it contains |
|------|-----------------|
| processor_definitions.txt | General processor syntax |
| processor_launch.txt | Launch timing script (fixed/random) |
| 	actics_sam.txt | SAM engagement state machine |
| 	actics_naval_sam.txt | Naval SAM engagement logic |
| 	actics_naval_asm.txt | Naval ASM engagement logic |
| 	actics_naval_ssm.txt | Naval SSM engagement logic |

### Signatures & Antennas
| File | What it contains |
|------|-----------------|
| signatures_shared.txt | Shared IR/optical/radar signatures, datalink, filter |
| signatures_optical.txt | Optical signature definitions |
| signatures_radar.txt | Radar signature definitions |
| ntenna_patterns.txt | Antenna pattern templates |

### Multiresolution Demos
| File | What it contains |
|------|-----------------|
| multires_comm.txt | Communication components |
| multires_fuel.txt | Fuel system |
| multires_mover.txt | Mover types |
| multires_processor.txt | Processor types |
| multires_sensor.txt | Sensor types |

### Weapons
| File | What it contains |
|------|-----------------|
| weapon_aam.txt | Air-to-air missile (active radar) |
| missile_seekers.txt | Missile seeker radar sensors |

### LEO Satellite Communication
| File | What it contains |
|------|-----------------|
| main_leo_comm.txt | Main entry file template |
| scenario_leo_comm.txt | Satellite + ground station laydown |
| satellite_leo.txt | LEO satellite platform |
| station_ground_leo.txt | Ground station platform |
| nalyze_leo_comm.py | Python script: plots range, elevation, delay, FSL, RX power |
