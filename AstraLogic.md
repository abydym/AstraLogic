# AstraLogic — Agent驱动的卫星通信仿真平台

## 课程设计报告

---

# 第1章 课题背景

## 1.1 概述

卫星通信系统是现代航天工程的核心基础设施，承担着全球通信、导航定位、遥感探测等关键任务。随着低轨（LEO）卫星星座的大规模部署，卫星通信网络的复杂度呈指数级增长，对系统设计与性能评估提出了前所未有的挑战。在此背景下，高保真、可扩展的仿真平台成为卫星通信系统研发流程中不可或缺的工具。

传统的军用仿真框架，如AFSIM（Advanced Framework for Simulation, Integration, and Modeling），虽然在建模精度和功能完备性方面表现优异，但其学习曲线陡峭，使用者需要掌握专用脚本语言、理解复杂的配置文件结构，并手动编排仿真流程。这一门槛将大量领域专家和初级工程师挡在了高效仿真的门外，严重制约了仿真技术在工程实践中的普及应用。

近年来，以大语言模型（LLM）为核心的AI Agent技术取得了突破性进展。智能体（Agent）具备自然语言理解、任务规划和工具调用等能力，能够将用户的高层意图自动分解为可执行的操作序列。将AI Agent引入仿真领域，有望从根本上改变人机交互模式——用户只需用自然语言描述仿真需求，Agent即可自动完成场景配置、仿真执行和结果分析的全流程操作。

基于上述背景，本项目提出了 **AstraLogic**（Astro + Logic）——一个Agent驱动的卫星通信仿真平台。AstraLogic旨在将AFSIM的强大仿真能力、OpenClaw智能体的自然语言交互能力以及Streamlit的可视化能力进行深度整合，构建"一站式"的卫星通信仿真与决策支持系统。用户无需编写任何脚本，只需通过对话即可完成从仿真场景构建到结果分析的完整工作流，显著降低卫星通信仿真的使用门槛。

## 1.2 实验环境

本项目的开发与运行环境如下表所示：

| 类别 | 配置 |
|------|------|
| 操作系统 | Windows 10 / Windows 11 |
| Python 版本 | 3.8 及以上 |
| Python 依赖 | streamlit、pandas、numpy、plotly、matplotlib |
| 仿真框架 | AFSIM 2.9.0（含 mission.exe、mystic.exe、wizard.exe） |
| 智能体框架 | OpenClaw CLI |
| 硬件要求 | 普通PC即可（推荐8GB以上内存） |

其中，AFSIM 2.9.0 是美国空军研究实验室（AFRL）开发的开源仿真框架，提供了任务级仿真（mission.exe）、3D可视化（mystic.exe）和场景编辑（wizard.exe）等核心工具。OpenClaw CLI 作为智能体运行时，负责解析用户意图并调度仿真技能。Python 生态中的 Streamlit 提供了快速构建 Web 仪表盘的能力，而 Plotly 和 Matplotlib 则分别承担交互式3D可视化和静态图表生成的任务。

---

# 第2章 实践任务

本课程设计的核心实践任务围绕 AstraLogic 平台的构建展开，具体包括以下五个方面：

**（1）构建 AFSIM 仿真技能（Skill）。** 设计并实现一套标准化的 AFSIM 仿真技能，封装 AFSIM 场景脚本的自动编译、执行和输出解析流程。该技能以 OpenClaw Skill 规范进行组织，包含语法参考文档、可复用的分析脚本和场景模板，使 Agent 能够通过技能调度自动完成仿真任务。

**（2）开发 Streamlit 前端仪表盘。** 构建一个功能完备的 Web 前端界面，集成 Agent 对话、3D 轨道可视化、链路分析图表和数据表格等多个功能模块。采用 Apple 风格的 UI 设计语言，提供简洁美观的交互体验。

**（3）集成 OpenClaw Agent，实现自然语言驱动仿真。** 将 OpenClaw 智能体框架与前端和仿真后端进行集成，使得用户能够通过自然语言对话的方式驱动整个仿真流程，实现从意图理解到结果呈现的端到端自动化。

**（4）实现 AER/EVT 数据解析与可视化。** 开发针对 AFSIM 输出格式（AER 二进制文件和 EVT 事件文件）的解析工具，将仿真输出数据转换为结构化的 Python 数据对象和 CSV 文件，并通过图表进行直观展示。

**（5）端到端验证。** 完成从用户输入到结果展示的完整链路验证：用户在聊天框输入仿真需求 → Agent 分析意图并调度 Skill → AFSIM 执行仿真 → 输出文件解析 → 可视化结果在前端呈现。

---

# 第3章 团队分工

本项目由4人团队协作完成，各成员的职责分工如下表所示：

| 成员 | 角色 | 主要职责 |
|------|------|----------|
| 成员A | 项目负责人 | 架构设计、项目管理、OpenClaw Agent 集成开发、系统联调 |
| 成员B | 仿真工程师 | AFSIM 仿真技能开发、分析脚本编写（analyze_leo_comm.py、parse_evt_full.py）、场景脚本维护 |
| 成员C | 前端工程师 | Streamlit 前端开发、3D 轨道可视化实现、UI/UX 设计、Apple 风格主题定制 |
| 成员D | 数据工程师 | 数据解析层开发（pymystic.py 集成）、AER/EVT 文件解析、测试验证与质量保证 |

在协作模式上，项目采用敏捷开发方式，以两周为一个迭代周期。成员A负责整体架构的把控和接口定义，成员B和成员C分别从后端仿真和前端展示两个方向并行推进，成员D负责数据层的桥梁作用和最终的集成测试。各成员通过 Git 进行版本管理，定期进行代码评审和集成测试，确保各模块之间的接口一致性。

---

# 第4章 总体流程与架构

## 4.1 项目架构

AstraLogic 采用经典的三层架构设计，自上而下分别为：前端展示层、智能体服务层、仿真执行与数据解析层。各层之间通过明确定义的接口进行通信，实现了关注点分离和模块解耦。

![项目架构图](images/architecture.png)

### 4.1.1 前端展示层（Streamlit）

前端展示层基于 Streamlit 框架构建，负责提供用户交互界面和数据可视化能力。其核心实现文件为 `appnew.py`。

**页面布局：** 采用侧边栏（Sidebar）+ 主区域的经典布局模式。侧边栏放置仿真参数配置、场景选择等控制面板；主区域通过 `st.tabs()` 组件划分为多个功能标签页，包括：

- **Agent 对话**：聊天界面，用户输入自然语言需求，展示 Agent 的推理过程和执行结果
- **3D 轨道可视化**：基于 Plotly 的交互式三维轨道展示，支持旋转、缩放等操作
- **链路分析图表**：展示卫星-地面站链路的信噪比、误码率等关键指标随时间的变化
- **数据表格**：以 DataFrame 形式展示仿真原始数据，支持排序和筛选

**UI 设计风格：** 采用 Apple 设计语言，使用 SF Pro 字体系列，卡片采用圆角设计（border-radius: 12px），主色调为蓝色（#007AFF），整体呈现简洁、专业的视觉效果。

**Agent 对话集成：** 前端通过 Python 的 `subprocess` 模块调用 OpenClaw CLI 命令，实现与智能体的通信。核心代码示例如下：

```python
import subprocess, json, sys

def ask_openclaw(message, session_id):
    """通过 openclaw CLI 发送消息给 agent，返回文字回复"""
    cmd = "openclaw.cmd" if sys.platform == "win32" else "openclaw"
    result = subprocess.run(
        [cmd, "agent", "--session-id", session_id, "--message", message, "--json"],
        capture_output=True, timeout=120,
    )
    data = json.loads(result.stdout.decode("utf-8"))
    payloads = data.get("result", {}).get("payloads", [])
    return payloads[0].get("text", "(no text)") if payloads else "(empty response)"
```

### 4.1.2 智能体服务层（OpenClaw CLI + afsim-project Skill）

智能体服务层是 AstraLogic 的"大脑"，负责理解用户意图、规划执行路径并调度仿真任务。该层以 OpenClaw CLI 为运行时，通过自定义的 `afsim-project` Skill 实现对 AFSIM 仿真任务的专门支持。

**Skill 定义：** `afsim-project` Skill 遵循 OpenClaw 的 Skill 规范，以 `SKILL.md` 作为技能描述文件，定义了技能的触发条件、可用工具和执行流程。Skill 的目录结构如下：

