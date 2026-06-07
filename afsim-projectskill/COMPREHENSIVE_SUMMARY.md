# afsim-projectskill 全文件功能总结

> 生成日期: 2026-06-07 | AFSIM 2.9.0 仿真 Skill | 共 82 个文件

---

## 一、总体架构

```
afsim-projectskill/
├── SKILL.md                         ← Skill 入口与完整使用指南
├── blocks/          (41文件)        ← 可复用 AFSIM 代码块（从官方 demo 提取）
│   └── leo_constellation/ (5文件)   ← LEO 星座专项
├── references/      (17文件)        ← 离线命令参考手册
├── scripts/         (8文件)         ← Python 工具脚本
└── templates/       (16文件)        ← 完整可编译项目模板
    └── leo_constellation/ (5文件)   ← LEO 星座可运行模板
```

---

## 二、SKILL.md — Skill 入口与使用指南

**文件定位**: 整个 Skill 的入口，定义了工作流、项目结构、常见错误和所有可用模块索引。

**实现的完整功能**:
| 功能 | 说明 |
|------|------|
| AFSIM 环境配置 | 设置 `AFSIM_HOME` 环境变量，验证 `mission.exe --version` |
| Python 依赖安装 | `pip install matplotlib numpy` |
| 4步工作流 | ① `mission.exe -es main.txt` 编译 → ② 修复错误迭代 → ③ `mystic.exe output/*.aer` 3D可视化 → ④ Python 分析画图 |
| 完整项目结构模板 | `main.txt` → `setup.txt` → `platforms/`/`weapons/`/`sensors/`/`processors/`/`scenarios/` |
| 4种平台类型模板 | `TANK`(地面)、`UAV`(空中)、`MSL_BODY`(直飞弹体)、`GUIDED_MSL`(制导弹体) |
| 3种武器定义模板 | `WSF_EXPLICIT_WEAPON`(显式)、`WSF_EXPLICIT_WEAPON + WSF_GUIDED_MOVER`(制导)、`WSF_IMPLICIT_WEAPON`(隐式) |
| 脚本处理器模板 | `WSF_SCRIPT_PROCESSOR` — 找目标、Cue、Fire |
| 场景布设模板 | `platform xxx position 34.0n 118.0w altitude 10 m heading 0 deg` |
| 想定编排模板 | 蓝方先于红方（预置跟踪） |
| 数据导出 | `csv_event_output enable all` → CSV 或 `event_output` → .evt |
| 链路指标计算 | Slant范围/仰角/传播延迟/自由空间损耗/接收功率 |
| Python 分析示例 | `analyze_leo_comm.py` 生成6张图+CSV |
| 13条关键规则 | WSF_PLATFORM必须、mover必须、签名全局引用、CueToTarget→Fire顺序、传感器默认off等 |
| 轨道周期公式 | `T = 2π × √((R_earth + h)³/μ)`，LEO 520km ≈ 5693s |
| AFSIM 2.9 脚本限制 | 无 `on_init`/`substr()`/`atan2()`/三元运算符/数组`{}`初始化/`Latitude()`方法 |
| 不存在的命令表 | 7个常见误用命令及正确替代 |
| 常见错误表 | 15种编译错误及修复方案 |
| 可用模板目录索引 | 12行速查表 |

---

## 三、blocks/ — 可复用 AFSIM 代码块（41文件）

### 3.1 blocks/README.md
**功能**: 全部 blocks 文件的索引目录，按启动器/导弹/传感器/平台/处理器/签名天线/多分辨率/武器/LEO通信分类

### 3.2 平台定义文件

#### blocks/platform_types.txt
**功能**: 6种复合平台类型定义

| 平台类型 | 功能 |
|----------|------|
| `SIMPLE_FIGHTER` | 最简战斗机，仅含 `WSF_AIR_MOVER` |
| `UAV_EOIR` | 无人机 + EOIR传感器 + 脚本化成像(`BeginImaging`/`EndImaging`) + 通信 + 图像处理器 |
| `GROUND_SITE` | 地面站（雷达+光学信号），EOIR/SAR目标 |
| `GENERIC_EOIR_SITE` | 通用EOIR站点 + 跟踪管理器 + 图像处理器 |
| `GENERIC_IRST_SITE` | 通用IRST站点 + 跟踪管理器 |
| `MR_SENSOR_SITE` | 多分辨率传感器站点 |
| `GEOMETRIC_SENSOR_SITE` | 几何传感器站点（对比用），含扫描参数 |

#### blocks/platform_air_target.txt
**功能**: 最简空中目标 `AIRPLANE`（图标F-18，仅`WSF_AIR_MOVER`），用于SAM交战想定

#### blocks/platform_ground_target.txt
**功能**: 最简地面目标 `TARGET`（图标Bullseye，`WSF_GROUND_MOVER`，蓝方），用于弹道导弹/TBM想定

#### blocks/platform_naval_ship.txt
**功能**: 4种海军平台完整定义

| 平台类型 | 功能 |
|----------|------|
| `MISSILE_SHIP` | 通用导弹舰：SAM/ASM/SSM三合一，含`RICE_SCREEN`对空搜索雷达、SSM火控雷达、数据链网络、第三方更新管理、全运动包络区 |
| `RED_MISSILE_DESTROYER` | 驱逐舰：SAM + ASM + 第三方直升机制导 + 对空/对海雷达 |
| `RED_MISSILE_FRIGATE` | 护卫舰：4×照射器`FRONT_DOME` + 半运动包络区 + SAM照明体制 |
| `RED_NAVAL_HELICOPTER` | 舰载直升机：对海搜索雷达 + 飞行中目标更新（`INFLIGHT_UPDATE_TACTICS`） + 从站数据链 |

### 3.3 启动器文件

#### blocks/launcher_ballistic.txt
**功能**: 5种弹道导弹发射车平台（SRBM/MRBM），每种配置：
- `RED_SRBM_1~4_LAUNCHER` — 短程弹道导弹发射车（Scud_Launcher图标，`WSF_GROUND_MOVER`，单发SSM武器，`LAUNCH_WEAPON_PROCESSOR`）
- `RED_MRBM_2_LAUNCHER` — 中程弹道导弹发射车

#### blocks/launcher_sam.txt
**功能**: 地对空导弹发射平台 `SAM_LAUNCHER`：
- 雷达 `RADAR_SET`（X波段，20km探测）
- 武器 `SAM_MISSILE`（34发备弹，5s发射延迟，20s发射间隔）
- 上行通信 `uplink`
- `SAM_TACTICS_PROCESSOR` + `WSF_TRACK_PROCESSOR` 双处理器协同

#### blocks/launcher_tbm.txt
**功能**: 3种 TBM 发射器：
- `TBM1_LAUNCHER` — 带射程感知轨迹选择：近距离→压制，远距离→高抛；`on_create` 回调中动态设轨迹类型
- `TBM2_LAUNCHER` — 简单发射，无轨迹覆盖
- `TBM3_LAUNCHER` — 简单发射

### 3.4 导弹武器文件

#### blocks/missile_ballistic.txt
**功能**: 完整弹道导弹 `RED_SRBM_1` 的端到端定义（可作为模板复制创建新变体）：

