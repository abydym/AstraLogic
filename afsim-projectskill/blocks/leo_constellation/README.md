# LEO Constellation Blocks

6-satellite LEO constellation + 2 ground gateways + 1 mobile terminal.
Inter-satellite links (60GHz V-band) + feeder links (Ka-band 27.5/17.5GHz).

## Files

| File | Purpose |
|------|---------|
| `satellite_leo_block.txt` | LEO_SAT platform type: ISL + downlink + uplink + link_budget + handover processors |
| `gateway_station_block.txt` | GATEWAY_GS platform type: Ka-band Rx/Tx, 33dBi |
| `mobile_terminal_block.txt` | MOBILE_TERMINAL platform type: 18dBi, handover decision logic |
| `deployment_scenario.txt` | Positions: 6 sats + 2 gateways + mobile terminal |
| `network_definitions.txt` | LeoSatNet (ISL ring) + GroundFeederNet (star) networks |

## How to Use

### Option A: Quick template (recommended)
Copy `templates/leo_constellation/` to a new directory, then:

```bash
cd my_project
$AFSIM_HOME/bin/mission.exe -es leo_constellation.txt
```

### Option B: Custom project
Include blocks individually:

```afsim
include_once blocks/leo_constellation/satellite_leo_block.txt
include_once blocks/leo_constellation/gateway_station_block.txt
include_once blocks/leo_constellation/mobile_terminal_block.txt
include blocks/leo_constellation/deployment_scenario.txt
include blocks/leo_constellation/network_definitions.txt
```

## Network Architecture

```
                    ┌─────────┐
      ┌─────────────│ Sat_1   │─────────────┐
      │  (ISL ring) └─────────┘             │
      │   ┌─────────┐           ┌─────────┐ │
      ├───│ Sat_6   │           │ Sat_2   ├─┘
      │   └─────────┘           └─────────┘
      │   ┌─────────┐           ┌─────────┐
      ├───│ Sat_5   │           │ Sat_3   ├─┐
      │   └─────────┘           └─────────┘ │
      │   ┌─────────┐             │         │
      └───│ Sat_4   │─────────────┘         │
          └─────────┘                       │
              │ Ka                         │ Ka
    ┌─────────┴────────────┐    ┌──────────┴───────┐
    │  Gateway_A (32N118E) │    │  Gateway_B (25N113E)│
    └──────────────────────┘    └──────────────────┘
              │ Ka (mobile terminal 29N116E -> NE at 15km/h)
              │
    ┌─────────┴──────────┐
    │  Mobile_Terminal   │  (automatic handover between satellites)
    └────────────────────┘
```

## Parameters

| Parameter | Value |
|-----------|-------|
| Orbit | 520km circular, 50deg inclination |
| Satellites | 6, same orbital plane, 60deg phase |
| ISL | 60GHz V-band, 22dBi, 20Mbps |
| Feeder link | Ka 27.5GHz DL / 17.5GHz UL, 24/33dBi |
| Terminal access | Ka 27.5GHz, 18dBi, min elev 7deg |
| Handover | Automatic, based on elevation angle |