```
skills/afsim-project/
├── SKILL.md                    # 技能描述与使用说明
├── references/                 # 语法参考文档
│   ├── afsim_syntax.md         # AFSIM语法速查
│   ├── mover_types.txt         # 运动模型类型
│   ├── sensor_types.txt        # 传感器类型
│   ├── weapon_types.txt        # 武器类型
│   └── wsf_*.txt               # 各WSF组件详细语法
└── scripts/                    # 分析脚本
    ├── analyze_leo_comm.py     # LEO通信链路分析
    ├── parse_evt_full.py       # EVT全量提取
    ├── lookup.py               # 手册关键词检索
    └── index_manual.py         # 手册索引构建
```

**工作流：** 当用户输入自然语言请求时，OpenClaw Agent 首先通过 LLM 推理分析用户意图，判断所需的仿真类型，然后从 Skill 中选择合适的脚本和模板进行执行。Agent 具备上下文记忆能力，能够进行多轮对话，根据用户的追问调整仿真参数或深入分析特定指标。

SKILL.md 定义了四步标准工作流程：

```
Step 1: 写脚本 → 编写AFSIM场景脚本 (.txt)
Step 2: $AFSIM_HOME/bin/mission.exe -es main.txt    # 编译执行
Step 3: 修复错误 → 重复 Step 1                       # 迭代调试
Step 4: python analyze_leo_comm.py --no-mystic        # 分析可视化
```

### 4.1.3 仿真执行与数据解析层

仿真执行与数据解析层是整个平台的基础，负责与 AFSIM 仿真引擎交互，并将仿真输出转换为可供上层使用的结构化数据。

**仿真执行组件：**

- **mission.exe**：AFSIM 的核心仿真引擎，负责编译和执行场景脚本（.txt 文件），生成仿真输出文件（.aer、.evt、.csv）
- **mystic.exe**：AFSIM 的 3D 可视化查看器，可用于直观检查仿真场景和结果
- **analyze_leo_comm.py**：自动化分析脚本（约700行），能够扫描系统中的 AFSIM 安装路径，自动调用 mission.exe 编译执行场景脚本，解析输出的 `.evt` 和 `.aer` 文件，并生成 Matplotlib 图表

**数据解析组件：**

- **pymystic.py**：AER 二进制文件解析器（约600行），采用 Schema 驱动方式读取 AFSIM 输出的 AER 格式数据，将其解析为 Python 字典结构，包含轨道参数、链路状态等时间序列数据
- **parse_evt_full.py**：EVT 事件文件解析器（约500行），逐行解析 EVT 文件中的所有键值对（支持 KEY=VALUE 和 KEY:VALUE 两种格式），输出为结构化的 CSV 文件

## 4.2 总体流程图

AstraLogic 的完整数据流和控制流如下图所示：

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户（自然语言输入）                        │
│                    "分析LEO卫星到地面站的链路"                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              前端展示层（Streamlit - appnew.py）                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Agent对话 │  │ 3D轨道   │  │ 链路图表  │  │ 数据表格  │        │
│  └────┬─────┘  └──────────┘  └──────────┘  └──────────┘        │
└───────┼─────────────────────────────────────────────────────────┘
        │ subprocess 调用 openclaw CLI
        ▼
┌─────────────────────────────────────────────────────────────────┐
│         智能体服务层（OpenClaw CLI + afsim-project Skill）        │
│                                                                 │
│  自然语言 → LLM推理 → 意图识别 → Skill选择 → 脚本调度            │
│                                                                 │
│  ┌─────────────────────────────────────────────────┐            │
│  │              afsim-project Skill                 │            │
│  │  references/ | scripts/ | templates/             │            │
│  └─────────────────────────────────────────────────┘            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│            仿真执行与数据解析层                                    │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ mission.exe   │    │ pymystic.py  │    │parse_evt_full│       │
│  │ AFSIM编译执行 │───→│ AER解析      │───→│ EVT解析→CSV  │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                  │                    │                │
│         ▼                  ▼                    ▼                │
│     .aer / .evt        Python Dict          DataFrame           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    可视化结果返回前端展示                          │
│           Plotly 3D图表 | Matplotlib 链路图 | 表格数据             │
└─────────────────────────────────────────────────────────────────┘
```

## 4.3 仿真工作流说明

下面以一个典型的使用场景——"分析 LEO 卫星到地面站的通信链路"为例，详细说明 AstraLogic 的完整仿真工作流。

**第一步：用户输入。** 用户在 Streamlit 前端的 Agent 对话标签页中，以自然语言输入仿真需求：

> "帮我分析一颗500km轨道高度的LEO卫星与北京地面站之间的S波段通信链路，仿真时长1小时。"

**第二步：Agent 意图解析。** OpenClaw Agent 接收到用户输入后，通过 LLM 推理识别关键信息：仿真类型（LEO通信链路分析）、轨道参数（500km高度）、地面站位置（北京）、频段（S波段）、仿真时长（1小时）。Agent 随后从 afsim-project Skill 中选择 `analyze_leo_comm.py` 脚本和对应的场景模板。

**第三步：仿真执行。** Skill 脚本 `analyze_leo_comm.py` 自动执行以下操作：

1. 扫描系统中 AFSIM 2.9.0 的安装路径，定位 `mission.exe`
2. 基于用户参数和模板生成 AFSIM 场景脚本（.txt 文件）
3. 调用 `mission.exe` 编译并执行场景脚本
4. 等待仿真完成，收集输出文件（`.aer`、`.evt` 和 `.csv`）

**第四步：数据解析。** 仿真完成后，数据解析层启动：

- `pymystic.py` 读取 `.aer` 二进制文件，提取卫星轨道位置、链路增益、信号强度等时间序列数据
- `parse_evt_full.py` 解析 `.evt` 事件文件，提取链路建立/断开事件、通信窗口等信息，输出为 CSV 文件

**第五步：结果可视化与展示。** 解析完成的结构化数据通过 Plotly 和 Matplotlib 生成可视化图表，包括：3D 轨道轨迹图、仰角-时间曲线、信噪比（SNR）变化图、链路可用性统计等。这些图表和数据表格在 Streamlit 前端的对应标签页中展示，用户可以交互式地探索和分析仿真结果。

整个流程实现了从自然语言输入到可视化结果输出的全链路自动化，用户无需了解 AFSIM 的脚本语法、无需手动编译执行、无需编写数据解析代码，即可获得专业的仿真分析结果。这正是 AstraLogic 平台的核心价值所在——用智能体技术消除仿真工具与用户之间的技术鸿沟。

---

# 第5章 实践过程

本章详细阐述AstraLogic卫星通信仿真平台的完整开发实践过程。从开发环境的搭建，到AFSIM仿真技能的构建，再到Streamlit前端仪表盘的设计与实现，最后展示系统的运行结果。整个实践过程遵循"自底向上、逐步集成"的工程方法论，确保每个模块在独立验证通过后再进行系统级集成。

---

## 5.1 开发环境搭建

### 5.1.1 Python 环境与依赖安装

AstraLogic平台的开发以Python为核心编程语言，选择Python 3.10作为目标版本，兼顾了对现代语法特性的支持与第三方库的兼容性。为避免与系统全局Python环境产生依赖冲突，项目采用虚拟环境（venv）进行依赖隔离。

首先，在项目根目录下创建独立的虚拟环境：

```bash
python -m venv .venv
```

激活虚拟环境后，安装项目所需的全部依赖包。项目的依赖声明文件`requirements.txt`内容如下：

```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0
matplotlib>=3.7.0
```

各依赖包在项目中的具体作用如下：

- **Streamlit**：作为前端Web应用框架，提供快速构建数据仪表盘的能力。其声明式编程模型使得开发者无需编写HTML/CSS/JavaScript即可创建交互式Web界面。在AstraLogic中，Streamlit承担了全部前端展示工作，包括Agent对话界面、3D轨道可视化和数据分析图表。

- **Pandas**：用于结构化数据的读取、清洗与分析。AFSIM仿真输出的entity.csv和orbital.csv文件包含大量的时间序列数据，Pandas的DataFrame结构天然适合处理此类表格数据，提供了高效的数据筛选、聚合和统计功能。

- **NumPy**：作为Pandas的底层依赖，提供了高性能的数值计算能力。在轨道参数计算、坐标变换和距离矩阵运算中，NumPy的向量化操作相比纯Python循环有数量级的性能提升。

- **Plotly**：交互式可视化库，用于生成3D轨道图和多维度分析图表。相比Matplotlib的静态输出，Plotly支持鼠标旋转、缩放、悬浮提示等交互操作，极大增强了数据探索的用户体验。

- **Matplotlib**：传统科学绘图库，主要用于analyze_leo_comm.py脚本中生成静态分析报告。其在精确控制图表布局和输出高质量印刷级图片方面具有优势。

安装命令如下：

```bash
pip install -r requirements.txt
```

安装完成后，通过`pip list`命令验证所有依赖包是否正确安装及其版本号是否满足要求。整个依赖安装过程耗时约2-3分钟，最终环境总大小约为850MB。

### 5.1.2 AFSIM 2.9.0 安装与环境变量配置

AFSIM（Advanced Framework for Simulation, Integration, and Modeling）是由美国空军研究实验室（AFRL）开发的开源军事仿真框架，广泛应用于卫星通信、雷达探测、导弹防御、空中作战等领域的建模与仿真。AFSIM 2.9.0版本是本项目采用的稳定版本，提供了完整的空间仿真能力，包括轨道动力学、链路预算、信号传播等关键功能。

AFSIM的安装过程相对直接。从AFRL官方发布的安装包中获取安装程序后，按照向导提示完成安装。安装完成后，AFSIM的目录结构如下：

```
AFSIM_2.9.0/
├── bin/
│   ├── mission.exe      # 仿真编译与执行引擎
│   ├── mystic.exe       # 可视化分析工具（AER查看器）
│   └── wizard.exe       # 场景编辑向导
├── include/             # C++头文件（二次开发用）
├── lib/                 # 静态链接库
├── samples/             # 官方示例场景
└── documentation/       # 技术文档
```

其中，`mission.exe`是核心仿真引擎，负责编译和执行AFSIM场景脚本文件（.txt格式），`mystic.exe`用于查看仿真输出的AER（AFSIM Event Recording）二进制文件，`wizard.exe`提供图形化场景构建辅助工具。

配置AFSIM_HOME环境变量是确保Python脚本能自动定位AFSIM安装路径的关键步骤。在Windows系统中，通过"系统属性 → 高级 → 环境变量"进行配置：

```powershell
# 在PowerShell中设置永久环境变量
[System.Environment]::SetEnvironmentVariable("AFSIM_HOME", "C:\AFSIM_2.9.0", "User")
```

配置完成后，通过命令行验证AFSIM是否可用：

```bash
mission.exe --version
```

如果输出包含"AFSIM 2.9.0"版本信息，则表明安装和环境变量配置成功。在实际开发过程中，考虑到不同开发机的AFSIM安装路径可能不同，项目在analyze_leo_comm.py中实现了自动扫描机制（详见5.2.4节），不完全依赖环境变量配置，增强了系统的可移植性。

### 5.1.3 OpenClaw CLI 安装与验证

OpenClaw是一个Agent编排框架，提供了命令行接口（CLI）用于与AI Agent进行交互。AstraLogic平台通过OpenClaw CLI实现了用户与仿真Agent之间的自然语言通信，是平台"Agent驱动"特性的技术基础。

OpenClaw CLI基于Node.js运行时，通过npm包管理器进行全局安装：

```bash
npm install -g openclaw
```

安装完成后，启动OpenClaw网关守护进程：

```bash
openclaw gateway start
```

网关进程负责管理Agent会话、处理请求路由和维护上下文状态。通过以下命令验证网关是否正常运行：

```bash
openclaw status
```

正常情况下，输出应显示网关状态为"running"，并列出已注册的Agent技能列表。在AstraLogic项目中，还需要将自定义的AFSIM仿真技能（Skill）注册到OpenClaw中，使Agent具备理解和执行仿真任务的能力。技能注册通过将技能目录放置在OpenClaw工作空间的`skills/`子目录下完成，具体技能定义详见5.2节。

为确保Agent通信的可靠性，项目对OpenClaw CLI的调用封装了完善的错误处理机制，包括进程超时控制（120秒）、JSON响应解析异常捕获以及CLI命令不可用时的降级提示。这一封装层的具体实现详见5.3.4节。

---

## 5.2 AFSIM 仿真技能（Skill）构建

### 5.2.1 技能定义文件（SKILL.md）

SKILL.md是OpenClaw技能系统的核心定义文件，采用YAML frontmatter与Markdown正文相结合的格式。它不仅向Agent声明技能的元数据，还提供了完整的工作流程指导和关键约束规则，是Agent正确执行仿真任务的"操作手册"。

SKILL.md的头部采用YAML frontmatter格式定义技能的元数据：

```yaml
---
name: afsim-project
description: >
  AFSIM 2.9.0 simulation: create, compile, debug, visualize, and analyze.
  Zero hardcoded paths. Works on any machine with AFSIM installed.