| 组件 | 功能 |
|------|------|
| `RED_SRBM_1_INFRARED_SIG` | 红外签名（1 W/sr 常量） |
| `RED_SRBM_1_OPTICAL_SIG` | 光学签名（1 m² 常量） |
| `RED_SRBM_1_RADAR_SIG` | 雷达签名（1 m² 常量） |
| `RED_SRBM_1_EFFECT` | 杀伤效果（半径1000m，杀伤概率1.0） |
| `RED_SRBM_1_AERO` | 气动模型（参考面积6.54ft²，CLmax=4.5） |
| `RED_SRBM_1_MOVER` | 制导运动体：单级固推（空重4500lb, 燃料9450lb, 推力26000lbf, 比冲220s, 燃烧79.94s） |
| `RED_SRBM_1_GUIDANCE` | 制导计算机三阶段：LIFTOFF(延迟100s)→PITCH_OVER(指令航迹角)→BALLISTIC(关机制导) |
| `RED_SRBM_1_LAUNCH_COMPUTER` | 弹道发射计算机（查阅发射数据表） |
| `RED_SRBM_1`（platform_type） | 导弹平台类型：签名 + 运动体 + 制导 + 地面目标引信 |
| `RED_SRBM_1`（weapon） | 武器定义：倾斜角度89.9°、方位回转±180°、预测拦截点瞄准 |

#### blocks/missile_sam.txt
**功能**: 完整SAM导弹 `SAM_MISSILE` 定义：

| 组件 | 功能 |
|------|------|
| `SAM_MISSILE_AERO` | 气动模型（Cd0_sub=0.30, Cd0_super=0.50, 参考面积0.017m², CLmax=3.5） |
| `SAM_MISSILE`(平台) | 制导运动体（总重84.5kg, 燃料25.45kg, 推力5200lbf, 燃烧20s）+ 上行通信 + `WSF_GUIDANCE_COMPUTER`(比例导引6.0+速度追踪6.0+重力偏置1.2+最大25g) + 引信(最大飞行45s) |
| `SAM_MISSILE_EFFECT` | 杀伤效果（半径20m，概率0.8） |
| `SAM_MISSILE`(武器) | 8发备弹，1s发射延迟，3s齐射间隔，仰角回转±180°, 仰角范围10°-80° |

#### blocks/missile_tbm.txt
**功能**: 3种 TBM 导弹类型：

| 导弹 | 功能 |
|------|------|
| `TBM1` | 单级TBM（`WSF_TBM_MOVER`）：总重6481kg, 燃料比例0.751, 比冲253s, 弹道系数98000Nt/m², 燃烧79.2s, 轨迹类型lofted；`WSF_GROUND_TARGET_FUSE` |
| `TBM2` | 双级TBM：第一级质量极小(2999.99kg燃料)，第二级3400kg(1800kg燃料)；推力和燃烧时间独立可配；含 `on_stage_ignition`/`burnout`/`separation` 生命周期脚本记录每级状态 |
| `TBM3` | 双级TBM + 最大高度追踪：含4个生命周期脚本（启动/燃尽/分离+高度报告）+ `max-alt`脚本处理器持续追踪最大高度并输出 |

#### blocks/missile_seekers.txt
**功能**: 2种导弹导引头雷达：

| 传感器 | 功能 |
|--------|------|
| `RED_MISSILE_SEEKER_1` | X波段(9GHz)雷达导引头：sine天线(31dB峰值, 4.6°波束), 500W, 1μs脉宽, 3600Hz PRF, 10km探测, 前后比2/2和1/3, 仅搜索海面目标(忽略陆地/空中/水下/太空), 上报距离/方位/仰角 |
| `RED_MISSILE_SEEKER` | 同上，不同命名，功能相同 |

### 3.5 传感器文件（10个）

#### blocks/radar_sam.txt
**功能**: SAM火控雷达 `RADAR_SET`：
- X波段(9GHz), 500W, 1μs脉宽, 3600Hz PRF
- 20km的1m²探测距离, 最大60km
- 2s帧时, 前后比2/2和1/3, 跟踪质量1.0
- 仅搜索空中目标(忽略陆/海/水下/太空)
- 上报：距离/方位/仰角/速度

#### blocks/radar_tracker.txt
**功能**: 4种跟踪雷达组件：

| 传感器/平台 | 功能 |
|-------------|------|
| `GEOMETRIC_SENSOR` | 简单位置感知传感器（10s帧时，报告位置，质量0.5） |
| `LRSAM_TTR` | 多模火控雷达（SEARCH→ACQUIRE→TRACK三阶段递进）：sine天线(40dB, 1°波束), X波段9.5GHz, 1000kW, 150nm探测；每种模式独立帧时/扫描范围/前后比 |
| `MAR` | 电扫雷达：genap天线(9dB余弦分布, 1°波束), 3GHz, 5kW, 波束电子扫描±90°, 超高帧率0.01s |
| `GENERIC_TRACKER` | 集成跟踪平台：几何传感器+`LRSAM_TTR`+通信+5状态任务处理器(DETECTED→TRY_TO_ACQUIRE→TRY_TO_TRACK→TRY_TO_FIRE→FIRED)，每状态0.5s评估 |
| `MAR_ESAMS`(注释) | 4扇区MAR部署模板（每扇区90°偏航偏移） |

#### blocks/sensor_eoir.txt
**功能**: EOIR/IRST 传感器定义：

| 传感器 | 功能 |
|--------|------|
| `GENERIC_EOIR` | 光电/红外传感器：10s帧时，方位/仰角回转各±45°，视觉波段，0.005/m大气衰减，最大50nm，1000×1000像素，检测阈值3 |
| `GENERIC_IRST` | 红外搜索跟踪传感器：0.05/km大气衰减，中波段，背景辐射500μW/cm²/sr，NEI 1.0E-12 W/cm²，定位精度(0.001°方位/仰角, 7m距离)，前后比3/5和1/4 |
| `SCANNING_CAM_PLATFORM` | 扫描相机平台：`WSF_EOIR_SENSOR` + yaw周期性扫描脚本(`IsBetween`边界检测+方向反转) + 图像处理器 + 检测回调脚本 |
| `GEOM_SENSOR` | 空几何传感器占位符 |

#### blocks/sensor_esm.txt
**功能**: ESM 电子支援措施传感器：

| 组件 | 功能 |
|------|------|
| `ESM_ANTENNA` | 全向天线（0dB常量） |
| `ESM_SENSOR` | 基本ESM：4s帧时，固定模式，最大400km，0.1-20GHz，检测阈值5dB，噪声-180dBw |
| `ESM_SENSOR_TDOA` | TDOA增强ESM：附加误差模型（位置误差0.1ft, 时间误差5ns, 大气折射余量0） |
| `TRIMSIM_PROCESSOR` | TDOA定位处理器（最小检测数2，调试级别2） |
| `STRIKER_PLATFORM_ESM` | 攻击机ESM平台：F-18E, 雷达签名10m², 空中运动体, ESM传感器+跟踪管理 |

#### blocks/sensor_bistatic.txt
**功能**: 双基地/多基地雷达系统：

