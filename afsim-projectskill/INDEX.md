# INDEX.md — AFSIM Skill 文件索引

> 本文件是技能文件的完整索引。用 `read()` 按需加载具体文件。

---

## blocks/ — 可复用代码块

### 平台

| 文件 | 路径 | 用途 |
|------|------|------|
| platform_air_target.txt | `blocks/platform_air_target.txt` | 简单空中目标（WSF_AIR_MOVER） |
| platform_ground_target.txt | `blocks/platform_ground_target.txt` | 简单地面目标 |
| platform_naval_ship.txt | `blocks/platform_naval_ship.txt` | 海军舰艇（4种：通用导弹舰/驱逐舰/护卫舰/舰载直升机） |
| platform_types.txt | `blocks/platform_types.txt` | 6种复合平台类型定义 |
| satellite_leo.txt | `blocks/satellite_leo.txt` | LEO 通信卫星 |
| station_ground_leo.txt | `blocks/station_ground_leo.txt` | 卫星地面站 |

### 启动器

| 文件 | 路径 | 用途 |
|------|------|------|
| launcher_ballistic.txt | `blocks/launcher_ballistic.txt` | 弹道导弹发射车（SRBM/MRBM） |
| launcher_sam.txt | `blocks/launcher_sam.txt` | 地对空导弹发射平台（含雷达+武器+处理器） |
| launcher_tbm.txt | `blocks/launcher_tbm.txt` | 战区弹道导弹发射器 |

### 导弹

| 文件 | 路径 | 用途 |
|------|------|------|
| missile_ballistic.txt | `blocks/missile_ballistic.txt` | 弹道导弹完整栈（aero, mover, guidance, LC） |
| missile_sam.txt | `blocks/missile_sam.txt` | 防空导弹（aero + 4阶段制导 mover + weapon） |
| missile_tbm.txt | `blocks/missile_tbm.txt` | 战区弹道导弹（单级/双级） |
| missile_seekers.txt | `blocks/missile_seekers.txt` | 导弹导引头雷达传感器 |

### 传感器

| 文件 | 路径 | 用途 |
|------|------|------|
| sensor_bistatic.txt | `blocks/sensor_bistatic.txt` | 双基地雷达（含干扰变体） |
| sensor_clutter.txt | `blocks/sensor_clutter.txt` | 杂波模型生成 |
| sensor_coherent.txt | `blocks/sensor_coherent.txt` | 相干传感器处理器 |
| sensor_composite.txt | `blocks/sensor_composite.txt` | 复合传感器融合 |
| sensor_eoir.txt | `blocks/sensor_eoir.txt` | 光电/红外传感器 |
| sensor_esm.txt | `blocks/sensor_esm.txt` | ESM 被动射频传感器 |
| sensor_jamming.txt | `blocks/sensor_jamming.txt` | 干扰效果 |
| sensor_nav.txt | `blocks/sensor_nav.txt` | 导航雷达 |
| sensor_radar_ew.txt | `blocks/sensor_radar_ew.txt` | 电子战雷达（含干扰） |
| sensor_sar.txt | `blocks/sensor_sar.txt` | SAR 合成孔径雷达 |
| sensor_spin_scheduler.txt | `blocks/sensor_spin_scheduler.txt` | 旋转调度器演示 |
| radar_sam.txt | `blocks/radar_sam.txt` | SAM 火控雷达 |
| radar_tracker.txt | `blocks/radar_tracker.txt` | 通用跟踪雷达 |

### 处理器

| 文件 | 路径 | 用途 |
|------|------|------|
| processor_definitions.txt | `blocks/processor_definitions.txt` | 通用处理器语法 |
| processor_launch.txt | `blocks/processor_launch.txt` | 发射时序脚本（定时/随机） |
| tactics_sam.txt | `blocks/tactics_sam.txt` | SAM 交战状态机 |
| tactics_naval_sam.txt | `blocks/tactics_naval_sam.txt` | 海军 SAM 交战逻辑 |
| tactics_naval_asm.txt | `blocks/tactics_naval_asm.txt` | 海军反舰导弹交战逻辑 |
| tactics_naval_ssm.txt | `blocks/tactics_naval_ssm.txt` | 海军舰对舰导弹交战逻辑 |