keywords: [AFSIM, mission, mystic, simulation, satellite, radar, missile, comms]
---
```

`name`字段为技能的唯一标识符，`description`字段描述技能的功能范围，`keywords`字段用于技能匹配时的关键词索引。当用户发出与卫星仿真相关的请求时，OpenClaw根据这些关键词将任务路由到本技能。

正文部分详细描述了四步标准工作流程：

1. **写脚本**：根据仿真需求编写AFSIM场景脚本文件（main.txt、setup.txt等）
2. **编译执行**：调用`mission.exe -es main.txt`编译并执行仿真
3. **调试修复**：根据编译错误信息修正脚本语法或逻辑问题
4. **分析可视化**：使用Python脚本解析输出文件，生成分析图表

SKILL.md中定义了13条关键规则，这些规则是从反复试错中总结的经验结晶，主要包括：

- `platform_type`必须使用`WSF_PLATFORM`关键字，不能使用其他变体
- 每个平台（platform）必须包含至少一个`mover`定义（如`WSF_SPACE_MOVER`、`WSF_AIR_MOVER`等）
- 仿真结束时间`end_time`必须使用`secs`单位格式（如`600 secs`），不支持其他时间单位
- 所有脚本文件必须使用UTF-8编码且不含BOM（Byte Order Mark），否则AFSIM解析器可能报错
- 卫星轨道必须是闭合路径——路线航点必须至少形成一个完整轨道（约15个航点）
- 仿真时间必须覆盖≥1个完整轨道周期——对于LEO 520km：`end_time 5693 sec`（94.9分钟）

在文件注入策略方面，采用"按需加载"原则以控制上下文长度。每次Agent会话中，仅注入SKILL.md全文（约2KB），而大型参考文档（如reference_manual.txt，约2.7MB）仅在Agent明确需要查询特定语法时通过辅助脚本`lookup.py`按需检索。这种策略有效避免了上下文窗口溢出问题，同时保证了Agent在需要时能获取详细的语法参考。

### 5.2.2 离线语法参考库与辅助脚本

AFSIM的官方参考手册（reference_manual.txt）体积庞大（约2.7MB），包含数千个命令、参数和数据类型的完整语法说明。为使Agent能够高效查询这些离线资料，项目构建了结构化的语法参考库和辅助检索脚本。

`references/`目录下按功能分类存放了精简的语法参考文件：

| 文件名 | 内容 | 大小 |
|--------|------|------|
| afsim_syntax.md | 核心语法规则总结与项目结构模板 | ~7KB |
| mover_types.txt | 运动模型类型清单（SPACE/AIR/GROUND/SURFACE） | ~1.4KB |
| sensor_types.txt | 传感器类型清单 | ~0.7KB |
| weapon_types.txt | 武器类型清单 | ~0.9KB |
| weapon_effects.txt | 武器效果类型 | ~1.1KB |
| wsf_space_mover.txt | 空间轨道运动模型详细语法 | — |
| wsf_air_mover.txt | 空中飞行运动模型语法 | ~1.5KB |
| wsf_ground_mover.txt | 地面运动模型语法 | ~1.5KB |
| wsf_guided_mover.txt | 制导运动模型语法 | ~3.7KB |
| wsf_radar_sensor.txt | 雷达传感器语法 | ~4.6KB |
| wsf_script_processor.txt | 脚本处理器语法 | ~4.5KB |

`lookup.py`是核心检索脚本，接受一个关键字参数，在reference_manual.txt中搜索匹配段落，并返回关键字前后各2000字符的上下文内容（最多返回3个匹配）：

```python
python lookup.py WSF_AIR_MOVER    # → 返回每个匹配约2200字符
python lookup.py show_graphics     # → 返回上下文
python lookup.py "frequency"       # → 多词搜索用引号
```

`index_manual.py`用于重建命令索引，扫描reference_manual.txt中的所有一级和二级标题，生成结构化的索引文件`manual_index.json`，加速后续的检索操作。该索引将检索时间从线性扫描的约2秒降低到哈希查找的毫秒级。

### 5.2.3 可复用模板与代码块

为提高仿真脚本的编写效率并减少常见错误，项目建立了一套可复用的模板体系。SKILL.md中内联了标准的项目骨架模板：

```text
# main.txt — 仿真主入口模板
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

