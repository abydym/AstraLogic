---
name: afsim-project
description: |
  AFSIM 2.9.0 simulation: create, compile, debug, visualize, and analyze.
  Zero hardcoded paths. Works on any machine with AFSIM installed.
  Workflow: write .txt -> mission.exe compile -> fix errors -> mystic.exe view -> python analyze
keywords: [AFSIM, mission, mystic, simulation, satellite, radar, missile, comms]
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["mission"], "anyBins": ["mystic"] },
        "homepage": "https://github.com/afsim-community/afsim-skill",
      },
  }
user-invocable: true
---
**You need:**
1. AFSIM 2.9.0 installed somewhere on your machine
2. Python 3.x with `pip`

> **File injection policy:** Only this SKILL.md is model-injected.
> All .txt files in locks/, 
eferences/, 	emplates/ are on-disk only.
> They are read on demand via 
ead() — never auto-injected.
> Python scripts in scripts/ are invoked explicitly when needed.


**Step 1: Tell the skill where AFSIM lives**

```bash
# Windows (PowerShell)
$env:AFSIM_HOME = "C:\AFSIM2.9\afsim-2.9.0"

# Linux/Mac
export AFSIM_HOME=/opt/afsim-2.9.0
```

Or add `AFSIM_HOME` to your system/user environment variables permanently.

**Step 2: Install Python dependencies (for analysis plots)**

```bash
pip install matplotlib numpy
```

**Step 3: Verify it works**

```bash
# Should print version info
"$env:AFSIM_HOME/bin/mission.exe" --version
```

---

## Workflow (4 steps, always in order)

```
Step 1:  $AFSIM_HOME/bin/mission.exe -es main.txt         # compile
Step 2:  Fix errors 鈫?repeat Step 1                        # iterate
Step 3:  $AFSIM_HOME/bin/mystic.exe output/*.aer            # 3D view
Step 4:  python analyze.py --evt output/*.evt               # plots + CSV
```

> 鈿狅笍 The `define_path_variable CASE name` line must come BEFORE any
> `event_output`, `csv_event_output`, or `event_pipe` block in your main.txt.

### Full example (LEO satellite)

```bash
cd leo_comm/
"$AFSIM_HOME/bin/mission.exe" -es leo_comm.txt
"$AFSIM_HOME/bin/mystic.exe" output/leo_comm.aer
python analyze_leo_comm.py --no-mystic
# 鈫?Opens Mystic 3D view + saves analysis output (see analyze_leo_comm.py) + .csv
```

---

## What's in this skill

```
skills/afsim-project/
├── SKILL.md                    ← This file. Your instructions.
├── templates/                  ← Complete, compilable projects (12 files)
│   ├── main.txt + setup.txt    ← Copy this folder to start
│   ├── platforms/              ← tank.txt, building.txt, fighter.txt
│   ├── weapons/                ← missile.txt
│   ├── sensors/                ← fire_control_radar.txt
│   ├── processors/             ← launch + aa_tactics
│   └── scenarios/              ← blue + red laydown
├── blocks/                     ← Reusable code blocks (45 files)
│   ├── README.md               ← Full index
│   ├── launcher_sam.txt        ← SAM launcher + missile + radar + tactics
│   ├── missile_ballistic.txt   ← Ballistic missile definitions
│   ├── sensor_*.txt            ← 10 sensor types (EOIR, ESM, SAR, ...)
│   ├── tactics_naval_sam.txt   ← Naval SAM/ASM/SSM tactics
│   └── satellite_leo.txt       ← LEO comm satellite
├── references/                 ← Offline command references (16 files)
│   ├── reference_manual.txt    ← Full AFSIM manual (2.7 MB)
│   ├── wsf_radar_sensor.txt    ← 60 radar commands
│   ├── wsf_air_mover.txt       ← 35 air mover commands
│   └── ... (14 more)
└── scripts/                    ← Tool scripts (6 files)
    ├── lookup.py               ← Search manual: lookup.py <keyword>
    ├── index_manual.py         ← Rebuild command indexes
    ├── analyze_leo_comm.py     ← LEO comm analysis + plot generator
    └── audit_*.txt             ← Command audit reports (auto-generated)
```