### 签名与天线

| 文件 | 路径 | 用途 |
|------|------|------|
| signatures_shared.txt | `blocks/signatures_shared.txt` | 共享 IR/光学/雷达签名、数据链、滤波器 |
| signatures_optical.txt | `blocks/signatures_optical.txt` | 光学签名定义 |
| signatures_radar.txt | `blocks/signatures_radar.txt` | 雷达签名定义 |
| antenna_patterns.txt | `blocks/antenna_patterns.txt` | 天线方向图模板 |

### 多分辨率演示

| 文件 | 路径 | 用途 |
|------|------|------|
| multires_comm.txt | `blocks/multires_comm.txt` | 通信组件 |
| multires_fuel.txt | `blocks/multires_fuel.txt` | 燃料系统 |
| multires_mover.txt | `blocks/multires_mover.txt` | Mover 类型 |
| multires_processor.txt | `blocks/multires_processor.txt` | 处理器类型 |
| multires_sensor.txt | `blocks/multires_sensor.txt` | 传感器类型 |

### 武器

| 文件 | 路径 | 用途 |
|------|------|------|
| weapon_aam.txt | `blocks/weapon_aam.txt` | 空对空导弹（主动雷达） |

### LEO 星座通信

| 文件 | 路径 | 用途 |
|------|------|------|
| main_leo_comm.txt | `blocks/main_leo_comm.txt` | 主入口文件模板 |
| scenario_leo_comm.txt | `blocks/scenario_leo_comm.txt` | 卫星 + 地面站布设 |
| leo_constellation/ | `blocks/leo_constellation/` | 6星 LEO 星座 + 2地面网关 + 1移动终端 |
| satellite_leo_block.txt | `blocks/leo_constellation/satellite_leo_block.txt` | LEO_SAT 平台（ISL + 链路预算 + 切换） |
| gateway_station_block.txt | `blocks/leo_constellation/gateway_station_block.txt` | 网关站（Ka波段） |
| mobile_terminal_block.txt | `blocks/leo_constellation/mobile_terminal_block.txt` | 移动终端（自动切换） |
| deployment_scenario.txt | `blocks/leo_constellation/deployment_scenario.txt` | 部署位置 |
| network_definitions.txt | `blocks/leo_constellation/network_definitions.txt` | 网络定义 |
| README.md | `blocks/leo_constellation/README.md` | LEO 星座说明 |

---

## references/ — 命令参考手册

| 文件 | 路径 | AFSIM 类型 | 用途 |
|------|------|------------|------|
| reference_manual.txt | `references/reference_manual.txt` | 全部 | 完整 AFSIM 手册（2.7MB） |
| afsim_syntax.md | `references/afsim_syntax.md` | 语法 | AFSIM 2.9.0 语法参考 |
| wsf_radar_sensor.txt | `references/wsf_radar_sensor.txt` | WSF_RADAR_SENSOR | 雷达传感器命令 |
| wsf_air_mover.txt | `references/wsf_air_mover.txt` | WSF_AIR_MOVER | 空中 mover 命令 |
| wsf_ground_mover.txt | `references/wsf_ground_mover.txt` | WSF_GROUND_MOVER | 地面 mover 命令 |
| wsf_guided_mover.txt | `references/wsf_guided_mover.txt` | WSF_GUIDED_MOVER | 制导 mover 命令 |
| wsf_guidance_computer.txt | `references/wsf_guidance_computer.txt` | WSF_GUIDANCE_COMPUTER | 制导计算机命令 |
| wsf_launch_computer.txt | `references/wsf_launch_computer.txt` | WSF_BALLISTIC_MISSILE_LAUNCH_COMPUTER | 弹道导弹发射计算机命令 |
| wsf_explicit_weapon.txt | `references/wsf_explicit_weapon.txt` | WSF_EXPLICIT_WEAPON | 显式武器命令 |
| wsf_straight_line_mover.txt | `references/wsf_straight_line_mover.txt` | WSF_STRAIGHT_LINE_MOVER | 直线 mover 命令 |
| wsf_script_processor.txt | `references/wsf_script_processor.txt` | WSF_SCRIPT_PROCESSOR | 脚本处理器命令 |
| weapon_effects.txt | `references/weapon_effects.txt` | WSF_GRADUATED_LETHALITY | 武器效果命令 |
| sensor_types.txt | `references/sensor_types.txt` | 传感器 | AFSIM 传感器类型列表 |
| processor_types.txt | `references/processor_types.txt` | 处理器 | AFSIM 处理器类型列表 |
| mover_types.txt | `references/mover_types.txt` | Mover | AFSIM Mover 类型列表 |
| weapon_types.txt | `references/weapon_types.txt` | 武器 | AFSIM 武器类型列表 |
| extract_1742_1764_output.txt | `references/extract_1742_1764_output.txt` | 摘录 | 手册摘录 |