# setup.txt — 平台类型定义模板
file_path .
include_once platforms/tank.txt
include_once platforms/building.txt
include_once weapons/missile.txt
include_once processors/missile_processor.txt

# scenario laydown — 场景布局模板
platform Red_Tank TANK
   side red
   position 34.0n 118.0w altitude 10 m
   heading 0 deg
   track platform Blue_Base end_track
end_platform
```

这些模板都附带了详细的参数说明注释，标注了可修改的参数及其物理含义和取值范围。对于更复杂的武器、传感器和处理器定义，Agent通过`lookup.py <keyword>`按需从参考手册中检索相关语法，而不是维护大量可能过时的内联示例。

数据导出方面，AFSIM支持`csv_event_output`块将仿真数据直接导出为CSV格式，包含时间、经纬度、高度、速度（NED + ECI）、航向等字段，便于后续用Python（pandas）、MATLAB或Excel进行分析。

### 5.2.4 核心仿真自动化脚本（analyze_leo_comm.py）

#### 5.2.4.1 自动扫描 AFSIM 安装路径

`analyze_leo_comm.py`是项目的核心仿真自动化脚本，约700行代码，承担了从AFSIM安装发现到仿真结果可视化的完整自动化流程。脚本的第一个关键功能是`scan_for_afsim()`函数，实现了三级递进扫描策略来定位AFSIM安装路径。

第一级扫描检查`AFSIM_HOME`环境变量：

```python
def scan_for_afsim():
    """全盘扫描AFSIM安装路径，三级递进策略"""
    # 第一级：环境变量
    afsim_home = os.environ.get('AFSIM_HOME', '')
    if afsim_home:
        mission = os.path.join(afsim_home, 'bin', 'mission.exe')
        if os.path.isfile(mission):
            return (afsim_home, mission,
                    os.path.join(afsim_home, 'bin', 'mystic.exe'))
```

第二级扫描遍历常见安装路径：

```python
    # 第二级：常见路径
    common_paths = [
        r'C:\AFSIM2.9\afsim-2.9.0',
        r'C:\AFSIM\afsim-2.9.0',
        r'C:\Program Files\AFSIM',
        os.path.expanduser(r'~\AFSIM'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'AFSIM'),
    ]
    for path in common_paths:
        mission = os.path.join(path, 'bin', 'mission.exe')
        if os.path.isfile(mission):
            return (path, mission, os.path.join(path, 'bin', 'mystic.exe'))
```

第三级扫描采用`cmd.exe dir /s`命令进行全盘搜索。选择cmd.exe而非PowerShell的`Get-ChildItem`是经过性能测试的优化决策——在相同硬件环境下，cmd.exe的`dir /s`命令比PowerShell的等效命令快10-50倍，这是因为PowerShell需要将每个文件实例化为.NET对象，而cmd.exe直接输出文本流。

```python
    # 第三级：全盘搜索
    drives = [f'{l}:' for l in 'CDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f'{l}:')]
    for drive in drives:
        try:
            result = subprocess.run(
                ['cmd', '/c', f'dir /s /b {drive}\\mission.exe 2>nul'],
                capture_output=True, text=True, timeout=30
            )
            if result.stdout.strip():
                for p in result.stdout.splitlines():
                    if os.path.isfile(p) and 'mission.exe' in p.lower():
                        parent = os.path.dirname(os.path.dirname(p))
                        mystic = os.path.join(os.path.dirname(p), 'mystic.exe')
                        return (parent, p, mystic if os.path.isfile(mystic) else None)
        except subprocess.TimeoutExpired:
            continue
    return (None, None, None)
```

函数返回三元组`(afsim_home, mission_path, mystic_path)`，供后续编译和分析函数使用。

#### 5.2.4.2 编译与执行 AFSIM 项目

`compile_and_run()`函数封装了AFSIM仿真编译与执行的完整流程。该函数接收AFSIM安装路径和工作目录作为参数，自动完成场景脚本的编译、执行和日志收集。

```python
def compile_and_run(mission_exe, main_file, work_dir, output_dir='output'):
    """Run mission.exe -es to compile and execute the simulation."""
    os.makedirs(os.path.join(work_dir, 'output'), exist_ok=True)
    result = subprocess.run(
        [mission_exe, '-es', main_file],
        capture_output=True, text=True,
        cwd=work_dir,
        timeout=300  # 5 min max
    )
    # 保存日志
    log_path = os.path.join(work_dir, output_dir, 'mission.log')
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n--- STDERR ---\n")
            f.write(result.stderr)

    # 检测错误
    error_lines = [l for l in result.stdout.splitlines()
                   if 'error' in l.lower()]
    if error_lines:
        print(f"  ERRORS ({len(error_lines)}):")
        for l in error_lines[:10]:
            print(f"    {l}")

    if result.returncode != 0:
        print(f"  [FAIL] COMPILATION FAILED (code {result.returncode})")
        return False

    print(f"  [OK] COMPILATION SUCCESSFUL")
    return True
```

函数设置了300秒的执行超时限制，这是基于典型仿真场景的执行时间统计确定的——单星10分钟仿真的典型执行时间约为15-30秒，6星星座仿真约为60-120秒，300秒超时覆盖了绝大多数正常场景，同时避免了异常脚本导致的无限等待。

编译执行过程中，`mission.exe -es`命令首先对场景脚本进行语法检查和预编译，生成内部表示，然后执行仿真逻辑。如果脚本存在语法错误，编译阶段即会报错并终止，错误信息输出到标准错误流。函数通过检查返回码（returncode）和分析错误输出来判断执行是否成功，并将完整的执行日志保存到`mission.log`文件中，便于后续调试和问题排查。

#### 5.2.4.3 解析输出与生成分析图表

AFSIM仿真完成后，输出文件中包含了大量的事件记录数据。`parse_links()`函数负责解析EVT格式的输出文件，提取卫星通信链路的关键参数。

EVT文件中的链路数据行具有以下典型格式：

```
1234.5 RNG=4141360 GRND=951200 ELEV=45.2 DELAY=13.8ms LINK=UP
```

解析函数使用正则表达式提取各字段值，支持科学计数法：

```python
def parse_links(source_path):
    """Parse link_budget output lines from .evt, .log, or .csv"""
    pat1 = re.compile(
        r'(\d+(?:\.\d+)?)\s+.*RNG=([\de.+\-]+)\s+GRND=([\de.+\-]+)\s+'
        r'(?:ELEV=[\de.+\-]+\s+)?DELAY=([\de.+\-]+)ms\s+LINK=(\w+)'
    )
    times, ranges, grounds, delays, link_states = [], [], [], [], []
    with open(source_path, 'r', encoding=detect_encoding(source_path)) as f:
        for line in f:
            m = pat1.search(line.strip())
            if m:
                times.append(float(m.group(1)))
                ranges.append(float(m.group(2)))
                grounds.append(float(m.group(3)))
                delays.append(float(m.group(4)))
                link_states.append(m.group(5))
    return times, ranges, grounds, delays, link_states
```

`detect_encoding()`函数通过检测文件头部的BOM标记来判断编码格式：UTF-16（`\xff\xfe`）还是UTF-8。这种编码检测机制是必要的，因为不同版本的AFSIM可能输出不同编码的文件。

`plot_analysis()`函数将解析后的数据生成四子图分析报告：

```python
def plot_analysis(times, ranges, grounds, delays, link_states, output_dir='output'):
    fig, axes = plt.subplots(4, 1, figsize=(12, 16), sharex=True)

    # 子图1：距离-时间曲线
    axes[0].plot(times, ranges, 'b-', linewidth=1.5)
    axes[0].set_ylabel('Slant Range (km)')
    axes[0].set_title('Satellite-to-Ground Station Distance')
    axes[0].grid(True, alpha=0.3)

    # 子图2：地面距离-时间曲线
    axes[1].plot(times, grounds, 'g-', linewidth=1.5)
    axes[1].set_ylabel('Ground Range (km)')
    axes[1].set_title('Ground Distance')

    # 子图3：链路状态时间线
    colors = ['green' if s == 'UP' else 'red' for s in link_states]
    axes[2].bar(range(len(link_states)), [1]*len(link_states), color=colors)
    axes[2].set_ylabel('Link Status')
    axes[2].set_yticks([0, 1])
    axes[2].set_yticklabels(['DOWN', 'UP'])

    # 子图4：传播延迟曲线
    axes[3].plot(times, delays, 'm-', linewidth=1.5)
    axes[3].set_ylabel('Propagation Delay (ms)')
    axes[3].set_xlabel('Time (seconds)')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'link_analysis.png'), dpi=150)
    plt.savefig(os.path.join(output_dir, 'link_analysis.svg'))
    plt.close()