---

## 馃攳 How to Look Up Commands (token-saving)

**Never inject the full manual.** Query only what you need:

```python
import os

# Auto-find the manual (resolved relative to this skill directory)
skill_dir = os.path.dirname(os.path.abspath(__file__))  # provided at runtime
manual = os.path.join(skill_dir, 'references', 'reference_manual.txt')

with open(manual, 'r', encoding='utf-8', errors='replace') as f:
    txt = f.read()

# Quick existence check
print(txt.count('show_graphics'))  # 鈫?1 (only launch_computer)

# Keyword lookup with limited context (~1700 chars)
idx = txt.find('WSF_AIR_MOVER')
if idx > 0:
    print(txt[max(0,idx-200):idx+1500])
```

**Rules:**
- Limit context to `[-200:+1500]` chars 鈥?never dump entire sections
- Use `scripts/lookup.py <keyword>` as a shortcut
- For command lists: find the section with the most `鈻猔 bullet characters

---

## 馃摑 Template: Minimal Project (start here)

This is the simplest possible AFSIM project. Copy `templates/` to a new folder and edit.

### main.txt
```
define_path_variable CASE my_project
log_file output/$(CASE).log
include event_output.txt
event_output file output/$(CASE).evt end_event_output
event_pipe
   file output/$(CASE).aer
   use_preset high
end_event_pipe
include setup.txt
include scenarios/blue_laydown.txt
include scenarios/red_laydown.txt
end_time 120 secs
```

### setup.txt
```
file_path .
include_once platforms/tank.txt
include_once platforms/building.txt
include_once weapons/missile.txt
include_once processors/missile_processor.txt
```

### platform_type (ground vehicle)
```
platform_type TANK WSF_PLATFORM
   icon tank
   side red
   height 3 m  length 8 m  width 4 m
   mover WSF_GROUND_MOVER end_mover
   weapon MSL RED_TANK_MISSILE quantity 10 end_weapon
   processor launch MISSILE_LAUNCH_PROCESSOR
      script_variables WEAPON_NAME = "MSL"; end_script_variables
   end_processor
end_platform_type
```

### platform_type (aircraft)
```
platform_type UAV WSF_PLATFORM
   icon UAV
   height 2 m  length 8 m  width 10 m
   mover WSF_AIR_MOVER
      maximum_speed 150 kts  minimum_speed 50 kts
      maximum_altitude 6000 m  minimum_altitude 500 m
   end_mover
end_platform_type
```

### Weapon: explicit 鈥?straight-line (simplest)
```
weapon_effects EFF WSF_GRADUATED_LETHALITY
   radius_and_pk 50 m 1.0
end_weapon_effects

platform_type MSL_BODY WSF_PLATFORM
   icon missile
   height 1 m  length 5 m  width 1 m
   mover WSF_STRAIGHT_LINE_MOVER
      average_speed 300 kts
   end_mover
   processor fuse WSF_GROUND_TARGET_FUSE end_processor
end_platform_type

weapon RED_TANK_MISSILE WSF_EXPLICIT_WEAPON
   launched_platform_type MSL_BODY
   weapon_effects EFF
end_weapon
```

### Weapon: explicit 鈥?guided (with aerodynamics + guidance computer)
```
weapon_effects EFF WSF_GRADUATED_LETHALITY
   radius_and_pk 100 m 1.0
end_weapon_effects

aero MSL_AERO WSF_AERO
   reference_area 0.125 m2
   cd_zero_subsonic 0.30
   cd_zero_supersonic 0.50
   mach_begin_cd_rise 0.95
   mach_end_cd_rise 1.3
   mach_max_supersonic 4.0
end_aero

platform_type GUIDED_MSL WSF_PLATFORM
   icon missile
   mover WSF_GUIDED_MOVER
      total_mass 300 kg
      fuel_mass 100 kg
      thrust 5000 N
      thrust_duration 10 s
      aero MSL_AERO
   end_mover
   processor computer WSF_GUIDANCE_COMPUTER
      phase LIFTOFF
         guidance_delay 1.0 sec
         next_phase PITCH_OVER when phase_time >= 0.5 sec
      end_phase
      phase PITCH_OVER
         commanded_flight_path_angle 45 deg
         next_phase BALLISTIC when on_commanded_flight_path_angle
      end_phase
      phase BALLISTIC
         guidance_delay 2000 sec
      end_phase
   end_processor
   processor fuse WSF_AIR_TARGET_FUSE
      max_time_of_flight_to_detonate 100 sec
   end_processor
