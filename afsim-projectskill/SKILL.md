---
name: afsim-project
description: |
  AFSIM 2.9.0 仿真技能：创建、编译、调试、可视化和分析仿真场景。
  工作流：写 .txt → mission.exe 编译 → 修复错误 → mystic.exe 可视化 → Python 分析。
keywords: [AFSIM, mission, mystic, simulation, satellite, radar, missile, comms]
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["mission"], "anyBins": ["mystic"] },
        "homepage": "https://github.com/abydym/AstraLogic",
      },
  }
user-invocable: true
---

# AstraLogic AFSIM Skill

> **开发者：** 安徽大学 2023级网络工程 李乐怡 & 周钰炜
> **GitHub：** https://github.com/abydym/AstraLogic
> **引擎版本：** AFSIM 2.9.0

## 文件注入策略

- **仅本文件（SKILL.md）自动注入** — 控制 token 开销
- 其他文件（blocks/、references/、templates/、scripts/）均在磁盘上，通过 `read()` 按需加载
- **工作流程：** 先读 `INDEX.md` 查找所需文件，再用 `read()` 加载具体文件

## 环境配置

```powershell
# Windows
$env:AFSIM_HOME = "C:\AFSIM2.9\afsim-2.9.0"
# Linux/Mac
export AFSIM_HOME=/opt/afsim-2.9.0
# 验证
& "$env:AFSIM_HOME\bin\mission.exe" --version
# Python 依赖
pip install matplotlib numpy
```

## 工作流（4步）

```
Step 1: cd 项目目录 && mission.exe -es main.txt          # 编译
Step 2: 根据错误信息修复 → 重复 Step 1                    # 迭代
Step 3: mystic.exe output/*.aer                           # 3D 可视化
Step 4: python analyze.py --evt output/*.evt              # 分析画图
```

> ⚠️ `define_path_variable CASE name` 必须在 `event_output`/`csv_event_output`/`event_pipe` 之前。

## 关键规则

1. `platform_type <NAME> WSF_PLATFORM` — WSF_PLATFORM 关键字必须
2. 必须包含 mover：`WSF_GROUND_MOVER`、`WSF_AIR_MOVER`、`WSF_GUIDED_MOVER` 或 `WSF_STRAIGHT_LINE_MOVER`
3. 签名（radar/IR/optical）全局定义，然后在 platform_type 内按名引用
4. 结束时间用 `end_time <val> secs`，不是 `simulation_end_time`
5. 路由：`edit mover { route ... end_route } end_mover`
6. `CueToTarget()` 必须在 `Fire()` 之前
7. 场景文件中目标必须在射手之前包含（预置跟踪）
8. 传感器默认关闭；需设置 `on` 或调用 `sensor.TurnOn()`
9. 文件保存为 **无 BOM 的 UTF-8**（AFSIM 无法解析 UTF-8 BOM）
10. 卫星轨道必须闭合：路线航点需形成至少一个完整轨道（~15个航点）
11. 仿真时间需覆盖 ≥1 个完整轨道：LEO 520km 约 5693 秒，公式 `T = 2π × √((R+h)³/μ)`，μ = 3.986×10¹⁴
12. AFSIM 2.9 WSF_SCRIPT_PROCESSOR 限制：无 `on_init`、无 `substr()`、无 `atan2()`、无三元运算符、无数组 `{}` 初始化、无 `Latitude()`/`Longitude()` 方法

## 常见错误速查

| 错误 | 修复 |
|------|------|
| `Unknown command: <cmd>` | 查手册确认命令名 |
| `Bad value for: <cmd>` | 检查单位格式（m, km, sec, deg, kts, watt, dB） |
| `Unexpected End Of Data` | `end_` 标签不匹配，数一下块 |
| `Cannot open file: <path>` | setup.txt 中加 `file_path .` |
| `Unable to open event_output file` | 先创建 `output/` 目录 |
| `Target platform was not defined prior to track` | 蓝方文件放在红方之前 |
| `Bad value for position` | 用 `34.0n 118.0w altitude 0 m` 格式 |
| `aero type must be specified` | 加 `aero none` 或在制导 mover 中定义 aero |
| UTF-8 BOM 错误 | 用无 BOM 的 UTF-8 保存 |

## 查找命令（节省 token）

```python
# 在 reference_manual.txt 中查找（限 [-200:+1500] 字符）
# 或使用脚本：
# python scripts/lookup.py <keyword>
```

**规则：** 永远不要注入完整手册。按需查询，限制上下文。

## 文件目录

**完整索引见 `INDEX.md`。** 用 `read()` 加载后按需读取具体文件。

```
afsim-projectskill/
├── SKILL.md          ← 本文件（自动注入）
├── INDEX.md          ← 文件索引（先读这个）
├── SYNTAX.md         ← AFSIM 语法速查
├── blocks/           ← 可复用代码块（45+ 文件）
├── references/       ← 命令参考手册（17 文件）
├── scripts/          ← 工具脚本
├── templates/        ← 可编译项目模板
└── COMPREHENSIVE_SUMMARY.md ← 详细功能总结
```