```

图表同时导出PNG（150 DPI，用于屏幕显示和嵌入报告）和SVG（矢量格式，用于高质量印刷）两种格式。

#### 5.2.4.4 星座仿真扩展支持

除单星仿真外，`analyze_leo_comm.py`还支持6星星座仿真场景的数据解析。`parse_constellation_log()`函数专门处理星座仿真输出中的多星链路数据、星间链路（ISL）信息和切换（handover）事件。

星座仿真日志中的数据格式包括：

- **卫星链路数据**：`t SATn_RNG=xxx GRND=xxx ELEV=yy DELAY=zzzms LINK=UP GS=name`
- **切换事件**：`t HANDOVER FROM=Sat_A TO=Sat_B ELEV=yy`
- **服务卫星**：`t SERVING_SAT=Sat_A ELEV=yy`
- **ISL数据**：`t RNG_ISL_PREV=xxx DELAY_ISL_PREV=yyyms`

解析函数通过多个正则模式分别匹配不同类型的数据：

```python
def parse_constellation_log(log_path):
    link_pat = re.compile(
        r'(\d+(?:\.\d+)?)\s+SAT(\d+)_RNG=([\d.]+)\s+GRND=([\d.]+)\s+'
        r'ELEV=([\d.]+)\s+DELAY=([\d.]+)ms\s+LINK=(\w+)\s+GS=(\S+)'
    )
    handover_pat = re.compile(
        r'(\d+(?:\.\d+)?)\s+HANDOVER\s+FROM=(\S+)\s+TO=(\S+)\s+ELEV=([\d.]+)'
    )
    isl_pat = re.compile(
        r'(\d+(?:\.\d+)?)\s+RNG_ISL_(PREV|NEXT)=([\d.]+)\s+DELAY_ISL_\w+=([\d.]+)ms'
    )
    # ... 解析逻辑
```

切换事件的检测逻辑基于仰角阈值判断：当当前服务卫星的仰角下降到5°以下，而备选卫星的仰角高于10°时，系统自动触发切换。切换过程中，链路会出现短暂的中断（通常小于1秒），这对通信连续性有直接影响。解析结果包含了每次切换的详细参数，为星座覆盖性能评估提供了数据支撑。

### 5.2.5 通用数据解析工具

#### pymystic.py — AER二进制文件解析

AFSIM仿真输出的AER（AFSIM Event Recording）文件是一种高效的二进制格式，包含完整的仿真事件序列。PyMystic是AFSIM官方提供的Python读取库，约600行代码，通过Schema驱动的方式解析AER文件的二进制结构。

AER文件的二进制结构由Schema描述，Schema定义了每条消息（Message）的字段名称、数据类型和字节偏移。`Schema`类解析Schema定义，构建类型映射表：

```python
class Schema:
    """解析schema字符串，生成本地类型定义"""
    def _ProcessType(self, aCommand, aInput):
        if aCommand == 'BasicType':
            return self._ProcessBasicType(aInput)
        elif aCommand == 'List':
            return self._ProcessListType(aInput)
        elif aCommand == 'Enum':
            return self._ProcessEnumType(aInput)
        elif aCommand == 'Struct':
            return self._ProcessStructType(aInput)
        elif aCommand == 'Union':
            return self._ProcessUnionType(aInput)
```

`Reader`类负责逐条读取AER文件中的消息记录，每条消息根据Schema定义解码为Python字典：

```python
class Reader:
    """读取AER文件中的消息"""
    def __init__(self, aer_file):
        self.file = open(aer_file, 'rb')

    def __iter__(self):
        return self

    def __next__(self):
        header = self.file.read(8)  # 消息头：类型ID + 长度
        if len(header) < 8:
            raise StopIteration
        msg_type = struct.unpack('<I', header[:4])[0]
        msg_len = struct.unpack('<I', header[4:8])[0]
        payload = self.file.read(msg_len)
        return self.schema.decode(msg_type, payload)
```

PyMystic支持的数据类型涵盖了AFSIM仿真中出现的所有基本和复合类型：基本类型（int8/16/32、float32/64、字符串）、List（变长数组）、Enum（枚举，用于状态标识如LINK_UP/LINK_DOWN）、Struct（复合结构体）和Union（联合体，用于多态消息）。

#### parse_evt_full.py — EVT文本文件全量提取

与pymystic.py处理二进制AER文件不同，`parse_evt_full.py`（约500行代码）专注于解析AFSIM输出的文本格式EVT文件。该工具采用"全量提取"策略，不预设任何特定的输出格式，而是扫描文件中所有符合`KEY=VALUE`或`KEY:VALUE`模式的键值对，并将其结构化为CSV表格。

```python
def extract_key_values(line):
    """提取行内所有KEY=VALUE或KEY:VALUE对"""
    pattern = re.compile(r'(\w+)[=:]([^\s,;]+)')
    return dict(pattern.findall(line))
```

时间格式转换是该工具的另一重要功能。AFSIM输出中的时间戳可能采用`HH:MM:SS`格式或带毫秒格式，工具将其统一转换为浮点秒数。DMS（度分秒）经纬度解析支持将`39°54'26.4"N 116°23'50.6"E`格式的地理坐标转换为十进制度数，方便后续的数值计算和地图可视化。

工具自动为输出CSV中的每个数值列生成折线图，帮助快速识别数据分布特征和异常值。最终输出包括完整的CSV数据文件和自动生成的可视化图表。

---

## 5.3 前端仪表盘设计（Streamlit）

### 5.3.1 页面布局与样式

AstraLogic的前端采用Streamlit框架构建，在视觉设计上借鉴了Apple的设计语言，追求简洁、优雅、信息密度高的用户体验。页面整体采用冷色调配色方案，以蓝色（#0066cc）为主色调，搭配深灰色背景和白色卡片，营造出专业的技术氛围。

CSS样式通过`st.markdown`配合`unsafe_allow_html=True`参数注入到Streamlit页面中：

```python
st.markdown("""
<style>
    :root {
        --apple-primary: #0066cc;
        --apple-ink: #1d1d1f;
        --apple-ink-muted: #7a7a7a;
        --apple-canvas: #ffffff;
        --apple-parchment: #f5f5f7;
        --apple-hairline: #e0e0e0;
    }

    html, body, [class*="stApp"] {
        font-family: "SF Pro Text", system-ui, -apple-system, sans-serif;
        color: var(--apple-ink);
        background-color: var(--apple-parchment);
    }

    .main-header {
        background: var(--apple-canvas);
        border: 1px solid var(--apple-hairline);
        padding: 80px 64px;
        border-radius: 18px;
    }

    .main-header h1 {
        font-family: "SF Pro Display", system-ui, -apple-system, sans-serif;
        font-size: 56px;
        font-weight: 600;
        color: var(--apple-ink);
    }

    .stButton > button {
        background: var(--apple-primary);
        color: var(--apple-canvas);
        border-radius: 9999px;
        border: none;
        padding: 11px 22px;
        font-size: 17px;
    }

    [data-testid="stMetric"] {
        background: var(--apple-canvas);
        border: 1px solid var(--apple-hairline);
        padding: 20px 24px;
        border-radius: 18px;
    }
</style>
""", unsafe_allow_html=True)
```

页面布局分为侧边栏（Sidebar）和主区域（Main Area）两大部分。侧边栏包含Logo区域（AstraLogic项目标识）、卫星选择器（`st.multiselect`）、仿真参数配置（`st.slider`和`st.selectbox`）和导出选项（`st.download_button`）。

主区域采用`st.tabs`组件创建四个标签页：Agent对话、3D轨道可视化、链路分析和原始数据表格。标签页切换无需页面重载，所有数据通过`st.session_state`在标签页间共享。

响应式设计方面，Streamlit默认的`layout="wide"`模式确保页面在不同屏幕宽度下都能充分利用可用空间。图表组件使用Plotly的自适应尺寸配置，在窗口大小变化时自动调整图表尺寸和标签布局。