| 组件 | 功能 |
|------|------|
| `BISTATIC_TX_ANTENNA` / `BISTATIC_RX_ANTENNA` | 收发天线（常量0dB和12dB） |
| `BISTATIC_TX_ANTENNA_SINE` / `BISTATIC_RX_ANTENNA_SINE` | 正弦波束收发天线（360°方位×45°仰角） |
| `BISTATIC_SENSOR_XMTR` | 纯发射传感器：100MHz, 50kW, 天线高90m, 200kHz带宽 |
| `BISTATIC_SENSOR_RCVR` | 纯接收传感器：100MHz, 噪声系数7dB, 检测阈值15dB, 积分增益1e5绝对 |
| `BISTATIC_SENSOR_RCVR_DF` | 测向接收机：525MHz, 950MHz带宽, 瞬时带宽10MHz, 噪声-175dBm |
| `BISTATIC_SENSOR_RCVR_MEAS` | 测量误差接收机：含`compute_measurement_errors true` |
| `RADAR_SIGNATURE` | 双基地雷达签名（5m², `use_bisector_for_bistatic true`） |
| `JET` | 喷气飞机目标平台 |
| `C4I_PLATFORM` | C4I指挥平台：100Mbit/s数据链，跟踪上报 |
| `RCVR_PLATFORM` | 接收平台：双基地传感器+数据链+C4I报告 |
| `C4I_PLATFORM_DF` / `RCVR_PLATFORM_DF` | 测向变体：`WSF_DIRECTION_FINDER_PROCESSOR` TDOA定位 |
| 诊断脚本(注释) | `SENSOR_DETECTION_ATTEMPT` 观察器脚本，输出收发距+SNR |

#### blocks/sensor_clutter.txt
**功能**: 雷达杂波模型：

| 组件 | 功能 |
|------|------|
| `global_environment` | 全局环境设置（通用地形、起伏地形、海况2级） |
| `EW_RADAR_CLUTTER` / `CLUTTER_NONE` | 表面杂波模型和无杂波模型 |
| `CIRCULAR_ANTENNA` | 圆形天线（5°波束，30dB） |
| `EW_RADAR_CLUTTER` 雷达 | 含杂波雷达：1.2GHz, 100kW, 垂直极化, 1μs脉宽, 1.5kHz PRF, Blake衰减模型, 杂波衰减因子-10dB, 检测阈值12.8dB |
| `TARGET_PLATFORM` | 通用目标平台（B-747图标，100m² RCS） |

#### blocks/sensor_coherent.txt
**功能**: 相干传感器处理：

| 组件 | 功能 |
|------|------|
| `EW_RADAR_SITE_COHERENT` | 多传感器相干融合站点：2部`EW_RADAR_COHERENT`雷达 + `WSF_COHERENT_SENSOR_PROCESSOR`（SNR加权平均融合） + 跟踪管理器 |
| `EW_RADAR_COHERENT` | 多波束雷达：2波束(920/925MHz)，100nm探测，750kW, 50μs脉宽, 750μs PRI, 前后比3/5和1/3, 上报距离/方位/IFF |

#### blocks/sensor_composite.txt
**功能**: 复合传感器（4面阵雷达）：

| 组件 | 功能 |
|------|------|
| `EW_RADAR_COMPOSITE` | 多波束雷达：2波束(200/225MHz)，水平偏振，Earce衰减，Swerling 1型检测，线性检测律，32脉冲积累 |
| 4面阵模板(注释) | 每面90°偏航，`WSF_COMPOSITE_SENSOR` 同步工作模式，4面融合 |

#### blocks/sensor_jamming.txt
**功能**: 电子战/干扰：

| 组件 | 功能 |
|------|------|
| `JAMMER_ANTENNA` | 干扰天线（常量1dB） |
| `JAMMER_EA` | 电子攻击定义：假目标干扰技术，产生1个假目标 |
| `JAMMER_FALSE_TARGET` | RF假目标干扰机：100MHz, 1W, 200kHz带宽, 100μs PRI, 11dB损耗 |
| `JAMMER_NOISE` | RF噪声干扰机：100MHz, 1W, 20MHz带宽, 11dB损耗 |
| 诊断脚本(注释) | `JAMMING_ATTEMPT` 观察器，输出噪声功率+JNR |

#### blocks/sensor_nav.txt
**功能**: 导航误差与GPS区域控制：

| 组件 | 功能 |
|------|------|
| `ZONE_BASED_GPS_STATUS_PROCESSOR` | 区域GPS控制脚本：检查平台GPS状态，`WithinZone("no_gps")` 内GPS不可用，外GPS可用 |
| `UAV_NAV` | 导航误差无人机：GPS in-track 8m, cross-track 2m, 垂直3m, INS垂直10m + 完美传感器 + 区域GPS处理器 |
| `NO_GPS_ZONE` 模板(注释) | 多边形GPS禁用区域定义 |

#### blocks/sensor_radar_ew.txt
**功能**: EW雷达传感器：

| 组件 | 功能 |
|------|------|
| `EW_RADAR_ANTENNA` / `EW_RADAR_ANTENNA_WIDE` | 矩形天线（35dB峰值, 5°/10°方位×45°仰角） |
| `AUX_ANTENNA` | 辅助全向天线（10dB, 360°） |
| `EW_RADAR` | 基本EW雷达：1GHz, 100W, 25μs脉宽, 1250μs PRI, Swerling 1型检测, Pd=0.5, Pfa=1e-6, 16脉冲积累 |
| `EW_RADAR_ESM_DEMO` | ESM演示雷达：900MHz, 750kW, 225km探测, 0.1MHz带宽, 上报位置/速度/SNR |
| `EW_RADAR_SITE` | EW雷达站点平台（地面+跟踪管理） |
| `STRIKER_PLATFORM` | 攻击机平台（F-18E, 10m² RCS, 空中运动体） |

#### blocks/sensor_sar.txt
**功能**: SAR合成孔径雷达：

| 组件 | 功能 |
|------|------|
| `UAV_SAR` | SAR无人机：左右双SAR传感器(±90°偏航) + `BeginImaging`(自动计算俯角, CueToAbsoluteAzEl, 选模)/`EndImaging` 脚本 + 图像处理器 + 数据链 + 任务管理器 + 跟踪管理器 |
| 窄波束SAR技术(注释) | `ApparentLocationOf()` 大气折射补偿 + 窄波束凝视(±0.01°) |

#### blocks/sensor_spin_scheduler.txt
**功能**: 旋转雷达调度器：

| 组件 | 功能 |
|------|------|
| `SPIN_RADAR_PLATFORM` | 旋转雷达平台：`spin` 调度器(30s扫描周期, 起始方位240°, 顺时针), 10GW峰值功率, 10GHz, 54km探测, 20s帧时, 上报位置/速度 |
| `SIG_1M2` / `TARGET_SPIN` | 1m² RCS目标平台 |

### 3.6 签名与天线文件

#### blocks/signatures_shared.txt
**功能**: 共享签名、数据链、滤波器、通用处理器：

