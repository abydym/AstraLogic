# AFSIM 2.9.0 Syntax Reference

This reference captures the verified AFSIM 2.9.0 syntax learned from the 2488-page reference manual
and validated through iterative compilation with mission.exe.

## Project Structure

```
project/
├─ main.txt                   # Entry point (define_path_variable, include, end_time)
├─ setup.txt                  # Platform type definitions (file_path .)
├─ event_output.txt           # Event log configuration
├─ event_pipe.txt             # .aer visualization output
├─ platforms/                 # Platform type definitions
├─ weapons/                   # Weapon definitions (mover + airframe + effects)
├─ processors/                # Script processors (firing logic)
├─ scenarios/                 # Platform instantiation (laydown)
└─ output/                    # Generated files (.aer, .evt, .log)
```

## Main File Template

```
define_path_variable CASE my_project
log_file output/$(CASE).log

include event_output.txt
event_output file output/$(CASE).evt end_event_output

event_pipe
   file output/$(CASE).aer
   use_preset default
end_event_pipe

include setup.txt
include scenarios/red_side.txt
include scenarios/blue_side.txt

end_time 120 secs
```

## Event Output

```
event_output
   file output/simulation.evt
   time_format h:m:s.1
   enable WEAPON_FIRED
   enable WEAPON_HIT
   enable WEAPON_MISSED
   enable WEAPON_TERMINATED
   enable PLATFORM_ADDED
   enable PLATFORM_DELETED
end_event_output
```

## Event Pipe (Animation File)

```
event_pipe
   file output/simulation.aer
   use_preset default
end_event_pipe
```

## Platform Type Definition

```
platform_type TANK WSF_PLATFORM
   icon tank
   side red
   mover WSF_GROUND_MOVER end_mover
   weapon <weapon_instance_name> <WEAPON_TYPE>
      quantity 10
   end_weapon
   processor <name> <PROCESSOR_TYPE>
      ...
   end_processor
end_platform_type
```

Note: `platform_type <NAME> WSF_PLATFORM` — the WSF_PLATFORM keyword is required.
`mover WSF_GROUND_MOVER end_mover` — empty mover block is valid for stationary platforms.

## Platform Instantiation

```
platform Red_Tank TANK
   side red
   position 34.0n 118.0w altitude 10 m
   heading 0 deg
   processor launch_processor
      script_variables
         TIME_TO_LAUNCH = 5.0;
      end_script_variables
   end_processor
   track
      platform Blue_Base
   end_track
end_platform
```

Coordinates use N/S/E/W suffixes. Altitude in meters.

## Weapon Definition (Simple Missile)

```
weapon_effects MSL_1_EFFECT WSF_GRADUATED_LETHALITY
   radius_and_pk 50.0 m 1.0
end_weapon_effects

# Option A: Straight-line mover (simplest, works without guidance computer)
platform_type MSL_1_AIRFRAME WSF_PLATFORM
   icon missile
   mover WSF_STRAIGHT_LINE_MOVER
      average_speed 300 kts
   end_mover
   processor fuse WSF_GROUND_TARGET_FUSE
   end_processor
end_platform_type

# Option B: Guided mover (needs guidance computer + aero)
mover MSL_1_MOVER WSF_GUIDED_MOVER
   integration_timestep 0.01 secs
   compute_all_forces_each_substep true
   stage 1
      aero <type>|none          # MUST be specified
      total_mass 300 kg
      fuel_mass 100 kg
      thrust 5000 newtons
      thrust_duration 10 s
      specific_impulse 250 s
      pre_ignition_coast_time 0 secs
   end_stage
end_mover

weapon RED_TANK_MISSILE WSF_EXPLICIT_WEAPON
   launched_platform_type MSL_1_AIRFRAME
   weapon_effects MSL_1_EFFECT
end_weapon
```

## Script Processor

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
      if (fired == false && TIME_NOW >= TIME_TO_LAUNCH)
      {
         WsfWeapon wpn = PLATFORM.Weapon(WEAPON_NAME);
         WsfPlatform target = WsfSimulation.FindPlatform(TARGET_NAME);
         WsfTrack trk = target.MakeTrack();
         if (wpn.IsValid())
         {
            wpn.CueToTarget(trk);
            wpn.Fire(trk);
            writeln("[", TIME_NOW, "] Fired -> ", TARGET_NAME);
            fired = true;
         }
      }
   end_on_update
end_processor
```

## WSF_GUIDANCE_COMPUTER (for guided mover)

```
processor guidance WSF_GUIDANCE_COMPUTER
   phase LIFTOFF
      guidance_delay 1.0 sec
      next_phase PITCH_OVER when phase_time >= 0.5 sec
   end_phase
   phase PITCH_OVER
      commanded_flight_path_angle 45 deg
   end_phase
end_processor
```

## Compilation

```
# MUST cd into project directory first!
cd project/
mission.exe -es main.txt
```

`mission.exe` is the official command-line compiler. `wizard.exe` is a GUI IDE and cannot run headless.

The project directory must contain an `output/` subdirectory before running.

## Common Errors

| Error | Fix |
|-------|-----|
| `Unknown identifier: 'PlatformName'` in global script | Use `WsfSimulation.FindPlatform("Name")` or put code in processor |
| `Unexpected End Of Data` | Check all blocks have matching `end_` close tags |
| `Unknown command: kill_radius` | WSF_SPHERICAL_LETHALITY uses `minimum_radius`/`maximum_radius`/`maximum_damage` |
| `Unknown command: ground_speed/speed` in mover | Use empty mover block or check manual for valid commands |
| `Bad value for: position` | Use `34.0n 118.0w altitude 0 m` format with N/S/E/W |
| `Unknown command: simulation_end_time` | Use `end_time 120 secs` |
| `Unknown command: log_file` in event_output | Use `file <path>` instead |
| `Cannot open file: weapons/xxx.txt` | Add `file_path .` in setup.txt, or use absolute paths |
| `Unable to open event_output file` | Create output/ directory, use `cd project/` when compiling |
| `Target platform was not defined prior to track` | Include blue side files before red side files |
| `aero type must be specified` | Add `aero none` or define aero type in guided mover stages |
| `AGL_limit_encountered` (missile crashes) | Add `launch_delta_v`, guidance computer, or use WSF_STRAIGHT_LINE_MOVER |
| `Unknown command: flight_path_angle` | Use `commanded_flight_path_angle` |
| `Unknown command: proximity_fuse_distance` | WSF_GROUND_TARGET_FUSE does not support this command |

## Key Script Methods

```
WsfSimulation.FindPlatform("name")    # Find platform by name
PLATFORM.Weapon("name")               # Get weapon on current platform
wpn.IsValid()                         # Check weapon reference
wpn.CueToTarget(trk)                  # Target cueing before fire
wpn.Fire(trk)                         # Fire one round (NOT FireSalvo)
target.MakeTrack()                    # Create track from platform
PLATFORM.MasterTrackList()            # Get local track list
PLATFORM.Name()                       # Get platform name
writeln("msg", var1, var2)           # Print with newline
```