end_platform_type

weapon GUIDED_MISSILE WSF_EXPLICIT_WEAPON
   launched_platform_type GUIDED_MSL
   weapon_effects EFF
end_weapon
```

### Weapon: implicit (instant kill, no moving parts)
```
weapon_effects VKILL WSF_GRADUATED_LETHALITY
   radius_and_pk 100 m 1.0
end_weapon_effects
weapon VIRTUAL_KILL WSF_IMPLICIT_WEAPON
   weapon_effects VKILL
   firing_delay 0 secs
   firing_interval 0 secs
end_weapon
```

### Scenario laydown (where things go)
```
platform Red_Tank TANK
   side red
   position 34.0n 118.0w altitude 10 m
   heading 0 deg
   track platform Blue_Base end_track
end_platform

platform Blue_Base BUILDING
   side blue
   position 34.05n 118.05w
end_platform
```

### Script processor (find + fire at named target)
```
processor MISSILE_LAUNCH_PROCESSOR WSF_SCRIPT_PROCESSOR
   script_variables
      string WEAPON_NAME = "";
      double TIME_TO_LAUNCH = 5.0;
      string TARGET_NAME = "Blue_Base";
      bool fired = false;
   end_script_variables
   update_interval 1.0 sec
   on_update
      if (fired) return;
      if (TIME_NOW < TIME_TO_LAUNCH) return;
      WsfPlatform target = WsfSimulation.FindPlatform(TARGET_NAME);
      if (!target.IsValid()) return;
      WsfWeapon wpn = PLATFORM.Weapon(WEAPON_NAME);
      if (!wpn.IsValid()) return;
      wpn.CueToTarget(target.MakeTrack());
      wpn.Fire(target.MakeTrack());
      writeln(TIME_NOW, " Fired ", WEAPON_NAME);
      fired = true;
   end_on_update
end_processor
```

---

## 馃搳 Data Export

Add a `csv_event_output` block to export simulation data as CSV:

```
csv_event_output
   file output/$(CASE).csv
   enable all               # or: enable SPECIFIC_EVENT_NAME