| 组件 | 功能 |
|------|------|
| `VEHICLE_INFRARED_SIGNATURE` | 车辆红外签名（10W/sr常量） |
| `VEHICLE_OPTICAL_SIGNATURE` / `VEHICLE_RADAR_SIGNATURE` | 车辆光学(10m²)/雷达(1m²)签名 |
| `SHIP_INFRARED_SIGNATURE` / `SHIP_OPTICAL_SIGNATURE` / `SHIP_RADAR_SIGNATURE` | 舰船签名（红外10W/sr, 光学300m², 雷达1000m²） |
| `FIGHTER_RADAR_SIGNATURE` | 战斗机雷达签名（1m²常量） |
| `RED_DATALINK` | 红方数据链（100Mbit/s） |
| `FILTER_TACTICS` | Kalman滤波器（距离σ=50m, 方位σ=0.1°, 仰角σ=0.1°, 过程噪声XYZ=50/50/30） |
| `ANNOUNCE_LAUNCH_TACTICS` | 发射通告处理器：监听`WEAPON_FIRED`状态消息 → 创建新Track → 用`AssignTask`分派给指定类型的下属平台 |
| `INFLIGHT_UPDATE_TACTICS` | 飞行中目标更新处理器：通过数据链定期向武器通信设备发送更新后的Track消息（`WsfTrackMessage` + `SendMessage`），Map管理多武器-多Track更新调度 |

#### blocks/signatures_optical.txt
**功能**: 光学签名：

| 签名 | 功能 |
|------|------|
| `FIGHTER_SPHERICAL_OPTICAL_SIG` | 球形表面(半径2m, 绝热壁温) |
| `FIGHTER_BOX_OPTICAL_SIG` | 盒形表面(10×2×2m, 绝热壁温) |
| `FIGHTER_MULTI_SHAPE_OPTICAL_SIG` | 多形状复合：机翼(3×10×0.2m盒) + 机头(1m×0.7m锥) + 机身(10m×0.7m柱) + 尾焰(700K, 5m×0.5m) |
| `FIGHTER_MULTIRESOLUTION_OPTICAL_SIG` | 多分辨率光学签名：低(0-0.33球)→中(0.33-0.66盒)→高(0.66-1.0多形状) |
| `GROUND_SITE_RADAR_SIG` / `GROUND_SITE_OPTICAL_SIG` | 地面站签名（各50m²常量） |

#### blocks/signatures_radar.txt
**功能**: 雷达签名：

| 签名 | 功能 |
|------|------|
| `CONSTANT_RADAR_SIGNATURE` | 常量RCS（100m²） |
| `TABULAR_RADAR_SIGNATURE` | 角分表RCS：20个角度×2列(dBsm)，在±135°/±90°/±45°有20dB峰值，其他方向0dB |
| `MULTIRESOLUTION_RADAR_SIGNATURE` | 多分辨率雷达签名：低(0-0.5常量100m²)→高(0.5-1.0表分) |
| `BISTATIC_RADAR_SIGNATURE` | 双基地雷达签名（5m², 使用双基地平分线） |
| `FIGHTER_RADAR_SIGNATURE` | 战斗机雷达签名（10m²常量） |

#### blocks/antenna_patterns.txt
**功能**: 9种天线方向图模板合集：

| 天线 | 类型 | 参数 |
|------|------|------|
| `RECT_PATTERN_35dB_10x45` | 矩形 | 35dB, 10°方位×45°仰角 |
| `RECT_PATTERN_35dB_5x45` | 矩形 | 35dB, 5°方位×45°仰角 |
| `CIRC_PATTERN_30dB_5deg` | 圆形 | 30dB, 5°波束宽度 |
| `UNIFORM_10dB_360` | 均匀 | 10dB, 360° |
| `OMNI_0dB` | 全向 | 0dB |
| `OMNI_12dB` | 全向 | 12dB |
| `OMNI_1dB` | 全向 | 1dB |
| `SINE_0dB_360x45` | 正弦 | 0dB峰值, 360°方位×45°仰角 |

### 3.7 处理器文件

#### blocks/processor_definitions.txt
**功能**: 5种通用处理器定义：

| 处理器 | 功能 |
|--------|------|
| `ZONE_BASED_GPS_STATUS_PROCESSOR` | 区域GPS控制：5s间隔检查`GPS_Status()` → 在"no_gps"区内设-1(不可用)，反之设1(可用) |
| `TRIMSIM_PROCESSOR` | TDOA定位处理器（最小检测数2） |
| `DIRECTION_FINDER_PROCESSOR` | 测向处理器：收集替换间隔30s, 最大时间差10s, 使用真值高度, 滤波器旁通 |
| `MESSAGE_RECEIVER` | 消息接收记录器：`on_message` 记录来源/通信类型/时间/数据标签 |
| `LOW_FIDELITY_TASK_PROCESSOR` | 低精度任务处理器：10s间隔 → MOVING状态 → 直飞指定位置(0.3N,0E,6096m高度) |
| `HIGH_FIDELITY_TASK_PROCESSOR` | 高精度任务处理器：SEARCHING(1s) → 发现目标 → MOVING(0.5s) 追击 → 进入200m内捕获 |

#### blocks/processor_launch.txt
**功能**: 武器发射控制处理器 `LAUNCH_WEAPON_PROCESSOR`：
- 可配置发射时间（固定/随机）
- `on_initialize`：随机模式时 `RANDOM.Uniform(MIN_TIME, MAX_TIME)`
- `on_update`(每10s)：时间到了 → 从`MasterTrackList()`取Track → `CueToTarget` → `Fire` → trackIndex递增 → 用完后处理器自关闭
- 可配脚本变量：`WEAPON_NAME`, `TIME_TO_LAUNCH`, `LAUNCH_RANDOM`, `MIN_TIME`, `MAX_TIME`

### 3.8 战术处理器文件

#### blocks/tactics_sam.txt
**功能**: SAM交战战术处理器 `SAM_TACTICS_PROCESSOR`（状态机）：

| 状态 | 功能 |
|------|------|
| DETECTED | 等待条件：目标存活 + 可交战（自己是指挥官/收到任务/ENGAGE级别>0 + 空中目标） → ENGAGE |
| ENGAGE | 检查目标存活+正在跟踪 → 在拦截包络内 + 无活跃武器 → `LaunchWeapon`(2发齐射) → 射击日志输出 |
| 拦截包络检查 | 最小300m ~ 最大35000m |
| 传感器支持 | 可选传感器名称+模式配给 |

#### blocks/tactics_naval_sam.txt
**功能**: 海军SAM战术完整套装（状态机 + 发射计算机 + 3种SAM武器）：