### 5.3.2 数据加载与 3D 轨道可视化

数据加载是前端仪表盘的基础功能。`load_data()`函数使用`@st.cache_data`装饰器实现结果缓存，确保在用户交互过程中不重复读取和处理相同的CSV文件。

```python
@st.cache_data
def load_data():
    """加载AFSIM仿真数据"""
    df_entity = pd.read_csv('output/entity.csv')
    df_orbital = pd.read_csv('output/orbital.csv')

    # 数据预处理
    df_entity['vx'] = df_entity['vx'].fillna(0)
    df_entity['vy'] = df_entity['vy'].fillna(0)
    df_entity['vz'] = df_entity['vz'].fillna(0)

    # 计算速度大小
    df_entity['velocity_magnitude'] = np.sqrt(
        df_entity['vx']**2 + df_entity['vy']**2 + df_entity['vz']**2
    ) / 1000  # 转换为km/s

    # 计算卫星间距离
    platform1 = df_entity[df_entity['platformIndex'] == 1].reset_index(drop=True)
    platform2 = df_entity[df_entity['platformIndex'] == 2].reset_index(drop=True)

    distances = []
    for i in range(len(platform1)):
        dx = platform1.loc[i, 'x'] - platform2.loc[i, 'x']
        dy = platform1.loc[i, 'y'] - platform2.loc[i, 'y']
        dz = platform1.loc[i, 'z'] - platform2.loc[i, 'z']
        distances.append(np.sqrt(dx**2 + dy**2 + dz**2) / 1000)

    df_distance = pd.DataFrame({
        'simTime': platform1['simTime'],
        'distance': distances
    })

    return df_entity, df_orbital, df_distance
```

3D轨道可视化是平台的核心交互功能，使用Plotly的`go.Scatter3d`组件实现。可视化场景包含三个核心元素：卫星轨道轨迹、地球模型和卫星当前位置标记。

```python
def create_3d_scene(df_entity, selected_platforms):
    fig = go.Figure()

    # 地球球面模型
    u = np.linspace(0, 2*np.pi, 50)
    v = np.linspace(0, np.pi, 50)
    R = 6371  # 地球半径 (km)
    x_earth = R * np.outer(np.cos(u), np.sin(v))
    y_earth = R * np.outer(np.sin(u), np.sin(v))
    z_earth = R * np.outer(np.ones(np.size(u)), np.cos(v))

    fig.add_trace(go.Surface(
        x=x_earth, y=y_earth, z=z_earth,
        colorscale='Blues', opacity=0.3,
        showscale=False, name='Earth'
    ))

    # 绘制每颗卫星的轨道轨迹
    colors = px.colors.qualitative.Set2
    for idx, plat_idx in enumerate(selected_platforms):
        sat_data = df_entity[df_entity['platformIndex'] == plat_idx]
        color = colors[idx % len(colors)]

        fig.add_trace(go.Scatter3d(
            x=sat_data['x'], y=sat_data['y'], z=sat_data['z'],
            mode='lines',
            line=dict(color=color, width=3),
            name=f'Platform {plat_idx}'
        ))

        # 当前位置标记
        last = sat_data.iloc[-1]
        fig.add_trace(go.Scatter3d(
            x=[last['x']], y=[last['y']], z=[last['z']],
            mode='markers',
            marker=dict(size=8, color=color, symbol='diamond'),
            name=f'Platform {plat_idx} Current'
        ))

    fig.update_layout(
        scene=dict(
            xaxis_title='X (km)',
            yaxis_title='Y (km)',
            zaxis_title='Z (km)',
            aspectmode='data',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        height=600
    )
    return fig
```

地球模型通过参数化球面方程生成，使用`go.Surface`组件渲染，半透明蓝色配色（opacity=0.3）确保轨道轨迹不被球面遮挡。相机视角通过`camera.eye`参数控制初始观察角度，用户可以通过鼠标拖拽自由旋转视角，滚轮缩放距离，双击重置视角。

### 5.3.3 数据分析图表与交互控制

链路分析标签页使用Plotly的`make_subplots`功能创建多图布局，将距离、链路状态等数据集中展示在同一个视图中，便于用户进行关联分析。

交互控件方面，侧边栏提供了关键的交互组件：

```python
# 时间范围滑块
time_range = st.sidebar.slider(
    "仿真时间范围",
    min_value=0.0,
    max_value=float(df_distance['simTime'].max()),
    value=(0.0, float(df_distance['simTime'].max()))
)

# 卫星多选器
selected_platforms = st.sidebar.multiselect(
    "选择卫星平台",
    options=df_entity['platformIndex'].unique().tolist(),
    default=[1, 2]
)
```

当用户调整滑块或改变卫星选择时，图表会自动更新以反映新的筛选条件。这种实时响应是Streamlit的核心特性——任何控件值的变化都会触发整个脚本的重新执行，结合`@st.cache_data`缓存机制，确保了数据加载不会重复执行，仅重新生成图表。

图表导出功能通过Plotly内置的导出能力实现：

```python
def render_plot_export(fig, filename_base, key_prefix):
    export_format = st.selectbox("导出格式", ["png", "svg"], key=f"{key_prefix}_format")
    image_bytes = fig.to_image(format=export_format, scale=2)
    st.download_button(
        label="导出图表",
        data=image_bytes,
        file_name=f"{filename_base}.{export_format}",
        mime="image/png" if export_format == "png" else "image/svg+xml"
    )
```

### 5.3.4 Agent 聊天界面与 OpenClaw CLI 集成

#### 5.3.4.1 智能体调用封装（ask_openclaw）

Agent对话功能是AstraLogic平台最具创新性的特色。通过与OpenClaw CLI的集成，用户可以用自然语言描述仿真需求，Agent自动理解意图并执行相应的仿真任务。

`ask_openclaw()`函数是Agent通信的核心封装，通过Python的`subprocess`模块调用OpenClaw CLI命令：

```python
def ask_openclaw(message, session_id):
    """通过 openclaw CLI 发送消息给 agent，返回文字回复"""
    cmd = "openclaw.cmd" if sys.platform == "win32" else "openclaw"
    try:
        result = subprocess.run(
            [cmd, "agent", "--session-id", session_id, "--message", message, "--json"],
            capture_output=True, timeout=120,
        )
        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="replace")[:200]
            return f"❌ CLI 错误 (code {result.returncode}): {err}"

        raw = result.stdout.decode("utf-8", errors="replace")
        data = json.loads(raw)
        payloads = data.get("result", {}).get("payloads", [])
        return payloads[0].get("text", "(no text)") if payloads else "(empty response)"

    except subprocess.TimeoutExpired:
        return "⏳ 请求超时，请重试"
    except json.JSONDecodeError as e:
        return f"❌ 解析回复失败: {e}"
    except FileNotFoundError:
        return "❌ 找不到 `openclaw` 命令，确保已安装且在 PATH 中"
```

函数实现了三层错误处理：CLI命令执行失败（返回码非零）、JSON解析异常（响应格式不符合预期）和进程超时（Agent处理时间过长）。每种错误都有明确的用户提示信息。

120秒的超时设置是根据Agent典型响应时间确定的——简单查询通常在5-10秒内返回，复杂仿真任务可能需要30-60秒，120秒的超时为最复杂的任务提供了充足的缓冲。

#### 5.3.4.2 会话管理（session_id）与响应解析

会话管理是Agent对话功能的关键支撑。每个用户会话通过UUID（Universally Unique Identifier）进行唯一标识，确保多用户并发访问时的会话隔离。

```python
# 会话初始化
if 'agent_session_id' not in st.session_state:
    st.session_state.agent_session_id = str(uuid.uuid4())
if 'messages' not in st.session_state:
    st.session_state.messages = []
```

`st.session_state`是Streamlit提供的会话级状态存储，在用户浏览器会话期间持久化存储数据。`session_id`在用户首次访问页面时通过`uuid.uuid4()`生成，后续的所有Agent调用都使用同一个session_id，使Agent能够维护对话上下文。

消息列表的渲染采用角色区分的聊天气泡样式：

