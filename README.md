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

**AstraLogic** is an Agent-based framework designed to automate and intelligently govern satellite communication simulations inside the **AFSIM** (Advanced Framework for Simulation, Integration, and Modeling) environment. It treats the AFSIM Warlock/Mystic engine as a high-fidelity **physics engine** and wraps it with Python to manage the full lifecycle of simulation campaigns — from scenario generation through execution to result analysis.

At its core, AstraLogic closes the loop between simulation and intelligence: a large-language-model (LLM) agent observes simulation outputs, reasons about the current state of the satellite constellation, and synthesises new WSL (Weapon Simulation Language) scripts that drive the next iteration — all without human intervention.

```
┌─────────────────────────────────────────────────────────────┐
│                         AstraLogic                          │
│                                                             │
│  ┌──────────┐    WSL scripts    ┌───────────────────────┐  │
│  │  LLM /   │ ─────────────────►│   AFSIM Warlock /     │  │
│  │  Agent   │                   │   Mystic Engine       │  │
│  │          │◄─────────────────  │   (Physics Layer)     │  │
│  └──────────┘   CSV / AER logs  └───────────────────────┘  │
│        │                                  │                 │
│        │   Perception-Decision-Action     │                 │
│        └──────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Architecture

AstraLogic implements a **Perception → Decision → Action** closed loop:

| Phase | Component | Description |
|-------|-----------|-------------|
| **Perception** | CSV / AER Parser | Python reads AFSIM's structured output files, extracts link-budget metrics, orbital states, and event logs |
| **Decision** | LLM Agent | The agent reasons over the parsed state and selects the next maneuver, frequency plan, or routing policy |
| **Action** | WSL Generator | Python renders updated Weapon Simulation Language scripts that encode the agent's decision for the next simulation run |

Each iteration tightens the feedback loop, progressively converging on optimal communication policies under realistic space-environment constraints.

---

## Key Features

- 🔁 **Batch Simulation Runner** — programmatically launch hundreds of Warlock/Mystic runs with varying parameters, collecting results automatically
- 📝 **Automated WSL Template Generation** — Jinja2-based templating engine that renders scenario scripts from high-level Python configuration objects
- 📡 **Satellite Link-Budget Analysis** — built-in utilities for Eb/N₀, EIRP, and rain-fade calculations against AFSIM's propagation model outputs
- 🤖 **LLM-Ready Interfaces** — clean tool-use APIs compatible with OpenAI function calling, LangChain, and custom agent frameworks
- 📊 **Result Aggregation & Visualisation** — automatic ingestion of `.csv` result files into pandas DataFrames with optional Matplotlib/Plotly dashboards
- 🔧 **Zero-boilerplate Scenario Setup** — point to your local AFSIM installation and run a scenario in under ten lines of Python

---

## Quick Start

### Prerequisites

- Python ≥ 3.8
- A local AFSIM installation (Warlock or Mystic engine)
- An OpenAI-compatible API key (optional — only required for LLM agent features)

### Installation

```bash
git clone https://github.com/abydym/AstraLogic.git
cd AstraLogic
pip install -r requirements.txt
```

### Running Your First Scenario

```python
from astralogic import SimulationRunner, AgentController

# 1. Point AstraLogic at the local AFSIM Warlock executable
runner = SimulationRunner(
    afsim_exe_path="/opt/afsim/bin/warlock",   # ← set to your local path
    scenario_template="templates/leo_comms.wsl",
    output_dir="results/",
)

# 2. Execute a single scenario and collect outputs
result = runner.run(params={"altitude_km": 550, "inclination_deg": 53.0})
print(result.link_budget_summary())

# 3. Attach an LLM agent for closed-loop iteration
controller = AgentController(runner=runner, model="gpt-4o")
controller.optimize(objective="maximize_throughput", max_iterations=20)
```

### Environment Variables

Create a `.env` file (excluded from version control) with:

```dotenv
AFSIM_EXE_PATH=/opt/afsim/bin/warlock
OPENAI_API_KEY=sk-...
```

---

## Project Structure

```
AstraLogic/
├── astralogic/
│   ├── runner.py          # Batch simulation runner
│   ├── wsl_generator.py   # WSL script templating
│   ├── parser.py          # CSV / AER output parser
│   ├── link_budget.py     # Link-budget calculations
│   └── agent/
│       ├── controller.py  # LLM agent controller
│       └── tools.py       # Agent tool-use definitions
├── templates/             # WSL scenario templates
├── results/               # Simulation output (git-ignored)
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

---

## Roadmap

| Milestone | Status | Description |
|-----------|--------|-------------|
| Core simulation runner | 🔨 In progress | Batch Warlock/Mystic execution with result collection |
| WSL template engine | 🔨 In progress | Jinja2-based scenario generation |
| LLM agent integration | 📅 Planned | OpenAI / LangChain agent loop |
| MARL constellation routing | 📅 Planned | Multi-Agent Reinforcement Learning for dynamic routing across large LEO constellations |
| 6G NTN support | 📅 Planned | Non-Terrestrial Network (NTN) channel models aligned with 3GPP Release 17/18 |
| GUI dashboard | 📅 Planned | Real-time visualisation of orbital states and link budgets |

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