| 组件 | 功能 |
|------|------|
| `NAVAL_SAM_TACTICS` | 4状态机：DETECTED→ENGAGEABLE→ENGAGE→FIRING。支持可选照明器体制(`USE_ILLUMINATOR`)。包含 `IlluminateTarget`(遍历4个FRONT_DOME照明器)、`InInterceptEnvelopeOf`(调用`Local_SAM_LaunchComputer`)、`Engage`(传感器追踪请求管理)、`LaunchWeapon`(齐射) |
| `RED_SR_SAM_1_LaunchComputer` | 驱逐舰发射计算机：2D拦截位置计算(`InterceptLocation2D`), 最大12km, 飞行25s, 区域检查 |
| `RED_SR_SAM_2_LaunchComputer` | 护卫舰发射计算机：最大40km, 飞行45s |
| `SAM_LaunchComputer` | 发射计算机分配器：根据平台类型分发 |
| `Local_SAM_LaunchComputer` | 本地发射计算机：根据武器类型分发 |
| `RED_SR_SAM_1`(导弹+武器) | 短程SAM(12km)：84.5kg, 推力5200lbf×2.5s, 制导计算机(PN6.0+VP6.0, +1.0g偏置, max25g), 8发弹匣+5分钟重装(8发) |
| `RED_SR_NAVAL_SAM_1`(导弹+武器) | 海军SAM(30km)：2级(230kg燃料+70kg燃料), 23g机动, 2发弹匣+12s增量重装, 46发总库存 |
| `RED_SR_SAM_2`(导弹+武器) | 远程SAM(40km)：2级(265kg+80kg), 4.0马赫最大, 含`WSF_PERFECT_TRACKER`自主导引头, 32发, 2s齐射间隔 |

#### blocks/tactics_naval_asm.txt
**功能**: 海军反舰导弹战术完整套装：

| 组件 | 功能 |
|------|------|
| `NAVAL_ASM_TACTICS` | 4状态机：DETECTED→ENGAGEABLE→ENGAGE→FIRING。仅打击海面目标(`TRACK.SurfaceDomain()`), 支持可选传感器名称 |
| `ASM_TACTICS` | ASM飞行中制导处理器：ENROUTE(巡航50m, 朝向目标)→ACQUIRING_TARGET(进入导引头激活距离10000m内启动雷达搜索)→TERMINAL(终段降至10m俯冲) |
| `RED_ASM_MSL_LaunchComputer` | 发射计算机：最大120km, 飞行392s |
| `RED_ASM_MSL`(导弹+武器) | 亚音速反舰导弹(306m/s)：`WSF_AIR_MOVER`, 27m/s俯冲率, 2g机动, `RED_MISSILE_SEEKER_1`导引头(仅海面), `on_create`创建动态航线+`FollowRoute`, 8发, ±90°方位回转, 15°仰角 |
| `BLUE_ASM_MISSILE`(导弹+武器) | 高机动ASM：含`WSF_GUIDED_MOVER`单级(519kg初始, 200kg燃料, 2900N×1000s)→`WSF_GUIDANCE_COMPUTER`三阶段：CRUISE(75m/537mph沿航线, 到3km处)→POPUP(爬升至6000m)→DIVE(俯冲攻击), 最大10g |

#### blocks/tactics_naval_ssm.txt
**功能**: 海军面-面导弹战术完整套装：

| 组件 | 功能 |
|------|------|
| `NAVAL_SSM_TACTICS` | 4状态机：DETECTED→ENGAGEABLE→ENGAGE→FIRING。打击海面+陆地目标 |
| `SSM_MISSILE_LaunchComputer` | 发射计算机：最大920km, 飞行692s |
| `SSM_MISSILE`(导弹+武器) | 远程SSM：`WSF_GUIDED_MOVER`(1400lbm, 900lbm燃料, 12500lbf×18.3s)→`WSF_GUIDANCE_COMPUTER`(PN8.0, +3.0g偏置, 2s延迟, max6g)→导引头(1m²RCS常值)→引信(680s)→2min脚本调g_bias→5.5min再次调g_bias→导引头30km前自动开启→VLS风格发射(60fps Δv) |

### 3.9 武器文件

#### blocks/weapon_aam.txt
**功能**: 远程空对空导弹 `LRSAM`（来自engage演示）完整定义：
- **签名**: 红外1W/sr, 光学1m², 雷达1m²
- **制导计算机**: LAUNCH(延迟100s, 0.8s后)→TERMINAL(PN4.0, +1.0g偏置, guide_to_truth)
- **气动**: Cd0_sub=0.10, Cd0_super=0.25, 参考面积0.159m², CLmax=10.0, 展弦比16.0
- **3级运动体**: ①0.0078kg助推(51479N×0.77s)→②1284kg主燃烧(157386N×20s, 推力矢量15°×0.77-5s)→③854kg被动滑行
- **导引头**: `WSF_PERFECT_TRACKER`(0.1s)
- **引信**: `WSF_AIR_TARGET_FUSE`(粗略100km/击中90km)
- **武器**: VLS发射(22.4m/s Δv), 倾斜89.999°, 方位回转±180°, 4发, 随机3-5s齐射间隔

### 3.10 多分辨率文件（5个）

#### blocks/multires_comm.txt
**功能**: 多分辨率通信模型：

| 组件 | 功能 |
|------|------|
| `TEAM_DATALINK` | 简单数据链（100Mbit/s） |
| `TEAM_RADIOLINK` | 物理无线电链路（100MHz, 1.21GW, 100km） |
| `MESSAGE_RECEIVER` | 消息接收脚本处理器 |
| `MR_COMM` | 多分辨率通信：fidelity 0-0.5用数据链，0.5-1.0用物理无线电 |
| 网络使用示例(注释) | 指挥链 + Mesh网络 |
| `script_variables` | commName共享变量 |

#### blocks/multires_fuel.txt
**功能**: 多分辨率燃油模型：

| 组件 | 功能 |
|------|------|
| `LOW_FIDELITY_FUEL` | 低精度燃油：最大10000kg, 初始1000kg, 恒消耗率1kg/s |
| `HIGH_FIDELITY_FUEL` | 高精度燃油：表格化消耗率(按高度/马赫查表) |
| `MR_FUEL` | 多分辨率燃油：fidelity 0-0.5恒速率，0.5-1.0表格 |
| `MR_FUEL_FIGHTER` | 燃油演示平台：F-18, 空气运动体(5s更新), 航线飞行 |

#### blocks/multires_mover.txt
**功能**: 多分辨率运动体：

| 组件 | 功能 |
|------|------|
| `MR_AIR_MOVER` | 多分辨率空中运动体：低精度(30s更新), 高精度(0.1s更新) |
| `MR_SPACE_MOVER` | 多分辨率空间运动体：低精度`WSF_SPACE_MOVER`(Keplerian), 高精度`WSF_INTEGRATING_SPACE_MOVER`(Prince-Dormand78积分器, 大气阻力+地球单极+J2+日月木星引力) |
| `common`块 | 共享轨道参数(偏心率1e-3, 半长轴6600km, 倾角0°, RAAN/真近点角/近地点角0°) |

#### blocks/multires_processor.txt
**功能**: 多分辨率处理器：

| 组件 | 功能 |
|------|------|
| `LOW_FIDELITY_TASK_PROCESSOR` | 低精度：10s间隔 → 直飞(0.3N, 0E, 6096m), 速度250 |
| `HIGH_FIDELITY_TASK_PROCESSOR` | 高精度：SEARCHING(1s)→MOVING(0.5s)→捕获(<200m) |
| `MR_TASK_PROCESSOR` | 多分辨率任务处理器：fidelity 0-0.5低精度, 0.5-1.0高精度 |
| `MR_MESSAGE_PROCESSOR` | 多分辨率消息处理器：不同fidelity输出不同消息前缀 |