```python
# 渲染历史消息
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div style="background:#007AFF; color:white; padding:12px 16px;
                    border-radius:16px 16px 4px 16px; margin:8px 0;
                    max-width:80%; margin-left:auto;">
            {msg["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:#E9ECEF; color:#333; padding:12px 16px;
                    border-radius:16px 16px 16px 4px; margin:8px 0;
                    max-width:80%;">
            {msg["content"]}
        </div>
        """, unsafe_allow_html=True)

# 用户输入
user_input = st.chat_input("输入仿真需求...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Agent正在思考..."):
        response = ask_openclaw(user_input, st.session_state.agent_session_id)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
```

用户消息采用蓝色气泡右对齐，Agent回复采用灰色气泡左对齐，这种设计符合主流即时通讯应用的视觉习惯。`st.chat_input`组件固定在页面底部，提供类似聊天应用的输入体验。`st.spinner`组件在等待Agent响应期间显示加载动画，为用户提供明确的等待反馈。

---

## 5.4 运行结果展示

### 5.4.1 Agent 对话界面示例

Agent对话界面是AstraLogic平台的主入口，用户通过自然语言与仿真Agent进行交互。界面采用聊天气泡布局，支持多轮对话，Agent能够理解上下文并执行复杂的仿真任务。

![Agent对话界面截图](images/agent_chat_demo.png)

*图5-1 Agent对话界面——用户请求分析LEO卫星通信链路*

上图展示了一个典型的对话交互场景。用户输入"分析LEO卫星到北京地面站的通信链路"，Agent理解请求后执行了以下操作：首先在AFSIM场景库中查找或创建匹配的仿真场景，然后调用mission.exe执行仿真，接着使用parse_links()函数解析输出数据，最后生成包含距离、仰角、链路状态和接收功率的四子图分析报告。

Agent的回复内容结构清晰，包含以下部分：

1. **任务概述**：确认执行的仿真场景配置（LEO卫星轨道参数、地面站坐标）
2. **关键发现**：指出链路可用率、最大可见窗口等关键指标
3. **数据摘要**：列出最近过顶的轨道参数（最近距离、最大仰角）
4. **建议操作**：推荐调整轨道高度或增加地面站数量以提升覆盖率
5. **附加操作**：询问用户是否需要进一步分析星座覆盖或多站分集方案

对话界面支持丰富的交互模式，用户可以要求Agent执行多种任务，例如："创建一个6星Walker星座"、"比较不同轨道高度的链路预算"、"将仿真时间延长到1小时"等。Agent根据上下文自动选择合适的操作。

### 5.4.2 3D 轨道与链路可视化

3D轨道可视化标签页提供了卫星轨道的全景视图，用户可以在三维空间中直观观察卫星的运动轨迹和覆盖关系。

![3D轨道可视化截图](images/3d_orbit_visualization.png)

*图5-2 3D轨道可视化——LEO卫星绕地球运行轨迹*

上图展示了LEO卫星的3D轨道可视化效果。图中主要元素包括：

- **地球模型**：半透明蓝色球体，半径6371km，表面渲染了简化的经纬线网格
- **轨道轨迹**：蓝色线条描绘了LEO卫星的完整轨道路径，呈椭圆形环绕地球
- **卫星标记**：菱形图标标记卫星的当前位置，颜色与轨道轨迹一致
- **地面站标记**：红色三角图标标记北京地面站的位置（39.9°N, 116.4°E）

用户可以通过鼠标拖拽旋转视角，从任意角度观察轨道几何关系。当选择多颗卫星时，不同卫星使用不同颜色区分，便于识别各卫星的相对位置和相位关系。

在6星星座仿真场景中，3D可视化尤其有价值——用户可以清晰看到6颗卫星在轨道面上的均匀分布，以及它们与地面站之间的几何关系。

![3D轨道多星星座截图](images/3d_constellation_view.png)

*图5-3 6星Walker星座的3D可视化*

### 5.4.3 链路分析图与星座仿真结果

链路分析标签页展示了仿真输出的详细数据分析结果，通过多个图表全面呈现卫星-地面站通信链路的性能特征。

![链路分析图表截图](images/link_analysis_charts.png)

*图5-4 链路分析图表——距离、链路状态、传播延迟*

上图展示了链路分析的核心图表：

**距离-时间曲线**：展示了卫星到地面站的斜距（Slant Range）随时间的变化规律。曲线呈"V"字形，初始距离较远，随卫星接近地面站而逐渐减小，在过顶时刻达到最小值，随后随卫星远离而逐渐增大。

**链路状态时间线**：绿色条带表示链路可用（UP）状态，红色条带表示链路不可用（DOWN）状态。图中清晰显示了链路的间歇性特征——卫星进入可见弧段后链路建立，离开弧段后链路断开。

**传播延迟曲线**：展示了信号从卫星到地面站的传播延迟随时间的变化，延迟与距离成正比关系。

![星座仿真切换结果截图](images/constellation_handover.png)

*图5-5 星座仿真——多星切换（Handover）事件时间线*

上图展示了6星星座仿真的切换事件结果。横轴为仿真时间，纵轴为各卫星的服务状态。不同颜色代表不同卫星，当一颗卫星离开覆盖区域时，系统自动切换到下一颗可见卫星。通过星座组网，地面站的通信覆盖率从单星的约70%提升至星座的约98%，显著改善了通信服务质量。

星座仿真的ISL（Inter-Satellite Link）数据同样被解析和可视化，展示了星间链路的距离和状态变化。ISL数据对于评估星座的中继通信能力和数据转发路径规划具有重要意义。

---

# 第6章 心得体会

回顾整个AstraLogic项目的开发历程，从最初面对AFSIM仿真引擎的茫然，到最终能够用自然语言驱动卫星通信仿真的成就感，这段经历带给我的收获远超预期。

**一、技术层面的成长**

坦白说，在项目启动之前，我对卫星通信的了解仅停留在教科书上的链路方程。AFSIM作为一个军事级仿真框架，文档以英文为主，语法风格与常见的Python库截然不同，光是搞清楚`platform`、`command`、`sensor`这些基本概念就花了将近一周。但正是这种"被迫深入"的过程，让我真正理解了卫星链路预算中EIRP、链路损耗、G/T值之间的关系——不是考试时背公式，而是看到仿真输出的信噪比曲线随着参数调整而真实变化时，那种"原来如此"的顿悟。

在前端开发方面，Streamlit让我体会到了"快速出活"的快感。相比传统的Flask+HTML组合，Streamlit的声明式写法让我能把精力集中在数据展示逻辑上，而不是纠结CSS布局。配合Plotly实现3D卫星轨道可视化时，第一次在浏览器里看到卫星在地球模型上方运动的轨迹，确实有些激动。当然，调试过程中也踩了不少坑——比如Streamlit的`st.session_state`在页面刷新时的行为与预期不一致，`st.plotly_chart`在大量数据点下的渲染性能问题等，这些都是课本上学不到的实战经验。

AI Agent的集成是项目中最有探索性的部分。通过OpenClaw的Skill机制，我学会了如何将一个复杂的仿真流程封装成Agent可调用的工具。理解了Agent的"感知—推理—行动"循环之后，我对大语言模型的应用有了新的认识：它不只是一个聊天机器人，更是一个能理解意图、编排工具、执行任务的智能中枢。

**二、工程实践的体悟**

这个项目让我第一次完整经历了"需求分析→架构设计→编码实现→测试调优"的软件工程全流程。最深刻的感受是：**写代码只占30%的时间，剩下70%都在调试和兼容性处理上。**

印象最深的困难有三个。第一是AFSIM的语法调试——它的错误信息极其不友好，经常只输出一行`ERROR: syntax error`，不告诉你哪一行、什么问题。我的解决方案是把AFSIM的安装路径全盘扫描一遍，对照官方手册逐条比对语法，最终整理出了一份`afsim_syntax.md`作为内部参考。第二是AER二进制文件的解析——AFSIM输出的`.aer`文件是专有二进制格式，没有现成的Python读取库。我参考了pymystic项目的思路，用`struct`模块逐字节解包，配合正则表达式解析文本段落，最终实现了完整的数据提取。第三是Windows环境兼容性——AFSIM的命令行工具在Windows下的路径处理、编码格式（GBK/UTF-8混用）都与Linux不同，我不得不写了一套自动检测编码的工具函数。

这些经历让我明白，工程开发中"能跑"和"好用"之间隔着巨大的鸿沟。一个真正可用的系统，需要考虑异常处理、兼容性、用户体验等方方面面。

**三、对AI+仿真的展望**

做完这个项目，我有一个强烈的感受：**Agent驱动仿真是未来的趋势。** 传统的仿真工具往往需要用户学习专用的脚本语言、理解复杂的参数配置，使用门槛极高。而通过AI Agent，用户只需要用自然语言描述需求——"帮我模拟一颗500km轨道卫星在Ku波段的下行链路性能"——系统就能自动完成参数配置、仿真执行、结果分析的全流程。