**AstraLogic** 是一个基于智能体（Agent）的框架，旨在自动化和智能化地管理 **AFSIM**（高级仿真、集成与建模框架）环境中的卫星通信仿真。该框架将 AFSIM Warlock/Mystic 引擎视为高保真**物理引擎**，通过 Python 封装层全面管理仿真活动的生命周期——从场景生成、批量执行到结果分析。

AstraLogic 的核心在于打通"仿真"与"智能"之间的闭环：大语言模型（LLM）智能体实时观测仿真输出，对卫星星座的当前状态进行推理，并自动合成新的 WSL（武器仿真语言）脚本驱动下一轮迭代，全程无需人工干预。

---

## 核心架构

AstraLogic 实现了 **感知 → 决策 → 行动** 的闭合循环：

| 阶段 | 组件 | 描述 |
|------|------|------|
| **感知** | CSV / AER 解析器 | Python 读取 AFSIM 结构化输出文件，提取链路预算指标、轨道状态及事件日志 |
| **决策** | LLM 智能体 | 智能体基于解析状态进行推理，选择下一步机动方案、频率规划或路由策略 |
| **行动** | WSL 生成器 | Python 将智能体决策渲染为 WSL 脚本，驱动下一次仿真运行 |

每次迭代都进一步收紧反馈回路，在真实空间环境约束下逐步收敛至最优通信策略。

---

## 主要特性

- 🔁 **批量仿真运行器** — 以编程方式启动数百次参数变化的 Warlock/Mystic 仿真，并自动收集结果
- 📝 **WSL 模板自动生成** — 基于 Jinja2 的模板引擎，将高层 Python 配置对象渲染为场景脚本
- 📡 **卫星链路预算分析** — 内置 Eb/N₀、EIRP 及雨衰计算工具，对接 AFSIM 传播模型输出
- 🤖 **LLM 就绪接口** — 兼容 OpenAI 函数调用、LangChain 及自定义智能体框架的简洁工具调用 API
- 📊 **结果聚合与可视化** — 自动将 `.csv` 结果文件导入 pandas DataFrame，支持 Matplotlib/Plotly 可视化
- 🔧 **零样板场景配置** — 只需指定本地 AFSIM 安装路径，十行 Python 即可运行场景

---

## 快速开始

### 环境要求

- Python ≥ 3.8
- 本地 AFSIM 安装（Warlock 或 Mystic 引擎）
- OpenAI 兼容 API 密钥（可选，仅 LLM 智能体功能需要）

### 安装

```bash
git clone https://github.com/abydym/AstraLogic.git
cd AstraLogic
pip install -r requirements.txt
```

### 运行第一个场景

```python
from astralogic import SimulationRunner, AgentController

# 1. 指定本地 AFSIM Warlock 可执行文件路径
runner = SimulationRunner(
    afsim_exe_path="/opt/afsim/bin/warlock",   # ← 修改为你的本地路径
    scenario_template="templates/leo_comms.wsl",
    output_dir="results/",
)

# 2. 执行单次场景并收集输出
result = runner.run(params={"altitude_km": 550, "inclination_deg": 53.0})
print(result.link_budget_summary())

# 3. 接入 LLM 智能体进行闭环迭代优化
controller = AgentController(runner=runner, model="gpt-4o")
controller.optimize(objective="maximize_throughput", max_iterations=20)
```

### 环境变量配置

创建 `.env` 文件（已加入 `.gitignore`，不会提交到版本库）：

```dotenv
AFSIM_EXE_PATH=/opt/afsim/bin/warlock
OPENAI_API_KEY=sk-...
```

---

## 项目结构

```
AstraLogic/
├── astralogic/
│   ├── runner.py          # 批量仿真运行器
│   ├── wsl_generator.py   # WSL 脚本模板引擎
│   ├── parser.py          # CSV / AER 输出解析器
│   ├── link_budget.py     # 链路预算计算工具
│   └── agent/
│       ├── controller.py  # LLM 智能体控制器
│       └── tools.py       # 智能体工具调用定义
├── templates/             # WSL 场景模板
├── results/               # 仿真输出（已加入 git-ignore）
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

---

## 路线图

| 里程碑 | 状态 | 描述 |
|--------|------|------|
| 核心仿真运行器 | 🔨 进行中 | Warlock/Mystic 批量执行与结果收集 |
| WSL 模板引擎 | 🔨 进行中 | 基于 Jinja2 的场景生成 |
| LLM 智能体集成 | 📅 计划中 | OpenAI / LangChain 智能体闭环 |
| MARL 星座路由 | 📅 计划中 | 多智能体强化学习（MARL），面向大规模 LEO 星座动态路由优化 |
| 6G NTN 支持 | 📅 计划中 | 符合 3GPP Release 17/18 的非地面网络（NTN）信道模型 |
| GUI 仪表盘 | 📅 计划中 | 轨道状态与链路预算的实时可视化界面 |

---

## 贡献指南

欢迎提交 Pull Request。对于重大变更，请先提交 Issue 进行讨论。请确保同步更新相关测试。

---

## 许可证

本项目采用 [MIT 许可证](LICENSE)，详见 LICENSE 文件。