#### blocks/multires_sensor.txt
**功能**: 多分辨率传感器：

| 组件 | 功能 |
|------|------|
| `MR_SENSOR` | 多分辨率传感器：fidelity 0-0.5用`WSF_GEOMETRIC_SENSOR`(简单快速), 0.5-1.0用`GENERIC_IRST`(物理精细化) |
| `common`块 | 共享参数(on, 上报距离, 10s帧时, ±45°视场, 50nm, 回转参数) |
| `MR_SENSOR_SITE` | 传感器站点平台（含跟踪管理+图像处理） |

### 3.11 LEO通信文件

#### blocks/satellite_leo.txt
**功能**: 简单LEO通信卫星 `LEO_SAT`（单星+单地面站）：
- `WSF_AIR_MOVER`(10000-14500kts, 500-600km高度)
- Ka下行(28GHz, 30W, 25dBi, 10Mbit/s)
- `link_budget`脚本处理器：每1s计算对"Wuhan_Ground_Station"的斜距/地面距/延迟, 根据2500km判断UP/DOWN

#### blocks/station_ground_leo.txt
**功能**: 简单地面站 `SAT_GS`（单站）：
- Ka接收(28GHz, 32dBi, 1.5dB损耗, -130dBm噪声, 12dB阈值)
- `log`脚本处理器：每5s输出在线日志

#### blocks/main_leo_comm.txt
**功能**: LEO通信主入口文件模板：
- `define_path_variable CASE leo_comm`
- event_output启用8种事件（武器/平台/通信开关/消息收发）
- event_pipe high预设
- `end_time 90 sec`, `start_date Apr 18 2025`

#### blocks/scenario_leo_comm.txt
**功能**: LEO通信布设：
- `Leo_Satellite_1`：27N 110E 550km高度, 航线(27N110E→33N120E@14000kts)
- `Wuhan_Ground_Station`：30N 115E 50m
- `LeoSatNet`：卫星下行↔地面站接收

### 3.12 leo_constellation/ 子目录（5文件）

#### blocks/leo_constellation/README.md
**功能**: 6星星座说明文档（网络架构图+参数表+使用方法）

#### blocks/leo_constellation/satellite_leo_block.txt
**功能**: 星座卫星 `LEO_SAT`（功能比单星版本丰富得多）：

| 组件 | 功能 |
|------|------|
| `ISL_60GHZ_ANT` | V波段星间链路天线（22dBi, 60GHz） |
| `SAT_KA_DOWNLINK_ANT` | Ka下行天线（24dBi, 27.5GHz） |
| `SAT_KA_UPLINK_ANT` | Ka上行天线（24dBi, 17.5GHz） |
| `isl_xcvr` | 星间链路收发器（20W, 1dB损耗, 20Mbps, LeoSatNet） |
| `ka_downlink` | 下行（25W, 0.5dB损耗, 8Mbps, GroundFeederNet） |
| `ka_uplink` | 上行（-125dBm噪声, 10dB阈值） |
| `link_budget` 处理器 | 每1s输出：星间链路(前后邻居)+地面链路(2网关+1移动终端), 计算斜距/地面距/仰角/延迟/链路状态 |
| `handover` 处理器 | 每1s对移动终端输出候选卫星(仰角≥7°) |
| `on_init` | 从平台名提取卫星编号(`substr(9)`) |

#### blocks/leo_constellation/gateway_station_block.txt
**功能**: 网关地面站 `GATEWAY_GS`：
- Ka上下行(33dBi, 27.5GHz收/17.5GHz发, 2dB损耗, -130dBm噪声, 12dB阈值, 8Mbps)
- `gs_monitor`处理器：每5s输出在线状态

#### blocks/leo_constellation/mobile_terminal_block.txt
**功能**: 移动终端 `MOBILE_TERMINAL`：
- `WSF_GROUND_MOVER`(1-30kts)
- Ka收发(18dBi, 27.5GHz, 5W, 2dB损耗, 8Mbps)
- `mt_handover`处理器(核心)：每1s扫描6颗卫星 → 计算仰角 → 选择仰角≥7°的最优卫星 → 检测切换事件 → 输出：`HANDOVER FROM=xxx TO=yyy ELEV=zz` / `SERVING_SAT=xxx ELEV=yy`

#### blocks/leo_constellation/deployment_scenario.txt
**功能**: 完整星座部署（6星+2网关+1移动终端+全部网络）：

| 组件 | 内容 |
|------|------|
| `Leo_Sat_1~6` | 6颗卫星，同轨道面(50°倾角)，60°相位间隔，每颗15个航路点(完整闭合轨道)，520km高度，16000kts |
| `Gateway_A` | 32N 118E（南京-合肥一带） |
| `Gateway_B` | 25N 113E（广东-湖南交界） |
| `Mobile_Terminal` | 29N 116E→30.5N 117.5E，8kts航行，45°航线 |
| `LeoSatNet` | 环形ISL：每个卫星 ↔ 前后邻居 |
| `GroundFeederNet` | 星状：所有6星下行→2网关 |

#### blocks/leo_constellation/network_definitions.txt
**功能**: 独立网络定义（与deployment_scenario.txt中重复，可选独立include）：
- `LeoSatNet`：环形ISL（使用`isl_xcvr`收发器而不是`isl_xmtr`/`isl_rcvr`）
- `GroundFeederNet`：所有6星→2网关

---

## 四、references/ — 离线参考手册（17文件）

### 4.1 afsim_syntax.md
**功能**: AFSIM 2.9.0 语法速查指南，覆盖：
- 项目结构
- main.txt模板（`define_path_variable`, `end_time 120 secs`）
- event_output配置（8种事件类型）
- Event Pipe动画输出（`use_preset default|low|high|full`）
- 平台类型定义模板（`platform_type xxx WSF_PLATFORM`）
- 平台实例化模板（坐标N/S/E/W后缀）
- 武器定义（简单直飞/制导运动体两种）
- 脚本处理器模板（`FindPlatform → MakeTrack → CueToTarget → Fire`）
- 制导计算机模板
- 编译命令（`mission.exe -es main.txt`，需先cd到项目目录）
- 15种常见编译错误+修复方案
- 8种关键脚本方法速查

### 4.2 WSF 命令参考文件（10个）
这些文件是从2488页 AFSIM 参考手册中提取的命令列表：

| 文件 | 内容 |
|------|------|
| `wsf_radar_sensor.txt` | 60条雷达传感器命令（模式UUID, UCI AMTI/ESM/POST消息, 能力设置等） |
| `wsf_air_mover.txt` | 35条空中运动体命令（导航, 偏移, 转向, 速度, 加速度, 航线变换, 插入航线等） |
| `wsf_ground_mover.txt` | 地面运动体命令 |
| `wsf_guided_mover.txt` | 制导运动体命令（级配置, 推力, 比冲等） |
| `wsf_guidance_computer.txt` | 制导计算机命令（阶段, 导引律, 航迹角等） |
| `wsf_launch_computer.txt` | 弹道发射计算机命令 |
| `wsf_explicit_weapon.txt` | 显式武器命令 |
| `wsf_straight_line_mover.txt` | 直线运动体命令 |
| `wsf_script_processor.txt` | 脚本处理器命令 |
| `weapon_effects.txt` | 18种武器效果命令（`WSF_GRADUATED_LETHALITY`：离散/插值, 2D/3D半径, radius_and_pk, 目标类型, 杀伤类型MK/FK/KK等） |