---

## scripts/ — 工具脚本

| 文件 | 路径 | 用途 | 用法 |
|------|------|------|------|
| lookup.py | `scripts/lookup.py` | 搜索手册 | `python scripts/lookup.py <keyword>` |
| index_manual.py | `scripts/index_manual.py` | 重建命令索引 | `python scripts/index_manual.py` |
| analyze_leo_comm.py | `scripts/analyze_leo_comm.py` | LEO 通信分析 | 6 张图 + CSV 输出 |
| extract_pages.py | `scripts/extract_pages.py` | PDF 页面提取 | `python scripts/extract_pages.py <pdf> <pages>` |
| parse_evt_full.py | `scripts/parse_evt_full.py` | EVT 事件文件解析 | `python scripts/parse_evt_full.py <file.evt>` |
| audit_mover.txt | `scripts/audit_mover.txt` | Mover 命令审计报告 | 参考文档 |
| audit_processor.txt | `scripts/audit_processor.txt` | 处理器命令审计报告 | 参考文档 |
| audit_sensor.txt | `scripts/audit_sensor.txt` | 传感器命令审计报告 | 参考文档 |

---

## templates/ — 可编译项目模板

| 文件 | 路径 | 用途 | 适用场景 |
|------|------|------|----------|
| main.txt | `templates/main.txt` | 主入口模板 | 新项目起点 |
| setup.txt | `templates/setup.txt` | 设置模板 | 平台类型定义 |
| event_output.txt | `templates/event_output.txt` | 事件输出模板 | 配置事件日志 |
| tank.txt | `templates/platforms/tank.txt` | 坦克平台 | 地面装甲目标 |
| fighter.txt | `templates/platforms/fighter.txt` | 战斗机平台 | 空中目标 |
| building.txt | `templates/platforms/building.txt` | 建筑平台 | 固定地面目标 |
| missile.txt | `templates/weapons/missile.txt` | 导弹武器 | 武器定义 |
| fire_control_radar.txt | `templates/sensors/fire_control_radar.txt` | 火控雷达 | 传感器定义 |
| aa_tactics.txt | `templates/processors/aa_tactics.txt` | 防空战术 | 防空交战逻辑 |
| missile_processor.txt | `templates/processors/missile_processor.txt` | 导弹处理器 | 导弹发射逻辑 |
| blue_laydown.txt | `templates/scenarios/blue_laydown.txt` | 蓝方布设 | 蓝方场景配置 |
| red_laydown.txt | `templates/scenarios/red_laydown.txt` | 红方布设 | 红方场景配置 |
| leo_constellation/ | `templates/leo_constellation/` | LEO 星座完整项目 | 卫星通信仿真 |

---

## 其他文件

| 文件 | 路径 | 用途 |
|------|------|------|
| SKILL.md | `SKILL.md` | 技能主文件（自动注入） |
| INDEX.md | `INDEX.md` | 本文件 |
| SYNTAX.md | `SYNTAX.md` | AFSIM 语法速查 |
| COMPREHENSIVE_SUMMARY.md | `COMPREHENSIVE_SUMMARY.md` | 详细功能总结 |
