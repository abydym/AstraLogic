<div align="center">

# 🛰️ AstraLogic

**Agent-Driven Satellite Communication Simulation Framework**

*An intelligent bridge between high-fidelity physics simulation and cognitive decision-making agents*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![AFSIM](https://img.shields.io/badge/engine-AFSIM%20Warlock-orange.svg)]()

[English](#english) | [中文](#chinese)

</div>

---

<a name="english"></a>

## Overview

**AstraLogic** is a one-stop satellite communication simulation & decision platform that seamlessly integrates AFSIM (Advanced Framework for Simulation, Integration, and Modeling) execution with intelligent agent-driven analysis within a single web interface.

Users interact with the system entirely through a web dashboard — submitting simulation requests via an Agent chat interface, which delegates decision-making to **OpenClaw** (an intelligent agent framework). OpenClaw reasons about orbital mechanics, link budgets, and communication strategies, then orchestrates AFSIM simulations via **Skills** and **MCP servers**. Results are automatically parsed and visualized in the dashboard without ever needing to leave the browser.

The architecture consists of:

1. **Frontend** — Streamlit dashboard with Agent chat interface for end-to-end simulation control
2. **Backend** — FastAPI server coordinating agent decisions and simulation state
3. **Decision Engine** — OpenClaw agent with custom Skills for link analysis and frequency optimization
4. **Simulation Bridge** — MCP server protocol for headless AFSIM execution and result ingestion
5. **Data Layer** — AER parser converting AFSIM binary outputs to structured DataFrames

```
┌────────────────────────────────────────────────────────────────┐
│                  AstraLogic One-Stop Platform                  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │    Streamlit Dashboard with Agent Chat Interface        │  │
│  │    "Plan a LEO-to-ground link with backup path"        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                               ↓                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  FastAPI Backend ← → OpenClaw Agent Decision Engine    │  │
│  │  (Request routing, state management, result caching)    │  │
│  └─────────────────────────────────────────────────────────┘  │
│        ↓                                           ↑            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  OpenClaw Skills & MCP Servers                          │  │
│  │  • LinkBudgetSkill — analyze propagation & margins      │  │
│  │  • FrequencyOptimizerSkill — select frequencies         │  │
│  │  • AFSIMExecutor MCP — launch Warlock/Mystic headless  │  │
│  └─────────────────────────────────────────────────────────┘  │
│        ↓                                                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  AFSIM Simulation (Warlock/Mystic)                      │  │
│  │  Binary AER Output → pymystic Parser → CSV Results      │  │
│  └─────────────────────────────────────────────────────────┘  │
│        ↓                                                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Dashboard Result Visualization                          │  │
│  │  Orbital plots, link metrics, performance summary        │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## Core Architecture

AstraLogic implements an **Agent-Driven Simulation Pipeline**:

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Dashboard** | Streamlit | User interface with Agent chat box for natural language requests |
| **Backend Coordinator** | FastAPI | Routes agent decisions, manages simulation state, caches results |
| **Decision Engine** | OpenClaw Agent | Reasons about orbital mechanics, link budgets, and resource optimization |
| **Skill System** | Custom Skills | LinkBudgetAnalyzer, FrequencyOptimizer, ManeuverPlanner |
| **Simulation Bridge** | MCP (Model Context Protocol) | Headless AFSIM execution, parameter templating, result collection |
| **Data Parser** | pymystic + pandas | Binary AER → structured CSV for visualization |

### Workflow: End-to-End Simulation

```
User: "Plan a backup link for Sat-A when it loses contact with GS-1"
        ↓ (natural language → parsed request)
OpenClaw Agent receives context:
  • Current orbital state (from last simulation)
  • Available frequency bands
  • Ground station locations
  • Link margin thresholds
        ↓ (reasoning loop)
OpenClaw invokes Skills:
  1. LinkBudgetSkill.analyze() → SNR for candidate frequencies
  2. FrequencyOptimizer.select_channels() → optimal band selection
  3. ManeuverPlanner.compute_handover() → timing & power levels
        ↓ (decision ready)
AFSIMExecutor.run() via MCP:
  • Template WSL with agent-selected parameters
  • Launch Warlock/Mystic headless
  • Stream binary AER output
  • Parse results in real-time
        ↓ (results ready)
Dashboard auto-updates with:
  • Orbital trajectory plots
  • Link margin time-series
  • Success/failure metrics
  • Agent reasoning summary
```

---

## Key Features

### ✅ Active Development

- 🤖 **Agent Chat Interface** — Natural language simulation requests directly in the dashboard
- 🧠 **OpenClaw Decision Engine** — Intelligent agent for link planning, frequency optimization, and maneuver scheduling
- 🎯 **Skill-based Architecture** — Extensible Skills for link-budget analysis, frequency selection, orbital mechanics
- 🔌 **MCP Server Integration** — Headless AFSIM execution orchestrated via Model Context Protocol
- 🔍 **Real-time AER Parser** — Binary simulation output ingestion with live CSV export
- 📊 **Dashboard Visualization** — Plotly-based orbital plots, link metrics, and performance dashboards
- ⚡ **FastAPI Backend** — REST API for state queries, result caching, and agent coordination
- 🔄 **Automated Workflows** — Complete simulation from request to result without leaving the browser

### 📅 Future Enhancements

- Advanced link-budget calculations (rain fade, fading margins)
- Multi-scenario comparison & optimization loop
- AFSIM direct launch button for advanced users
- Expanded orbital mechanics solvers (perturbations, collision avoidance)

---

## Quick Start

### Prerequisites

- Python ≥ 3.8
- AFSIM Warlock or Mystic installation (local or remote)
- OpenClaw configuration (provided in setup)

### Installation

```bash
git clone https://github.com/abydym/AstraLogic.git
cd AstraLogic
pip install -r requirements.txt
```

### Running the Platform

```bash
# Terminal 1: Start the backend API
python backend.py
# API available at http://localhost:8000/docs

# Terminal 2: Launch the dashboard
streamlit run app.py
# Dashboard opens at http://localhost:8501
```

### Using the Agent Chat Interface

Once the dashboard is live, use the **Agent Chat Box** to request simulations:

**Example 1: Simple link analysis**
```
User: "Analyze the communication link between Sat-A and Ground Station-1 
       when Sat-A passes over the ground station at 14:30 UTC."

OpenClaw will:
  1. Retrieve orbital ephemerides
  2. Compute elevation angle and slant range
  3. Run LinkBudgetSkill to determine SNR margins
  4. Launch AFSIM simulation via MCP
  5. Display results in dashboard
```

**Example 2: Frequency optimization**
```
User: "Find the best frequency band for Sat-B to GS-2 link 
       with at least 6 dB margin and no interference."

OpenClaw will:
  1. Analyze available frequency allocations
  2. Check interference environment
  3. Invoke FrequencyOptimizerSkill
  4. Simulate multiple candidates in parallel
  5. Recommend optimal band with reasoning
```

### Custom Simulation (Advanced)

For direct control, you can also invoke simulations programmatically:

```python
from aermsg2dataframe import parse_aer_messages
import pymystic
import pandas as pd

# Read existing AFSIM output
with pymystic.Reader('scenarios/demo_output.aer') as reader:
    messages = list(reader)

# Parse to DataFrames
df_entity, df_orbital = parse_aer_messages(messages)

# Analyze
print(f"Simulation duration: {df_entity['simTime'].max()} seconds")
print(f"Tracked platforms: {sorted(df_entity['platformIndex'].unique())}")

# Compute inter-satellite distance
sat1 = df_entity[df_entity['platformIndex'] == 1]
sat2 = df_entity[df_entity['platformIndex'] == 2]
if len(sat1) > 0 and len(sat2) > 0:
    distances = ((sat1[['x','y','z']].reset_index(drop=True) - 
                  sat2[['x','y','z']].reset_index(drop=True))**2).sum(axis=1)**0.5 / 1000
    print(f"Min distance: {distances.min():.1f} km, Max: {distances.max():.1f} km")
```

---

## Project Structure

```
AstraLogic/
├── app.py                      # 🎨 Streamlit dashboard (main UI)
├── backend.py                  # ⚡ FastAPI server
├── aer_read.py                 # 📡 AER binary parser (pymystic wrapper)
├── aermsg2dataframe.py         # 📊 Message → DataFrame converter
├── openclaw_agent.py           # 🤖 LLM agent (planned)
├── afsim_mcp_server.py         # 🔌 MCP server bridge (planned)
├── pymystic.py                 # 📦 Local pymystic library
│
├── core/                       # Core utility modules
│   ├── __init__.py
│   └── afsim_bridge.py         # AFSIM integration helpers
│
├── scenarios/                  # AFSIM scenario files
│   ├── demo_2sat_1gs.txt       # 2 satellites + 1 ground station
│   ├── demo_output.aer         # Sample AFSIM output (binary)
│   ├── demo_output.csv         # Converted CSV (for reference)
│   └── demo_output.evt         # Event log
│
├── output/                     # Generated data files
│   ├── entity.csv              # Parsed platform states
│   └── orbital.csv             # Parsed orbital elements
│
├── docs/                       # Documentation
├── brand-design-md-main/       # Design system assets
├── README.md                   # This file
├── DESIGN.md                   # Architecture & design notes
├── requirements.txt            # Dependencies
├── LICENSE                     # MIT License
└── .env.example                # Environment template (unused for now)
```

---

## Roadmap

| Milestone | Status | Target | Description |
|-----------|--------|--------|-------------|
| ✅ AER Parser | Complete | v0.1 | AFSIM binary deserialization (pymystic) |
| ✅ Dashboard Core | Complete | v0.1 | Streamlit UI with orbital visualization |
| ✅ FastAPI Backend | Complete | v0.1 | REST API for state management |
| 🔨 Agent Chat Interface | In Progress | v0.2 | OpenClaw integration with natural language processing |
| 🔨 LinkBudgetSkill | In Progress | v0.2 | Eb/N₀, EIRP, interference analysis |
| 🔨 MCP Server Bridge | In Progress | v0.2 | Headless AFSIM execution & result streaming |
| 📅 FrequencyOptimizerSkill | Planned | v0.3 | Automated frequency band selection |
| 📅 Multi-scenario Optimization | Planned | v0.3 | Parallel simulation & comparative analysis |
| 📅 Advanced Orbital Mechanics | Planned | v0.4 | Perturbations, collision avoidance, station-keeping |
| 📅 Result Export & Reporting | Planned | v0.4 | PDF reports, data archiving, batch export |

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. Please make sure to update tests as appropriate.

---

## License

This project is licensed under the [MIT License](LICENSE) — see the LICENSE file for details.

---

---

<a name="chinese"></a>

## 概述

**AstraLogic** 是一个一站式卫星通信仿真决策平台，在单一网页界面中实现了 AFSIM（高级仿真、集成与建模框架）与智能决策引擎的无缝融合。

用户完全通过网页仪表盘进行交互——在 Agent 对话框中提交仿真需求，由 **OpenClaw** 智能体负责决策。OpenClaw 可以推理轨道力学、链路预算和通信策略，通过 **Skills** 和 **MCP 服务器**协调 AFSIM 的无头执行。仿真完成后，结果自动解析并在仪表盘中可视化展示，用户无需离开浏览器。

系统架构包括：

1. **前端界面** — Streamlit 仪表盘，集成 Agent 对话框用于端到端仿真控制
2. **后端协调** — FastAPI 服务器，负责路由 Agent 决策和管理仿真状态
3. **决策引擎** — OpenClaw 智能体，推理轨道和通信优化
4. **技能系统** — 自定义 Skills 用于链路分析和频率优化
5. **仿真网桥** — MCP 协议支持无头 AFSIM 执行和结果导入
6. **数据层** — AER 解析器将 AFSIM 二进制输出转换为结构化 DataFrame

```
┌────────────────────────────────────────────────────────────────┐
│                  AstraLogic 一站式仿真平台                     │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │    Streamlit 仪表盘（含 Agent 对话框）                 │  │
│  │    "规划卫星A在失去地面站信号时的备用链路"            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                               ↓                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  FastAPI 后端 ← → OpenClaw Agent 决策引擎             │  │
│  │  （请求路由、状态管理、结果缓存）                     │  │
│  └─────────────────────────────────────────────────────────┘  │
│        ↓                                           ↑            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  OpenClaw Skills 与 MCP 服务器                         │  │
│  │  • LinkBudgetSkill — 分析传播与链路余量               │  │
│  │  • FrequencyOptimizerSkill — 频率选择                 │  │
│  │  • AFSIMExecutor MCP — 无头启动 Warlock/Mystic       │  │
│  └─────────────────────────────────────────────────────────┘  │
│        ↓                                                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  AFSIM 仿真（Warlock/Mystic）                         │  │
│  │  二进制 AER 输出 → pymystic 解析 → CSV 结果           │  │
│  └─────────────────────────────────────────────────────────┘  │
│        ↓                                                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  仪表盘结果展示                                        │  │
│  │  轨道图、链路指标、性能总结                           │  │
│  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```
---

## 核心架构

AstraLogic 实现了**智能体驱动的仿真管道**：

| 组件 | 技术栈 | 职责 |
|------|--------|------|
| **网页仪表盘** | Streamlit | 用户界面与 Agent 对话框，用于自然语言仿真请求 |
| **后端协调** | FastAPI | 路由 Agent 决策、管理仿真状态、缓存结果 |
| **决策引擎** | OpenClaw Agent | 推理轨道力学、链路预算和资源优化 |
| **技能系统** | 自定义 Skills | LinkBudgetAnalyzer、FrequencyOptimizer、ManeuverPlanner |
| **仿真网桥** | MCP 协议 | 无头 AFSIM 执行、参数模板、结果收集 |
| **数据解析** | pymystic + pandas | 二进制 AER → 结构化 CSV 用于可视化 |

### 工作流：端到端仿真

```
用户：「规划备用链路，当卫星A与地面站失联时」
        ↓ （自然语言 → 解析请求）
OpenClaw Agent 接收上下文：
  • 当前轨道状态（来自上次仿真）
  • 可用频段
  • 地面站位置
  • 链路余量阈值
        ↓ （推理循环）
OpenClaw 调用 Skills：
  1. LinkBudgetSkill.analyze() → 候选频率的信噪比
  2. FrequencyOptimizer.select_channels() → 最优频段选择
  3. ManeuverPlanner.compute_handover() → 时序与功率参数
        ↓ （决策就绪）
通过 MCP 执行 AFSIMExecutor：
  • 用 Agent 选定的参数模板化 WSL
  • 无头启动 Warlock/Mystic
  • 实时流式处理二进制 AER 输出
  • 在线解析结果
        ↓ （结果就绪）
仪表盘自动更新：
  • 轨道轨迹图
  • 链路余量时间序列
  • 成功/失败指标
  • Agent 推理摘要
```

---

## 主要特性

### ✅ 实际开发中

- 🤖 **Agent 对话框** — 在仪表盘中用自然语言提交仿真需求
- 🧠 **OpenClaw 决策引擎** — 智能体用于链路规划、频率优化和机动调度
- 🎯 **基于 Skill 的架构** — 可扩展的 Skills 用于链路分析、频率选择、轨道力学
- 🔌 **MCP 服务器集成** — 通过 Model Context Protocol 协调无头 AFSIM 执行
- 🔍 **实时 AER 解析器** — 二进制仿真输出摄取与实时 CSV 导出
- 📊 **仪表盘可视化** — 基于 Plotly 的轨道图、链路指标和性能仪表盘
- ⚡ **FastAPI 后端** — REST API 用于状态查询、结果缓存和 Agent 协调
- 🔄 **自动化工作流** — 从请求到结果的完整仿真，无需离开浏览器

### 📅 后续扩展

- 高级链路预算计算（雨衰、衰减余量）
- 多场景对比与优化循环
- AFSIM 直接启动按钮（供高级用户使用）
- 扩展轨道力学求解器（扰动项、碰撞规避）

---

## 快速开始

### 环境要求

- Python ≥ 3.8
- AFSIM Warlock 或 Mystic 安装（本地或远程）
- OpenClaw 配置（安装包中提供）

### 安装

```bash
git clone https://github.com/abydym/AstraLogic.git
cd AstraLogic
pip install -r requirements.txt
```

### 启动平台

```bash
# 终端 1：启动后端 API
python backend.py
# API 文档：http://localhost:8000/docs

# 终端 2：启动仪表盘
streamlit run app.py
# 仪表盘：http://localhost:8501
```

### 使用 Agent 对话框

仪表盘启动后，使用 **Agent 对话框**提交仿真请求：

**示例 1：简单链路分析**
```
用户：「分析卫星A与地面站-1 在UTC 14:30 通过地面站上空时的通信链路」

OpenClaw 将：
  1. 检索轨道星历
  2. 计算仰角和斜距
  3. 运行 LinkBudgetSkill 确定信噪比余量
  4. 通过 MCP 启动 AFSIM 仿真
  5. 在仪表盘中展示结果
```

**示例 2：频率优化**
```
用户：「为卫星B到地面站-2 的链路找到最优频段，至少6 dB余量且无干扰」

OpenClaw 将：
  1. 分析可用频段分配
  2. 检查干扰环境
  3. 调用 FrequencyOptimizerSkill
  4. 并行仿真多个候选频段
  5. 推荐最优频段并说明理由
```

### 自定义仿真（高级用户）

若需要直接控制，也可以编程方式调用仿真：

```python
from aermsg2dataframe import parse_aer_messages
import pymystic
import pandas as pd

# 读取现有 AFSIM 输出
with pymystic.Reader('scenarios/demo_output.aer') as reader:
    messages = list(reader)

# 解析为 DataFrame
df_entity, df_orbital = parse_aer_messages(messages)

# 分析
print(f"仿真时长：{df_entity['simTime'].max()} 秒")
print(f"追踪平台：{sorted(df_entity['platformIndex'].unique())}")

# 计算星间距离
sat1 = df_entity[df_entity['platformIndex'] == 1]
sat2 = df_entity[df_entity['platformIndex'] == 2]
if len(sat1) > 0 and len(sat2) > 0:
    distances = ((sat1[['x','y','z']].reset_index(drop=True) - 
                  sat2[['x','y','z']].reset_index(drop=True))**2).sum(axis=1)**0.5 / 1000
    print(f"最小距离：{distances.min():.1f} km，最大距离：{distances.max():.1f} km")
```

---

## 项目结构

```
AstraLogic/
├── app.py                      # 🎨 Streamlit 仪表盘（主界面）
├── backend.py                  # ⚡ FastAPI 服务器
├── aer_read.py                 # 📡 AER 二进制解析器（pymystic 封装）
├── aermsg2dataframe.py         # 📊 消息 → DataFrame 转换器
├── openclaw_agent.py           # 🤖 LLM 智能体（筹划中）
├── afsim_mcp_server.py         # 🔌 MCP 服务器网桥（筹划中）
├── pymystic.py                 # 📦 本地 pymystic 库
│
├── core/                       # 核心实用模块
│   ├── __init__.py
│   └── afsim_bridge.py         # AFSIM 集成助手
│
├── scenarios/                  # AFSIM 场景文件
│   ├── demo_2sat_1gs.txt       # 2 颗卫星 + 1 个地面站
│   ├── demo_output.aer         # 示例 AFSIM 输出（二进制）
│   ├── demo_output.csv         # 转换后的 CSV（参考）
│   └── demo_output.evt         # 事件日志
│
├── output/                     # 生成的数据文件
│   ├── entity.csv              # 解析后的平台状态
│   └── orbital.csv             # 解析后的轨道要素
│
├── docs/                       # 文档
├── brand-design-md-main/       # 设计系统资源
├── README.md                   # 本文件
├── DESIGN.md                   # 架构与设计笔记
├── requirements.txt            # 依赖清单
├── LICENSE                     # MIT 许可证
└── .env.example                # 环境变量模板（暂未使用）
```

---

## 路线图

| 里程碑 | 状态 | 目标版本 | 描述 |
|--------|------|--------|------|
| ✅ AER 解析器 | 已完成 | v0.1 | AFSIM 二进制反序列化（pymystic） |
| ✅ 仪表盘核心 | 已完成 | v0.1 | Streamlit UI 与轨道可视化 |
| ✅ FastAPI 后端 | 已完成 | v0.1 | 状态管理 REST API |
| 🔨 Agent 对话框 | 进行中 | v0.2 | OpenClaw 集成与自然语言处理 |
| 🔨 LinkBudgetSkill | 进行中 | v0.2 | Eb/N₀、EIRP、干扰分析 |
| 🔨 MCP 服务器网桥 | 进行中 | v0.2 | 无头 AFSIM 执行与结果流式处理 |
| 📅 FrequencyOptimizerSkill | 筹划中 | v0.3 | 自动频段选择 |
| 📅 多场景优化 | 筹划中 | v0.3 | 并行仿真与对比分析 |
| 📅 高级轨道力学 | 筹划中 | v0.4 | 扰动项、碰撞规避、台站保持 |
| 📅 结果导出与报告 | 筹划中 | v0.4 | PDF 报告、数据存档、批量导出 |

---

## 贡献指南

欢迎提交 Pull Request。对于重大变更，请先提交 Issue 进行讨论。请确保同步更新相关测试。

---

## 许可证

本项目采用 [MIT 许可证](LICENSE)，详见 LICENSE 文件。