### 4.3 类型索引文件（4个）

| 文件 | 内容 |
|------|------|
| `mover_types.txt` | 47种运动体类型（含继承关系注释） |
| `processor_types.txt` | 50种处理器类型（含继承关系注释） |
| `sensor_types.txt` | 25种传感器类型 |
| `weapon_types.txt` | 23种武器类型 |

### 4.4 其他参考文件

| 文件 | 功能 |
|------|------|
| `reference_manual.txt` | AFSIM 2.9.0 完整参考手册（2.7MB），被 lookup.py 和 index_manual.py 使用 |
| `extract_1742_1764_output.txt` | 手册第1742-1764页提取文本（`extract_pages.py` 生成） |

---

## 五、scripts/ — Python 工具脚本（8文件）

### 5.1 analyze_leo_comm.py
**核心分析工具**，实现完整数据处理管线：

| 功能模块 | 详述 |
|----------|------|
| **全盘 AFSIM 扫描**(`scan_for_afsim`) | ①检查`AFSIM_HOME`环境变量 → ②检查10个常见安装目录 → ③`cmd /c dir /s`全盘搜索`mission.exe` |
| **编译执行**(`compile_and_run`) | 运行`mission.exe -es main.txt`（300s超时），捕获stdout/stderr，保存.log文件（自动从主文件名派生），列出输出文件 |
| **链路数据解析**(`parse_links`) | 从.evt或.log中提取 TIME/RNG/GRND/DELAY/LINK 数据（正则：`RNG=xxx GRND=xxx DELAY=xxxms LINK=xx`），支持科学计数法 |
| **星座日志解析**(`parse_constellation_log`) | 提取卫星链路数据（`SATn_RNG=…GS=name`）、切换事件（`HANDOVER FROM=…TO=…`）、服务卫星（`SERVING_SAT=…`）、ISL数据（`RNG_ISL_PREV/NEXT=…`） |
| **物理计算** | `compute_elevation`(从斜距/地面距反算仰角 = atan2(sat_alt, ground)), `compute_fsl`(20log₁₀(4πR/λ)), `compute_rx_power`(Pr = Pt+Gt+Gr-FSL-losses) |
| **6面板绘图**(`plot_leo_comm`) | 3×2布局：①斜距(km) ②地面距(km) ③仰角(deg) ④传播延迟(ms) ⑤自由空间损耗@28GHz(dB) ⑥接收功率(dBm)；每种图区分Link UP(绿)/DOWN(红)；输出.png + .csv |
| **星座绘图**(`plot_constellation`) | ①6星仰角时序图 ②移动终端切换时间线图 ③ISL距离图 ④切换事件列表输出 |
| **Mystic 3D**(`open_mystic`) | 自动打开.aer文件到Mystic可视化器（Windows用`os.startfile`） |
| **主文件检测**(`detect_main_file`) | 扫描目录中`.txt`文件，通过`define_path_variable`/`end_time`特征识别主入口文件 |
| **编码自动检测** | BOM嗅探：`\xff\xfe`→UTF-16，否则UTF-8 |
| **CLI参数** | `--main`, `--evt`, `--log`, `--output`, `--afsim-home`, `--plot-only`, `--compile-only`, `--no-mystic` |

### 5.2 parse_evt_full.py
**通用EVT全数据提取器**：