end_csv_event_output
```

The CSV includes: time, lat, lon, altitude, velocity (NED + ECI), heading, etc.
Open it in Excel, Python (pandas), or MATLAB for analysis.

### Metrics reference

| Metric | How to get it |
|--------|--------------|
| Range / distance | Script: `PLATFORM.SlantRangeTo(target)` 鈫?writeln |
| Elevation angle | Computed from slant + ground range |
| Propagation delay | `delay = slant_range / 299792458` |
| Free space loss | Post-process: `20*log10(4蟺R/位)` |
| Received power | Post-process: `P_t + G_t + G_r - FSL - losses` |
| Link UP/DOWN | Script logic 鈫?writeln |

### Python analysis (example)

```bash
pip install matplotlib numpy
python analyze_leo_comm.py --evt output/*.evt
```

---

## 鉁?Critical Rules

1. `platform_type <NAME> WSF_PLATFORM` 鈥?WSF_PLATFORM is required
2. Always include a mover: `WSF_GROUND_MOVER`, `WSF_AIR_MOVER`, `WSF_GUIDED_MOVER`, or `WSF_STRAIGHT_LINE_MOVER`
3. Signatures (radar/IR/optical) are global, then referenced by name inside platform_type
4. `end_time <val> secs` 鈥?NOT `simulation_end_time`
5. Routes: `edit mover { route ... end_route } end_mover`
6. `CueToTarget()` BEFORE `Fire()` 鈥?always
7. Include targets BEFORE shooters in scenario files (pre-briefed tracks)
8. Sensors are `off` by default; set `on` or call `sensor.TurnOn()`
9. `use_preset {default|low|high|full}` controls Mystic output richness
10. Save files as **BOM-less UTF-8** (AFSIM can't parse UTF-8 BOM)
11. **Satellite orbits must be closed loops** — route waypoints must trace at least one full orbit (~15 waypoints forming the ground track from ~50°N to ~50°S and back)
12. **Simulation time must cover ≥1 full orbit** — for LEO 520km: `end_time 5693 sec` (94.9 min). Formula: `T = 2π × √((R_earth + h)³/μ)`, μ = 3.986×10¹⁴
13. **AFSIM 2.9 WSF_SCRIPT_PROCESSOR limits**: No `on_init`, no `substr()`, no `atan2()`, no ternary operators, no array `{ }` init, no `Latitude()`/`Longitude()` methods. Use `if/else` and `while` loops instead.

---

## 馃毇 Commands That Do NOT Exist

| Guessed | Actually鈥?|
|---------|-----------|
| `show_graphics` on radar | Valid only on guidance/launch computers |
| `draw_object` | Use script classes `WsfDrawCircle`/`BeginLines()` |
| `graphical_maximum_range` | Sensor range in Mystic is automatic |
| "AER Viewer" | Tool is called **Mystic** (or Warlock) |
| `ElevationAngleTo()` | Method doesn't exist on WsfPlatform |
| `IsConnected()` | Method doesn't exist on WsfComm |
| `log10()`, `atan()` | AFSIM scripts have no math functions |

---

## 馃О Available Template Projects

| Directory | What it contains |
|-----------|-----------------|
| `templates/` | Tank鈫払uilding (simplest), Fighter鈫扵arget (air combat) |
| `blocks/launcher_sam.txt`, `missile_sam.txt`, `radar_sam.txt`, `tactics_sam.txt` | SAM launcher + missile + radar + tactics (from AFSIM demos) |
| `blocks/launcher_ballistic.txt`, `missile_ballistic.txt` | Ballistic missile launchers + missiles |
| `blocks/launcher_tbm.txt`, `missile_tbm.txt` | Theater ballistic missiles |
| `blocks/sensor_*.txt` | 10 sensor types (EOIR, ESM, SAR, Bistatic, Clutter, 鈥? |
| `blocks/tactics_naval_sam.txt`, `tactics_naval_asm.txt`, `tactics_naval_ssm.txt`, `platform_naval_ship.txt` | Naval ship + SAM/ASM/SSM tactics |
| `blocks/satellite_leo.txt`, `station_ground_leo.txt`, `main_leo_comm.txt`, `scenario_leo_comm.txt` | LEO satellite 鈫?ground station comms |
| `scripts/analyze_leo_comm.py` | Python analysis 鈫?6 plots + CSV |
| `blocks/leo_constellation/` | 6-sat LEO constellation, 2 gateways, 1 mobile terminal |
| `templates/leo_constellation/` | Complete compilable constellation project |

---

## 馃敡 Common Errors

| Error | Fix |
|-------|-----|
| `Unknown command: <cmd>` | Look it up in manual; you guessed the name |
| `Bad value for: <cmd>` | Check unit format (m, km, sec, deg, kts, watt, dB) |
| `Unexpected End Of Data` | Mismatched `end_` tags 鈥?count your blocks |
| `Cannot open file: <path>` | Missing `file_path .` in setup.txt |
| `Unable to open event_output file` | Create `output/` dir first |
| `Target platform of pre-briefed track...` | Include blue_laydown BEFORE red_laydown |
| `Bad value for position` | Use `34.0n 118.0w altitude 0 m` with N/S/E/W |
| `Bad value for peak_gain` | Use `dB` not `dBi` |
| `aero type must be specified` | Add `aero none` or define aero in guided mover stages |
| `AGL_limit_encountered` (missile crashing) | Add guidance computer, `launch_delta_v`, or use WSF_STRAIGHT_LINE_MOVER |
| `Unknown command: kill_radius` | Use `radius_and_pk` in WSF_GRADUATED_LETHALITY |
| `Unknown command: flight_path_angle` | Use `commanded_flight_path_angle` |
| `Unknown command: proximity_fuse_distance` | Not supported on WSF_GROUND_TARGET_FUSE |
| UTF-8 BOM error | Save file as BOM-less UTF-8 |