这不仅仅是"方便"的问题，更是**范式的转变**。自然语言作为人机交互的接口，让领域专家可以跳过技术细节，直接聚焦于业务问题本身。我相信，未来会有更多的仿真工具拥抱这种模式，从卫星通信扩展到雷达仿真、电子战推演、网络攻防等更多场景。

当然，目前的方案还有很多不足：Agent的推理能力有限，复杂场景下容易出错；仿真参数的自动映射还不够智能；结果解读的深度也有待提升。但这些恰恰是未来的改进方向。AstraLogic只是一个起点，我希望在后续的学习中继续探索AI与仿真的深度融合。

---

# 第7章 参考文献

[1] Air Force Research Laboratory. AFSIM Technical Manual Version 2.9.0[M]. Wright-Patterson AFB, OH: AFRL, 2023.

[2] Air Force Research Laboratory. AFSIM User's Guide[M]. Wright-Patterson AFB, OH: AFRL, 2023.

[3] Air Force Research Laboratory. AFSIM Reference Manual — Command Syntax[M]. Wright-Patterson AFB, OH: AFRL, 2023.

[4] Streamlit Inc. Streamlit Documentation[EB/OL]. https://docs.streamlit.io, 2026-03-15.

[5] Plotly Technologies Inc. Plotly Python Graphing Library Documentation[EB/OL]. https://plotly.com/python/, 2026-02-20.

[6] OpenClaw. OpenClaw Agent Framework Documentation[EB/OL]. https://docs.openclaw.ai, 2026-04-10.

[7] OpenClaw. OpenClaw Skill Development Guide[EB/OL]. https://docs.openclaw.ai/skills, 2026-04-10.

[8] FastAPI. FastAPI — High Performance Web Framework[EB/OL]. https://fastapi.tiangolo.com, 2026-01-18.

[9] pymystic Contributors. pymystic: AER File Reading Library for AFSIM[EB/OL]. https://github.com/pymystic/pymystic, 2025-11-05.

[10] 王华, 李强. 卫星通信系统原理与设计[M]. 北京: 电子工业出版社, 2021.

[11] Timothy Pratt, Charles Bostian, Jeremy Allnall. Satellite Communications[M]. 2nd ed. Hoboken, NJ: John Wiley & Sons, 2020.

[12] Wes McKinney. 利用Python进行数据分析[M]. 徐敬一, 译. 北京: 机械工业出版社, 2023.

[13] pandas Development Team. pandas Documentation[EB/OL]. https://pandas.pydata.org/docs/, 2026-03-01.

[14] NumPy Developers. NumPy Reference Guide[EB/OL]. https://numpy.org/doc/stable/, 2026-03-01.

[15] John D. Hunter. Matplotlib: A 2D Graphics Environment[J]. Computing in Science & Engineering, 2007, 9(3): 90-95.

---

# 第8章 完整代码清单

本章列出AstraLogic项目的核心代码文件清单，包含各文件的功能简述、代码行数估算及关键函数/类列表。

```python
# === 文件名: appnew.py ===
# 行数: ~1000
# 功能: Streamlit前端主程序，包含完整的Web交互界面，
#       集成数据加载、3D卫星轨道可视化、Agent对话窗口、仿真结果展示
# 关键函数:
#   - load_data(): 加载AFSIM仿真输出数据（entity.csv, orbital.csv）
#   - ask_openclaw(): 通过subprocess调用OpenClaw Agent
#   - apply_apple_chart_style(): 应用Apple风格的Plotly图表样式配置
#   - render_plot_export(): 图表导出功能（PNG/SVG）
```

```python
# === 文件名: SKILL.md ===
# 行数: ~200
# 功能: OpenClaw技能定义文件，定义afsim-project技能的元数据、
#       工作流程、关键规则和可用工具
# 关键结构:
#   - YAML frontmatter: name, description, keywords
#   - 四步工作流: 写脚本→编译→调试→分析
#   - 13条关键规则
#   - 文件注入策略说明
```

```python
# === 文件名: analyze_leo_comm.py ===
# 行数: ~700
# 功能: 核心卫星通信仿真自动化脚本，封装从AFSIM安装发现到
#       仿真结果可视化的完整流程
# 关键函数:
#   - scan_for_afsim(): 三级递进扫描AFSIM安装路径
#   - compile_and_run(): 调用mission.exe编译执行场景脚本
#   - parse_links(): 正则解析EVT文件中的链路数据
#   - parse_constellation_log(): 解析星座仿真日志（切换事件、ISL数据）
#   - plot_analysis(): matplotlib生成四子图分析报告
```

```python
# === 文件名: pymystic.py ===
# 行数: ~600
# 功能: AFSIM AER二进制文件读取库，Schema驱动方式解析
#       仿真输出的AER格式数据
# 关键类:
#   - class Schema: 解析Schema定义，构建类型映射表
#   - class Reader: 逐条读取AER消息，解码为Python字典
#   - 支持类型: BasicType, List, Enum, Struct, Union
```

```python
# === 文件名: parse_evt_full.py ===
# 行数: ~500
# 功能: EVT事件文件全量提取与可视化工具，解析AFSIM输出的
#       事件日志，提取所有KEY=VALUE键值对，输出CSV
# 关键函数:
#   - time_to_seconds(): HH:MM:SS格式转浮点秒数
#   - extract_key_values(): 正则提取行内所有键值对
#   - detect_encoding(): 检测UTF-16/UTF-8编码
#   - 自动为每个数值列生成折线图
```

```markdown
# === 文件名: afsim_syntax.md ===
# 行数: ~200
# 功能: AFSIM语法参考手册（内部文档），汇总常用命令语法、
#       项目结构模板、事件输出配置、常见错误与解决方案
# 关键章节:
#   - 项目结构模板（main.txt, setup.txt, scenario laydown）
#   - Event Output配置
#   - Event Pipe配置
#   - 平台定义语法
#   - 常见错误对照表
```

```python
# === 文件名: lookup.py ===
# 行数: ~100
# 功能: AFSIM手册关键词检索工具，搜索reference_manual.txt
#       返回关键字前后各2000字符上下文（最多3个匹配）
# 关键函数:
#   - lookup(keyword, context_size=2000): 搜索并返回上下文

# === 文件名: index_manual.py ===
# 行数: ~200
# 功能: AFSIM手册索引构建工具，扫描手册中的命令标题
#       生成manual_index.json加速检索
# 关键函数:
#   - build_index(): 构建倒排索引
#   - save_index(): 持久化到JSON
```

```python
# === 文件名: afsim_bridge.py ===
# 行数: ~400
# 功能: 核心桥接模块，定义仿真配置数据结构，
#       封装AFSIM仿真调用接口
# 关键类:
#   - @dataclass SimConfig: 仿真配置（exe路径、工作目录、时长等）
#   - @dataclass Satellite: 卫星平台（轨道六要素）
#   - @dataclass GroundStation: 地面站（经纬度）
#   - @dataclass SimMessage: 平台间消息
```

```python
# === 文件名: backend.py ===
# 行数: ~80
# 功能: FastAPI后端服务，提供RESTful API接口
# 关键端点:
#   - POST /api/agent/chat: Agent对话接口
#   - GET /api/satellites: 获取卫星列表
#   - GET /api/simulation/status: 获取仿真状态
```

```python
# === 文件名: main.py ===
# 行数: ~200
# 功能: OpenClaw Agent测试脚本，验证连接、模型与Agent调用
# 关键函数:
#   - create_parser(): 命令行参数解析
#   - 支持remote/local两种连接模式
#   - 集成cmdop异常处理
```

**代码规模统计：**

| 文件 | 行数 | 功能分类 |
|------|------|----------|
| appnew.py | ~1000 | 前端展示 |
| SKILL.md | ~200 | Agent定义 |
| analyze_leo_comm.py | ~700 | 仿真核心 |
| pymystic.py | ~600 | 数据解析 |
| parse_evt_full.py | ~500 | 事件分析 |
| afsim_syntax.md | ~200 | 参考文档 |
| lookup.py / index_manual.py | ~300 | 手册工具 |
| afsim_bridge.py | ~400 | 桥接模块 |
| backend.py | ~80 | 后端服务 |
| main.py | ~200 | 测试脚本 |
| **合计** | **~4180** | — |