| 功能模块 | 详述 |
|----------|------|
| **多格式解析** | 支持 `KEY=VALUE`、`KEY: VALUE`、`HH:MM:SS.S`时间戳、DMS经纬度(`27:00:00.00n`)、续行符(`\`) |
| **时间转换** | `time_to_seconds`：HH:MM:SS.S → 秒，也处理纯浮点数 |
| **DMS解析** | `parse_dms`：`02:30:00.00n` → 2.50000十进制度 |
| **日志解析**(`parse_log_file`) | 从.log提取`RNG=`/`GRND=`开头的行，解析所有KEY=VALUE |
| **EVT解析**(`parse_evt_all`) | 逐行解析：时间 → 事件类型 → 实体名 → KEY=VALUE → KEY:VALUE → LLA特殊处理(拆分lat/lon/alt) |
| **CSV写入** | 自动去除单位后缀(ms/km/m/dB/...)、处理向量`* [x y z]`、数值/文本智能区分 |
| **绘图** | 自动检测数值列，每列一个子图(TIME作x轴) |
| **摘要** | 按事件类型计数、字段统计(唯一值/数据类型) |
| **双源合并** | `merge_rows`：.evt + .log 字段union后合并 |

### 5.3 其他脚本

| 文件 | 功能 |
|------|------|
| `lookup.py` | 手册关键词搜索器：`python lookup.py WSF_AIR_MOVER` → 在`reference_manual.txt`中查找并输出前后上下文(前200后2000字符)，最多3个匹配 |
| `index_manual.py` | 手册索引生成器：从`reference_manual.txt`提取10种主要AFSIM类型的命令列表，生成`wsf_*.txt`引用文件；同时统计并生成`sensor_types.txt`/`processor_types.txt`/`mover_types.txt`/`weapon_types.txt` |
| `extract_pages.py` | PDF页面提取器：用PyMuPDF从2488页PDF中提取指定页码范围(1742-1764)的文本+图像 |
| `audit_mover.txt` | 运动体命令审计报告（验证哪些命令在手册中存在） |
| `audit_processor.txt` | 处理器命令审计报告 |
| `audit_sensor.txt` | 传感器命令审计报告 |

---

## 六、templates/ — 完整可编译项目模板（16文件）

### 6.1 基础模板项目

#### templates/main.txt
**功能**: 最简 AFSIM 项目入口：
- `define_path_variable CASE my_scenario`
- 事件输出(.evt) + 动画管道(.aer, high预设)
- include setup.txt → blue_laydown → red_laydown
- `end_time 120 secs`

#### templates/setup.txt
**功能**: 类型定义加载：
- `file_path .`
- include_once：tank, building, missile, missile_processor

#### templates/event_output.txt
**功能**: 事件输出配置：
- 启用9种事件：WEAPON_FIRED/HIT/MISSED/TERMINATED, PLATFORM_ADDED/DELETED, SENSOR_TRACK_INITIATED, TASK_ASSIGNED
- 时间格式 `h:m:s.1`

### 6.2 平台模板

| 文件 | 平台类型 | 功能 |
|------|----------|------|
| `templates/platforms/tank.txt` | `TANK` | 红方坦克：3×8×4m, `WSF_GROUND_MOVER`, 10发`RED_TANK_MISSILE`, `MISSILE_LAUNCH_PROCESSOR` |
| `templates/platforms/building.txt` | `BUILDING` | 蓝方建筑：30×20×20m, `WSF_GROUND_MOVER`, 无武器 |
| `templates/platforms/fighter.txt` | `FIGHTER_AIRCRAFT` | 红方战斗机：F-18, 3×15×10m, 10000kg空重, `WSF_AIR_MOVER`(100-500kts, max15000m), 8发`AA_MRM`中程空空导弹, `FIRE_CONTROL_RADAR`, `AA_TACTICS`状态机 |

### 6.3 武器模板

| 文件 | 武器 | 功能 |
|------|------|------|
| `templates/weapons/missile.txt` | `RED_TANK_MISSILE` | 最简导弹：`WSF_STRAIGHT_LINE_MOVER`(300kts) + `WSF_GRADUATED_LETHALITY`(50m/1.0PK) + `WSF_GROUND_TARGET_FUSE` |

### 6.4 处理器模板

| 文件 | 处理器 | 功能 |
|------|--------|------|
| `templates/processors/missile_processor.txt` | `MISSILE_LAUNCH_PROCESSOR` | 脚本发射处理器：固定时间(TIME_TO_LAUNCH=5s)/按名查找目标(`WsfSimulation.FindPlatform`)→`CueToTarget`→`Fire` |
| `templates/processors/aa_tactics.txt` | `AA_TACTICS` | 空对空战术状态机：DETECTED→ENGAGEABLE→ENGAGE，含发射计算机(`Local_AA_LaunchComputer`)，传感器追踪管理，武器齐射控制 |

### 6.5 传感器模板

| 文件 | 传感器 | 功能 |
|------|--------|------|
| `templates/sensors/fire_control_radar.txt` | `FIRE_CONTROL_RADAR` | 火控雷达：正弦天线(30dB, 4°波束), 3GHz, 250kW, 1MHz带宽, ±15°扫描, 2-90km, 定位精度(0.3°方位/仰角, 4m距离), 前后比2/2和1/2 |

### 6.6 想定模板

| 文件 | 功能 |
|------|------|
| `templates/scenarios/blue_laydown.txt` | 蓝方布设：`Blue_Base BUILDING` @ 34.05N 118.05W（先定义，作为预置跟踪目标） |
| `templates/scenarios/red_laydown.txt` | 红方布设：`Red_Tank TANK` @ 34.0N 118.0W altitude 10m，预跟踪Blue_Base，发射时间5s |

### 6.7 LEO星座模板（5文件）

#### templates/leo_constellation/leo_constellation.txt
**功能**: 星座主入口（与 `blocks/main_leo_comm.txt` 类似，但针对星座）：
- `end_time 5693 sec`（≈94.9分钟，完整轨道周期）
- 额外增加 `csv_event_output enable all`
- include_once三平台 + include布设

#### templates/leo_constellation/setup.txt
**功能**: 星座类型加载：
- include_once三平台（leo_satellite, gateway_station, mobile_terminal）

#### templates/leo_constellation/platforms/leo_satellite.txt
**功能**: LEO卫星平台（内容与 `blocks/leo_constellation/satellite_leo_block.txt` 完全一致，被复制为独立可编译文件）：
- 60GHz ISL(V波段, 22dBi, 20W, 20Mbps) + Ka上下行(27.5/17.5GHz, 24dBi, 8Mbps)
- `link_budget`处理器：ISL双向距离/延迟 + 地面链路仰角判断(≥6°网关/≥7°终端)
- `handover`处理器：对移动终端输出候选卫星

#### templates/leo_constellation/platforms/gateway_station.txt
**功能**: 网关地面站（内容与 `blocks/leo_constellation/gateway_station_block.txt` 一致）：
- Ka收发(33dBi, 27.5GHz, 2dB损耗), `gs_monitor`每5s状态输出

#### templates/leo_constellation/platforms/mobile_terminal.txt
**功能**: 移动终端（内容与 `blocks/leo_constellation/mobile_terminal_block.txt` 一致）：
- 18dBi Ka收发, 1-30kts移动, `mt_handover`自动切换处理器

#### templates/leo_constellation/scenarios/laydown.txt
**功能**: 星座布设（内容与 `blocks/leo_constellation/deployment_scenario.txt` 相似）：
- 6颗卫星(15航路点完整轨道) + 2网关 + 1移动终端 + LeoSatNet环形ISL + GroundFeederNet星状地面

---

## 七、文件统计总表

| 目录 | 文件数 | 文件类型 | 核心功能 |
|------|--------|----------|----------|
| blocks/ | 36 | .txt(35) + .md(1) | 可复用AFSIM代码块 |
| blocks/leo_constellation/ | 5 | .txt(4) + .md(1) | LEO星座专项 |
| references/ | 17 | .md(1) + .txt(15) + 无扩展(1) | 命令参考+类型索引 |
| scripts/ | 8 | .py(5) + .txt(3) | Python分析+审计工具 |
| templates/ | 11 | .txt | 基础场景模板 |
| templates/leo_constellation/ | 5 | .txt | LEO星座可运行模板 |
| **总计** | **82** | | |

---

## 八、按仿真领域分类速查

| 领域 | 相关文件 |
|------|----------|
| **地空导弹(SAM)** | `launcher_sam.txt`, `missile_sam.txt`, `radar_sam.txt`, `tactics_sam.txt` |
| **弹道导弹(SRBM/MRBM)** | `launcher_ballistic.txt`, `missile_ballistic.txt` |
| **战区弹道(TBM)** | `launcher_tbm.txt`, `missile_tbm.txt` |
| **海军作战** | `platform_naval_ship.txt`, `tactics_naval_sam.txt`, `tactics_naval_asm.txt`, `tactics_naval_ssm.txt`, `signatures_shared.txt` |
| **空空作战** | `weapon_aam.txt`, `templates/platforms/fighter.txt`, `templates/processors/aa_tactics.txt`, `templates/sensors/fire_control_radar.txt` |
| **雷达传感器** | `radar_sam.txt`, `radar_tracker.txt`, `sensor_radar_ew.txt`, `sensor_clutter.txt`, `sensor_bistatic.txt`, `sensor_coherent.txt`, `sensor_composite.txt`, `sensor_spin_scheduler.txt` |
| **光电/红外/ESM** | `sensor_eoir.txt`, `sensor_esm.txt` |
| **SAR雷达** | `sensor_sar.txt` |
| **电子战/干扰** | `sensor_jamming.txt` |
| **导航/GPS** | `sensor_nav.txt` |
| **导弹导引头** | `missile_seekers.txt` |
| **LEO通信(单星)** | `satellite_leo.txt`, `station_ground_leo.txt`, `main_leo_comm.txt`, `scenario_leo_comm.txt` |
| **LEO星座(6星)** | `leo_constellation/*` 全套 + `templates/leo_constellation/*` 全套 |
| **签名/天线** | `signatures_shared.txt`, `signatures_optical.txt`, `signatures_radar.txt`, `antenna_patterns.txt` |
| **多分辨率** | `multires_comm.txt`, `multires_fuel.txt`, `multires_mover.txt`, `multires_processor.txt`, `multires_sensor.txt` |
| **数据处理分析** | `scripts/analyze_leo_comm.py`, `scripts/parse_evt_full.py`, `scripts/lookup.py` |
| **手册参考** | `references/` 全部17文件 |
