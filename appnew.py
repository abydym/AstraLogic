import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import uuid
import subprocess
import json
import sys
import requests as http_requests  # 避免与已有 requests 冲突
import warnings
warnings.filterwarnings('ignore')

from conversation_manager import ConversationManager
from openclaw_status import OpenClawStatus

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="AstraLogic - 卫星通信仿真系统",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 数据加载函数 ====================
@st.cache_data
def load_data():
    """加载AFSIM仿真数据"""
    try:
        df_entity = pd.read_csv('output/entity.csv')
        df_orbital = pd.read_csv('output/orbital.csv')
        
        # 标记原始 NaN 速度（用于区分静止平台如地面站）
        df_entity['has_velocity'] = ~(
            df_entity['vx'].isna() & df_entity['vy'].isna() & df_entity['vz'].isna()
        )

        # 数据预处理（NaN 补零，便于计算）
        df_entity['vx'] = df_entity['vx'].fillna(0)
        df_entity['vy'] = df_entity['vy'].fillna(0)
        df_entity['vz'] = df_entity['vz'].fillna(0)
        
        # 计算额外字段
        df_entity['velocity_magnitude'] = np.sqrt(
            df_entity['vx']**2 + df_entity['vy']**2 + df_entity['vz']**2
        ) / 1000  # 转换为km/s
        
        # 计算所有平台对之间的距离
        platforms = sorted(df_entity['platformIndex'].unique())
        time_points = sorted(df_entity['simTime'].unique())
        distance_records = []
        
        for t in time_points:
            t_data = df_entity[df_entity['simTime'] == t]
            pair_dists = []
            for i in range(len(platforms)):
                for j in range(i + 1, len(platforms)):
                    p_i = t_data[t_data['platformIndex'] == platforms[i]]
                    p_j = t_data[t_data['platformIndex'] == platforms[j]]
                    if len(p_i) > 0 and len(p_j) > 0:
                        dx = p_i.iloc[0]['x'] - p_j.iloc[0]['x']
                        dy = p_i.iloc[0]['y'] - p_j.iloc[0]['y']
                        dz = p_i.iloc[0]['z'] - p_j.iloc[0]['z']
                        dist = np.sqrt(dx**2 + dy**2 + dz**2) / 1000
                        pair_dists.append(dist)
            if pair_dists:
                distance_records.append({
                    'simTime': t,
                    'avg_distance': np.mean(pair_dists),
                    'min_distance': np.min(pair_dists),
                    'max_distance': np.max(pair_dists),
                    'pair_distances': pair_dists
                })
        
        if distance_records:
            df_distance = pd.DataFrame(distance_records)
        else:
            df_distance = pd.DataFrame()
        
        return df_entity, df_orbital, df_distance
    
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return None, None, None

def render_plot_export(fig, filename_base, key_prefix):
    export_format = st.selectbox(
        "导出格式",
        ["png", "svg"],
        key=f"{key_prefix}_format"
    )
    mime = "image/png" if export_format == "png" else "image/svg+xml"

    try:
        image_bytes = fig.to_image(format=export_format, scale=2)
    except Exception as exc:
        st.error(f"图表导出失败: {exc}")
        return

    st.download_button(
        label="导出图表",
        data=image_bytes,
        file_name=f"{filename_base}.{export_format}",
        mime=mime,
        key=f"{key_prefix}_download"
    )

def apply_apple_chart_style(fig, dark=False):
    font_color = "#ffffff" if dark else "#1d1d1f"
    paper_bg = "#272729" if dark else "#f5f5f7"
    plot_bg = "#252527" if dark else "#ffffff"

    fig.update_layout(
        font=dict(
            family="SF Pro Text, system-ui, -apple-system, sans-serif",
            color=font_color
        ),
        paper_bgcolor=paper_bg,
        plot_bgcolor=plot_bg,
        title_font=dict(
            family="SF Pro Display, system-ui, -apple-system, sans-serif",
            size=20,
            color=font_color
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0.0)",
            bordercolor="rgba(0,0,0,0)"
        )
    )

# ─── Agent 对话辅助函数 ───
def ask_openclaw(message, session_id, gateway_url=None, token=None):
    """通过 HTTP API 或 CLI 发送消息给 agent，返回文字回复（非流式，兼容旧调用）"""
    return "".join(ask_openclaw_stream(message, session_id, gateway_url, token))


def ask_openclaw_stream(message, session_id, gateway_url=None, token=None):
    """流式生成器：通过 HTTP API (SSE) 或 CLI 发送消息。

    Yields 结构化事件字典：
      {"type": "content",    "text": "..."}       # 普通文本 token
      {"type": "tool_call",  "name": "...", "args": "..."}  # 工具调用开始
      {"type": "tool_result","name": "...", "result": "..."} # 工具返回结果
      {"type": "status",     "text": "..."}       # 状态/思考中
      {"type": "error",      "text": "..."}       # 错误
    """

    # ── 尝试 HTTP 流式 API ──
    if gateway_url:
        try:
            headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            payload = {
                "model": "openclaw/default",
                "messages": [{"role": "user", "content": message}],
                "stream": True,
            }
            if session_id:
                payload["user"] = session_id

            with http_requests.post(
                f"{gateway_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=300,
                stream=True,
            ) as resp:
                if resp.status_code != 200:
                    raise Exception(f"HTTP {resp.status_code}")

                # 跟踪活跃的工具调用（index -> name）
                active_tools = {}

                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        choices = chunk.get("choices", [])
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})

                        # ── 普通文本内容 ──
                        content = delta.get("content", "")
                        if content:
                            yield {"type": "content", "text": content}

                        # ── 工具调用 ──
                        tool_calls = delta.get("tool_calls", [])
                        for tc in tool_calls:
                            idx = tc.get("index", 0)
                            fn = tc.get("function", {})
                            fn_name = fn.get("name", "")
                            fn_args = fn.get("arguments", "")

                            if fn_name:
                                # 新工具调用开始
                                active_tools[idx] = fn_name
                                yield {"type": "tool_call", "name": fn_name, "args": fn_args}
                            elif fn_args and idx in active_tools:
                                # 工具参数持续拼接中
                                yield {"type": "status", "text": f"🔧 调用 {active_tools[idx]}({fn_args})"}

                        # ── reasoning / thinking 内容 ──
                        reasoning = delta.get("reasoning_content", "")
                        if reasoning:
                            yield {"type": "status", "text": f"💭 {reasoning[:80]}..."}

                    except json.JSONDecodeError:
                        continue

                return  # 流式成功，不走 CLI

        except Exception:
            # HTTP 流式失败，降级到 CLI
            pass

    # ── 回退：CLI 方式（非流式，一次性返回） ──
    yield {"type": "status", "text": "⏳ 通过 CLI 获取回复..."}
    cmd = "openclaw.cmd" if sys.platform == "win32" else "openclaw"
    try:
        result = subprocess.run(
            [cmd, "agent", "--session-id", session_id, "--message", message, "--json"],
            capture_output=True, timeout=300,
        )
        stdout = result.stdout.decode("utf-8", errors="replace").strip()
        stderr = result.stderr.decode("utf-8", errors="replace").strip()

        if result.returncode != 0:
            yield {"type": "error", "text": f"❌ CLI 错误 (code {result.returncode}): {(stderr or stdout)[:300]}"}
            return

        if not stdout:
            if stderr:
                yield {"type": "error", "text": f"❌ 会话异常: {stderr[:300]}"}
                return
            new_id = str(uuid.uuid4())
            st.session_state.agent_session_id = new_id
            yield {"type": "error", "text": "🔄 会话已过期，已自动重新创建。请重新发送你的问题。"}
            return

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            yield {"type": "error", "text": f"❌ CLI 返回异常: {(stdout[:300])}"}
            return

        payloads = data.get("result", {}).get("payloads", [])
        if payloads:
            yield {"type": "content", "text": payloads[0].get("text", "(no text)")}
        else:
            yield {"type": "content", "text": json.dumps(data, ensure_ascii=False, indent=2)}

    except subprocess.TimeoutExpired:
        yield {"type": "error", "text": "⏳ 请求超时，请重试"}
    except FileNotFoundError:
        yield {"type": "error", "text": "❌ 找不到 `openclaw` 命令，确保已安装且在 PATH 中"}

# ==================== 初始化会话状态 ====================
if 'running' not in st.session_state:
    st.session_state.running = False
if 'sim_time' not in st.session_state:
    st.session_state.sim_time = 0.0
if 'selected_platforms' not in st.session_state:
    st.session_state.selected_platforms = [1, 2, 3]
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'agent_session_id' not in st.session_state:
    st.session_state.agent_session_id = str(uuid.uuid4())

# ==================== 自定义样式 ====================
st.markdown("""
<style>
    :root {
        --apple-primary: #0066cc;
        --apple-primary-focus: #0071e3;
        --apple-ink: #1d1d1f;
        --apple-ink-muted: #7a7a7a;
        --apple-canvas: #ffffff;
        --apple-parchment: #f5f5f7;
        --apple-pearl: #fafafc;
        --apple-hairline: #e0e0e0;
        --apple-divider: #f0f0f0;
        --apple-surface-black: #000000;
    }

    html, body, [class*="stApp"] {
        font-family: "SF Pro Text", system-ui, -apple-system, sans-serif;
        color: var(--apple-ink);
        background-color: var(--apple-parchment);
    }

    .block-container {
        padding-top: 48px;
        padding-bottom: 80px;
        max-width: 1200px;
    }

    .main-header {
        background: var(--apple-canvas);
        border: 1px solid var(--apple-hairline);
        padding: 80px 64px;
        border-radius: 18px;
        margin-bottom: 48px;
    }

    .main-header h1 {
        font-family: "SF Pro Display", system-ui, -apple-system, sans-serif;
        font-size: 56px;
        line-height: 1.07;
        letter-spacing: -0.28px;
        font-weight: 600;
        color: var(--apple-ink);
        margin: 0 0 12px 0;
    }

    .main-header p {
        font-family: "SF Pro Display", system-ui, -apple-system, sans-serif;
        font-size: 21px;
        line-height: 1.19;
        letter-spacing: 0.231px;
        color: var(--apple-ink-muted);
        margin: 0;
    }

    [data-testid="stSidebar"] {
        background: var(--apple-canvas);
        border-right: 1px solid var(--apple-hairline);
    }

    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: var(--apple-ink);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        white-space: pre-wrap;
        background-color: var(--apple-canvas);
        border-radius: 9999px;
        border: 1px solid var(--apple-hairline);
        color: var(--apple-ink);
        font-weight: 400;
        font-size: 14px;
        padding: 0 18px;
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--apple-primary);
        color: var(--apple-canvas);
        border-color: var(--apple-primary);
    }

    .custom-divider {
        height: 1px;
        background: var(--apple-hairline);
        margin: 48px 0;
    }

    .stButton > button {
        background: var(--apple-primary);
        color: var(--apple-canvas);
        border-radius: 9999px;
        border: none;
        padding: 11px 22px;
        font-size: 17px;
        font-weight: 400;
        letter-spacing: -0.374px;
    }

    .stButton > button:focus-visible {
        outline: 2px solid var(--apple-primary-focus);
        outline-offset: 2px;
    }

    [data-testid="stMetric"] {
        background: var(--apple-canvas);
        border: 1px solid var(--apple-hairline);
        padding: 20px 24px;
        border-radius: 18px;
    }

    [data-testid="stMetric"] label {
        font-size: 14px;
        letter-spacing: -0.224px;
        color: var(--apple-ink-muted);
    }

    [data-testid="stMetric"] div {
        color: var(--apple-ink);
    }

    .stDataFrame {
        border: 1px solid var(--apple-hairline);
        border-radius: 18px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 加载数据 ====================
df_entity, df_orbital, df_distance = load_data()

# ==================== 侧边栏 ====================
with st.sidebar:
    # ── Gateway 配置面板 ──
    st.markdown("### 🔗 Gateway 配置")

    # Gateway 地址
    gateway_url = st.text_input(
        "Gateway 地址",
        value=st.session_state.get("gateway_url", "http://127.0.0.1:18789"),
        key="gateway_url_input",
        help="OpenClaw Gateway 的 HTTP 地址"
    )
    st.session_state.gateway_url = gateway_url

    # Token 输入
    gateway_token = st.text_input(
        "Token",
        value=st.session_state.get("gateway_token", ""),
        type="password",
        key="gateway_token_input",
        help="Gateway 认证 Token（在 openclaw.json 的 gateway.auth.token 中配置）"
    )
    st.session_state.gateway_token = gateway_token

    # 测试连接按钮
    if st.button("🔌 测试连接", key="test_gateway_conn"):
        with st.spinner("检测中..."):
            ocs = OpenClawStatus()
            status = ocs.quick_status(
                gateway_url=gateway_url,
                token=gateway_token if gateway_token else None
            )
            st.session_state.gateway_status = status

    # 显示状态
    _gw_status = st.session_state.get("gateway_status")
    if _gw_status:
        overall = _gw_status.get("overall", "unknown")
        emoji = OpenClawStatus.status_emoji(overall)
        st.markdown(f"**状态:** {emoji} {overall.upper()}")
        if _gw_status.get("gateway_latency_ms", -1) > 0:
            st.caption(f"端口延迟: {_gw_status['gateway_latency_ms']}ms")
        if _gw_status.get("api_latency_ms", -1) > 0:
            st.caption(f"API 延迟: {_gw_status['api_latency_ms']}ms")
        if _gw_status.get("models"):
            st.caption(f"模型: {', '.join(_gw_status['models'][:3])}")

    st.caption("🔒 Token 仅存于浏览器会话中，不会写入代码文件")
    st.markdown("---")

    # ── 原有侧边栏内容 ──
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h2 style="margin-bottom: 0.5rem; font-family: 'SF Pro Display', system-ui, -apple-system, sans-serif;">🛰️ AstraLogic 控制台</h2>
        <p style="color: #7a7a7a;">卫星通信仿真系统</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # 数据状态指示器
    if df_entity is not None:
        st.success(f"✅ 数据已加载: {len(df_entity)} 条记录")
    else:
        st.error("❌ 数据加载失败")
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # 平台选择
    st.subheader("📡 卫星平台选择")
    
    platform_options = {
        1: "卫星1 (LEO-1)",
        2: "卫星2 (LEO-2)",
        3: "地面站 (Ground)"
    }
    
    selected_platforms = st.multiselect(
        "选择要显示的平台",
        options=list(platform_options.keys()),
        default=[1, 2, 3],
        format_func=lambda x: platform_options.get(x, f"平台 {x}")
    )
    
    st.session_state.selected_platforms = selected_platforms
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # 仿真时间控制
    st.subheader("⏱️ 仿真时间控制")
    
    if df_entity is not None:
        max_time = df_entity['simTime'].max()
        min_time = df_entity['simTime'].min()
        
        time_range = st.slider(
            "选择时间范围 (秒)",
            min_value=min_time,
            max_value=max_time,
            value=(min_time, max_time),
            step=10.0
        )
        
        # 当前时间点
        current_time = st.slider(
            "当前时间点 (秒)",
            min_value=time_range[0],
            max_value=time_range[1],
            value=time_range[0],
            step=10.0
        )
        
        st.session_state.sim_time = current_time
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # 可视化控制
    st.subheader("🎨 可视化设置")
    
    show_earth = st.checkbox("显示地球参考", value=True)
    show_comm_links = st.checkbox("显示通信链路", value=True)
    show_velocity_vectors = st.checkbox("显示速度矢量", value=False)
    
    color_scheme = st.selectbox(
        "颜色方案",
        ["默认", "科学", "对比", "暖色", "冷色"]
    )
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # 系统控制
    st.subheader("▶️ 仿真控制")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶ 开始仿真", width='stretch', type="primary"):
            st.session_state.running = True
    
    with col2:
        if st.button("⏹ 停止仿真", width='stretch'):
            st.session_state.running = False
    
    # 仿真状态
    if st.session_state.running:
        st.success("🟢 仿真运行中")
    else:
        st.warning("🔴 仿真已停止")
    
    # 实时指标
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    st.subheader("📊 实时指标")
    
    if df_entity is not None:
        current_data = df_entity[df_entity['simTime'] == current_time]
        
        for platform in selected_platforms:
            platform_data = current_data[current_data['platformIndex'] == platform]
            
            if len(platform_data) > 0:
                p_data = platform_data.iloc[0]
                
                # 计算指标
                velocity = p_data['velocity_magnitude']
                altitude = np.sqrt(p_data['x']**2 + p_data['y']**2 + p_data['z']**2) / 1000 - 6371  # km
                
                st.metric(
                    label=f"平台 {platform}",
                    value=f"{velocity:.2f} km/s",
                    delta=f"高度: {altitude:.1f} km"
                )

# ==================== 主界面 ====================
# 头部
st.markdown("""
<div class="main-header">
    <h1>🛰️ AstraLogic 卫星通信仿真系统</h1>
    <p>
        基于 Agent + MCP + AFSIM 的智能卫星通信仿真平台 · 数据时间范围: {min_time} - {max_time} 秒
    </p>
</div>
""".format(
    min_time=df_entity['simTime'].min() if df_entity is not None else 0,
    max_time=df_entity['simTime'].max() if df_entity is not None else 0
), unsafe_allow_html=True)

# 顶部指标卡
col1, col2, col3, col4 = st.columns(4)

if df_entity is not None:
    # 获取当前时间的数据
    current_data = df_entity[df_entity['simTime'] == current_time]
    
    # 计算指标
    total_platforms = len(selected_platforms)
    
    # 平均速度：只统计有实际速度数据的运动平台（排除地面站等静止平台）
    valid_velocity = current_data[
        (current_data['platformIndex'].isin(selected_platforms)) &
        (current_data['has_velocity'] == True)
    ]['velocity_magnitude']
    avg_velocity = valid_velocity.mean() if len(valid_velocity) > 0 else 0
    
    # 卫星间距离：使用所有平台对的平均距离
    max_comm_range = 10000  # 10000 km
    if df_distance is not None and len(df_distance) > 0 and current_time in df_distance['simTime'].values:
        current_row = df_distance[df_distance['simTime'] == current_time].iloc[0]
        current_distance = current_row['avg_distance']
        # 通信覆盖率：当前时刻所有平台对中，距离在通信范围内的比例
        pair_dists = current_row['pair_distances']
        coverage_ratio = sum(1 for d in pair_dists if d <= max_comm_range) / len(pair_dists) * 100
    else:
        current_distance = 0
        coverage_ratio = 0
    
    with col1:
        st.metric(
            label="📡 活跃平台",
            value=f"{total_platforms}",
            delta=f"当前时间: {current_time:.1f} 秒"
        )
    
    with col2:
        st.metric(
            label="🚀 平均速度",
            value=f"{avg_velocity:.2f} km/s",
            delta="LEO轨道速度 (~7.8 km/s)"
        )
    
    with col3:
        st.metric(
            label="📶 通信距离",
            value=f"{current_distance:.1f} km",
            delta=f"最大范围: {max_comm_range} km"
        )
    
    with col4:
        st.metric(
            label="📊 通信覆盖率",
            value=f"{coverage_ratio:.1f}%",
            delta="在最大通信范围内"
        )

# 分隔线
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# 主要内容标签页
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌐 3D轨道可视化", 
    "📊 数据分析", 
    "🤖 Agent对话",
    "📋 仿真日志",
    "📈 详细报告"
])

# ==================== Tab 1: 3D轨道可视化 ====================
with tab1:
    st.subheader("卫星轨道3D可视化")
    
    if df_entity is not None:
        # 创建3D图表
        fig_3d = go.Figure()
        
        # 颜色方案
        colors = {
            1: '#1f77b4',  # 蓝色
            2: '#ff7f0e',  # 橙色
            3: '#2ca02c',  # 绿色
        }
        
        # 为每个平台绘制轨迹
        for platform in selected_platforms:
            platform_data = df_entity[
                (df_entity['platformIndex'] == platform) & 
                (df_entity['simTime'] >= time_range[0]) & 
                (df_entity['simTime'] <= time_range[1])
            ].sort_values('simTime')
            
            if len(platform_data) > 0:
                # 轨迹线
                fig_3d.add_trace(go.Scatter3d(
                    x=platform_data['x'] / 1000,  # 转换为km
                    y=platform_data['y'] / 1000,
                    z=platform_data['z'] / 1000,
                    mode='lines',
                    name=f'平台 {platform} 轨迹',
                    line=dict(
                        color=colors.get(platform, '#666'),
                        width=3,
                        dash='solid'
                    ),
                    legendgroup=f'platform_{platform}',
                    showlegend=True
                ))
                
                # 当前时间点位置
                current_point = platform_data[platform_data['simTime'] == current_time]
                
                if len(current_point) > 0:
                    point = current_point.iloc[0]
                    
                    fig_3d.add_trace(go.Scatter3d(
                        x=[point['x'] / 1000],
                        y=[point['y'] / 1000],
                        z=[point['z'] / 1000],
                        mode='markers+text',
                        name=f'平台 {platform} 当前位置',
                        marker=dict(
                            size=10,
                            color=colors.get(platform, '#666'),
                            symbol='circle',
                            line=dict(color='black', width=2)
                        ),
                        text=[f'P{platform}'],
                        textposition='top center',
                        textfont=dict(size=12, color='black'),
                        legendgroup=f'platform_{platform}',
                        showlegend=False
                    ))
                    
                    # 速度矢量
                    if show_velocity_vectors and not np.isnan(point['vx']):
                        fig_3d.add_trace(go.Scatter3d(
                            x=[point['x']/1000, (point['x'] + point['vx']*100)/1000],
                            y=[point['y']/1000, (point['y'] + point['vy']*100)/1000],
                            z=[point['z']/1000, (point['z'] + point['vz']*100)/1000],
                            mode='lines',
                            name=f'平台 {platform} 速度矢量',
                            line=dict(
                                color='red',
                                width=2,
                                dash='dash'
                            ),
                            legendgroup=f'velocity_{platform}',
                            showlegend=True
                        ))
        
        # 添加通信链路
        if show_comm_links and len(selected_platforms) >= 2:
            for i in range(len(selected_platforms)):
                for j in range(i + 1, len(selected_platforms)):
                    p1 = selected_platforms[i]
                    p2 = selected_platforms[j]
                    
                    # 获取当前时间点的数据
                    p1_data = df_entity[
                        (df_entity['platformIndex'] == p1) & 
                        (df_entity['simTime'] == current_time)
                    ]
                    p2_data = df_entity[
                        (df_entity['platformIndex'] == p2) & 
                        (df_entity['simTime'] == current_time)
                    ]
                    
                    if len(p1_data) > 0 and len(p2_data) > 0:
                        p1_pos = p1_data.iloc[0]
                        p2_pos = p2_data.iloc[0]
                        
                        # 计算距离
                        dist = np.sqrt(
                            (p1_pos['x'] - p2_pos['x'])**2 +
                            (p1_pos['y'] - p2_pos['y'])**2 +
                            (p1_pos['z'] - p2_pos['z'])**2
                        ) / 1000
                        
                        # 根据距离设置颜色
                        if dist > 10000:
                            link_color = 'red'
                            link_dash = 'dot'
                        elif dist > 5000:
                            link_color = 'orange'
                            link_dash = 'dash'
                        else:
                            link_color = 'green'
                            link_dash = 'solid'
                        
                        # 绘制链路
                        fig_3d.add_trace(go.Scatter3d(
                            x=[p1_pos['x']/1000, p2_pos['x']/1000],
                            y=[p1_pos['y']/1000, p2_pos['y']/1000],
                            z=[p1_pos['z']/1000, p2_pos['z']/1000],
                            mode='lines',
                            name=f'通信链路 {p1}-{p2} ({dist:.1f}km)',
                            line=dict(
                                color=link_color,
                                width=3,
                                dash=link_dash
                            ),
                            legendgroup='comm_links',
                            showlegend=True
                        ))
        
        # 添加地球
        if show_earth:
            u = np.linspace(0, 2 * np.pi, 50)
            v = np.linspace(0, np.pi, 50)
            
            earth_radius = 6371  # km
            x_earth = earth_radius * np.outer(np.cos(u), np.sin(v))
            y_earth = earth_radius * np.outer(np.sin(u), np.sin(v))
            z_earth = earth_radius * np.outer(np.ones(np.size(u)), np.cos(v))
            
            fig_3d.add_trace(go.Surface(
                x=x_earth,
                y=y_earth,
                z=z_earth,
                colorscale='Blues',
                opacity=0.3,
                showscale=False,
                name='地球'
            ))
        
        # 更新布局
        fig_3d.update_layout(
            title=dict(
                text='卫星轨道3D可视化',
                font=dict(size=20, color='#1a1a2e'),
                x=0.5
            ),
            scene=dict(
                xaxis_title='X (km)',
                yaxis_title='Y (km)',
                zaxis_title='Z (km)',
                aspectmode='data',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.0),
                    up=dict(x=0, y=0, z=1)
                ),
                xaxis=dict(
                    backgroundcolor="rgb(255, 255, 255)",
                    gridcolor="#e0e0e0",
                    showbackground=True,
                    zerolinecolor="#e0e0e0"
                ),
                yaxis=dict(
                    backgroundcolor="rgb(255, 255, 255)",
                    gridcolor="#e0e0e0",
                    showbackground=True,
                    zerolinecolor="#e0e0e0"
                ),
                zaxis=dict(
                    backgroundcolor="rgb(255, 255, 255)",
                    gridcolor="#e0e0e0",
                    showbackground=True,
                    zerolinecolor="#e0e0e0"
                )
            ),
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor='rgba(255,255,255,0.0)',
                bordercolor='rgba(0,0,0,0)',
                borderwidth=0
            ),
            height=700,
            margin=dict(l=0, r=0, t=50, b=0)
        )
        apply_apple_chart_style(fig_3d)
        
        # 添加控件
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.plotly_chart(fig_3d, width='stretch')
        
        with col2:
            st.subheader("3D视图控制")
            
            # 视角预设
            view_preset = st.selectbox(
                "预设视角",
                ["正面视角", "侧面视角", "顶部视角", "自定义视角"]
            )
            
            if view_preset == "正面视角":
                fig_3d.update_layout(
                    scene=dict(camera=dict(eye=dict(x=1.5, y=0.5, z=0.5)))
                )
            elif view_preset == "侧面视角":
                fig_3d.update_layout(
                    scene=dict(camera=dict(eye=dict(x=0.5, y=1.5, z=0.5)))
                )
            elif view_preset == "顶部视角":
                fig_3d.update_layout(
                    scene=dict(camera=dict(eye=dict(x=0.0, y=0.0, z=2.0)))
                )

            st.markdown("---")
            st.subheader("图表导出")
            render_plot_export(fig_3d, "orbit_3d", "orbit3d")
            
            # 显示统计信息
            st.markdown("---")
            st.subheader("当前视图统计")
            
            if df_entity is not None:
                for platform in selected_platforms:
                    platform_data = df_entity[
                        (df_entity['platformIndex'] == platform) & 
                        (df_entity['simTime'] == current_time)
                    ]
                    
                    if len(platform_data) > 0:
                        p_data = platform_data.iloc[0]
                        
                        st.markdown(f"""
                        **平台 {platform}:**
                        - 位置: ({p_data['x']/1000:.1f}, {p_data['y']/1000:.1f}, {p_data['z']/1000:.1f}) km
                        - 速度: {np.sqrt(p_data['vx']**2 + p_data['vy']**2 + p_data['vz']**2)/1000:.2f} km/s
                        - 高度: {np.sqrt(p_data['x']**2 + p_data['y']**2 + p_data['z']**2)/1000 - 6371:.1f} km
                        """)
    
    else:
        st.warning("无法加载卫星数据，请检查数据文件路径")

# ==================== Tab 2: 数据分析 ====================
with tab2:
    st.subheader("仿真数据分析")
    
    if df_entity is not None:
        # 创建分析图表
        analysis_tab1, analysis_tab2, analysis_tab3, analysis_tab4 = st.tabs([
            "📍 位置分析", 
            "🚀 速度分析", 
            "📡 距离分析",
            "📈 轨道参数"
        ])
        
        with analysis_tab1:
            st.markdown("**卫星位置坐标变化**")

            fig_pos = make_subplots(
                rows=1,
                cols=3,
                subplot_titles=("X坐标变化", "Y坐标变化", "Z坐标变化")
            )

            for platform in selected_platforms:
                platform_data = df_entity[df_entity['platformIndex'] == platform]

                if len(platform_data) > 0:
                    fig_pos.add_trace(
                        go.Scatter(
                            x=platform_data['simTime'],
                            y=platform_data['x'] / 1000,
                            mode='lines',
                            name=f'平台 {platform}'
                        ),
                        row=1, col=1
                    )

                    fig_pos.add_trace(
                        go.Scatter(
                            x=platform_data['simTime'],
                            y=platform_data['y'] / 1000,
                            mode='lines',
                            name=f'平台 {platform}',
                            showlegend=False
                        ),
                        row=1, col=2
                    )

                    fig_pos.add_trace(
                        go.Scatter(
                            x=platform_data['simTime'],
                            y=platform_data['z'] / 1000,
                            mode='lines',
                            name=f'平台 {platform}',
                            showlegend=False
                        ),
                        row=1, col=3
                    )

            fig_pos.update_xaxes(title_text='仿真时间 (秒)', row=1, col=1, showgrid=True)
            fig_pos.update_xaxes(title_text='仿真时间 (秒)', row=1, col=2, showgrid=True)
            fig_pos.update_xaxes(title_text='仿真时间 (秒)', row=1, col=3, showgrid=True)
            fig_pos.update_yaxes(title_text='X坐标 (km)', row=1, col=1, showgrid=True)
            fig_pos.update_yaxes(title_text='Y坐标 (km)', row=1, col=2, showgrid=True)
            fig_pos.update_yaxes(title_text='Z坐标 (km)', row=1, col=3, showgrid=True)
            fig_pos.update_layout(height=450, legend=dict(x=0.02, y=0.98))
            apply_apple_chart_style(fig_pos)

            st.plotly_chart(fig_pos, width='stretch')
            render_plot_export(fig_pos, "position_timeseries", "pos_timeseries")
        
        with analysis_tab2:
            st.markdown("**卫星速度分析**")
            
            fig_vel = go.Figure()
            
            for platform in selected_platforms:
                platform_data = df_entity[df_entity['platformIndex'] == platform]
                
                if len(platform_data) > 0:
                    fig_vel.add_trace(go.Scatter(
                        x=platform_data['simTime'],
                        y=platform_data['velocity_magnitude'],
                        mode='lines+markers',
                        name=f'平台 {platform}',
                        line=dict(width=2),
                        marker=dict(size=4)
                    ))
            
            # 添加参考线
            fig_vel.add_hline(y=7.8, line_dash="dash", line_color="green",
                             annotation_text="LEO轨道速度 (~7.8 km/s)")
            fig_vel.add_hline(y=3.07, line_dash="dash", line_color="orange",
                             annotation_text="GEO轨道速度 (~3.07 km/s)")
            
            fig_vel.update_layout(
                title='卫星速度大小随时间变化',
                xaxis_title='仿真时间 (秒)',
                yaxis_title='速度大小 (km/s)',
                height=500,
                showlegend=True,
                legend=dict(x=0.02, y=0.98)
            )
            apply_apple_chart_style(fig_vel)
            
            st.plotly_chart(fig_vel, width='stretch')
            render_plot_export(fig_vel, "velocity_timeseries", "vel_timeseries")
        
        with analysis_tab3:
            st.markdown("**卫星间距离分析**")
            
            if df_distance is not None and len(df_distance) > 0:
                fig_dist = go.Figure()
                
                fig_dist.add_trace(go.Scatter(
                    x=df_distance['simTime'],
                    y=df_distance['avg_distance'],
                    mode='lines+markers',
                    name='平均距离',
                    line=dict(color='purple', width=3),
                    marker=dict(size=4)
                ))
                
                fig_dist.add_trace(go.Scatter(
                    x=df_distance['simTime'],
                    y=df_distance['min_distance'],
                    mode='lines',
                    name='最小距离',
                    line=dict(color='green', width=1, dash='dot')
                ))
                
                fig_dist.add_trace(go.Scatter(
                    x=df_distance['simTime'],
                    y=df_distance['max_distance'],
                    mode='lines',
                    name='最大距离',
                    line=dict(color='orange', width=1, dash='dot')
                ))
                
                # 添加通信阈值线
                max_comm_range = 10000  # 10000 km
                fig_dist.add_hline(y=max_comm_range, line_dash="dash", line_color="red",
                                  annotation_text="最大通信距离")
                
                y_max = max(df_distance['max_distance'].max(), max_comm_range) * 1.1
                fig_dist.update_layout(
                    title='卫星间距离随时间变化（通信链路评估）',
                    xaxis_title='仿真时间 (秒)',
                    yaxis_title='距离 (km)',
                    height=500,
                    showlegend=True,
                    yaxis=dict(range=[0, y_max])
                )
                apply_apple_chart_style(fig_dist)
                
                st.plotly_chart(fig_dist, width='stretch')
                render_plot_export(fig_dist, "distance_timeseries", "dist_timeseries")
                
                # 距离统计
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    min_dist = df_distance['min_distance'].min()
                    st.metric("全局最小距离", f"{min_dist:.1f} km")
                
                with col2:
                    max_dist = df_distance['max_distance'].max()
                    st.metric("全局最大距离", f"{max_dist:.1f} km")
                
                with col3:
                    avg_dist = df_distance['avg_distance'].mean()
                    st.metric("全局平均距离", f"{avg_dist:.1f} km")
            
            else:
                st.warning("无法计算卫星间距离")
        
        with analysis_tab4:
            st.markdown("**轨道参数分析**")
            
            if df_orbital is not None:
                # 轨道参数时间序列
                fig_orbital = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=('半长轴', '偏心率', '轨道倾角', '升交点赤经')
                )
                
                for platform in selected_platforms:
                    platform_orbital = df_orbital[df_orbital['platformIndex'] == platform]
                    
                    if len(platform_orbital) > 0:
                        # 半长轴（转换为km）
                        fig_orbital.add_trace(go.Scatter(
                            x=platform_orbital['simTime'],
                            y=platform_orbital['semiMajorAxis'] / 1000,
                            name=f'平台 {platform}',
                            mode='lines+markers'
                        ), row=1, col=1)
                        
                        # 偏心率
                        fig_orbital.add_trace(go.Scatter(
                            x=platform_orbital['simTime'],
                            y=platform_orbital['eccentricity'],
                            name=f'平台 {platform}',
                            mode='lines+markers',
                            showlegend=False
                        ), row=1, col=2)
                        
                        # 轨道倾角（转换为度）
                        fig_orbital.add_trace(go.Scatter(
                            x=platform_orbital['simTime'],
                            y=np.degrees(platform_orbital['inclination']),
                            name=f'平台 {platform}',
                            mode='lines+markers',
                            showlegend=False
                        ), row=2, col=1)
                        
                        # 升交点赤经（转换为度）
                        fig_orbital.add_trace(go.Scatter(
                            x=platform_orbital['simTime'],
                            y=np.degrees(platform_orbital['raan']),
                            name=f'平台 {platform}',
                            mode='lines+markers',
                            showlegend=False
                        ), row=2, col=2)
                
                fig_orbital.update_layout(height=600, title_text="轨道根数时间序列")
                apply_apple_chart_style(fig_orbital)
                st.plotly_chart(fig_orbital, width='stretch')
                render_plot_export(fig_orbital, "orbital_params", "orbital_params")
            
            else:
                st.warning("无法加载轨道参数数据")
    
    else:
        st.warning("无法加载卫星数据，请检查数据文件路径")

# ==================== Tab 3: Agent对话 ====================

def _ensure_default_conversation(cm):
    """确保至少有一个会话，返回当前会话 ID 和 openclaw_session_id。"""
    convs = cm.list_conversations()
    if convs:
        return convs[0]["id"], convs[0]["openclaw_session_id"]
    # 没有任何会话，自动创建一个
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    oc_sid = str(uuid.uuid4())
    cid = cm.create_conversation(f"新对话 {now_str}", oc_sid)
    return cid, oc_sid


def _load_messages_to_state(cm, conversation_id):
    """从 SQLite 加载消息到 session_state.messages。"""
    try:
        msgs = cm.get_messages(conversation_id)
        st.session_state.messages = [
            {"role": m["role"], "content": m["content"]} for m in msgs
        ]
    except Exception as e:
        st.error(f"加载消息失败: {e}")
        st.session_state.messages = []


with tab3:
    st.markdown("""
    <style>
    /* 隐藏 Streamlit 页脚，让聊天输入框不被打扰 */
    footer, .stApp footer { display: none !important; }
    section[data-testid="stBottom"] > div:first-child { padding-bottom: 0; }
    /* 页面底部区块隐藏 */
    .main > div:last-child .stMarkdown:last-child { display: none; }
    </style>
    """, unsafe_allow_html=True)

    # ── 初始化会话管理器和 OpenClaw 状态 ──
    try:
        cm = ConversationManager()
    except Exception as e:
        st.error(f"会话管理器初始化失败: {e}")
        cm = None

    try:
        ocs = OpenClawStatus()
    except Exception as e:
        ocs = None

    # ── 确保有默认会话 ──
    if cm is not None:
        if "current_conversation_id" not in st.session_state or not st.session_state.current_conversation_id:
            try:
                cid, oc_sid = _ensure_default_conversation(cm)
                st.session_state.current_conversation_id = cid
                st.session_state.agent_session_id = oc_sid
                _load_messages_to_state(cm, cid)
            except Exception as e:
                st.error(f"初始化默认会话失败: {e}")

    # ── 侧边栏：会话管理 ──
    with st.sidebar:
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.subheader("💬 会话管理")

        if cm is not None:
            # 新建会话按钮
            if st.button("➕ 新建会话", key="sidebar_new_conv", width='stretch'):
                try:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    oc_sid = str(uuid.uuid4())
                    new_cid = cm.create_conversation(f"新对话 {now_str}", oc_sid)
                    st.session_state.current_conversation_id = new_cid
                    st.session_state.agent_session_id = oc_sid
                    st.session_state.messages = []
                    st.rerun()
                except Exception as e:
                    st.error(f"创建会话失败: {e}")

            st.markdown("---")

            # 会话列表
            try:
                convs = cm.list_conversations()
                if convs:
                    conv_options = {}
                    conv_labels = []
                    for c in convs:
                        label = f"{c['title']} ({c['message_count']}条消息)"
                        conv_options[label] = c["id"]
                        conv_labels.append(label)

                    current_cid = st.session_state.get("current_conversation_id", "")
                    # 找到当前选中的索引
                    current_idx = 0
                    for i, c in enumerate(convs):
                        if c["id"] == current_cid:
                            current_idx = i
                            break

                    selected_label = st.radio(
                        "会话列表",
                        options=conv_labels,
                        index=current_idx,
                        key="conv_radio",
                        label_visibility="collapsed",
                    )
                    selected_cid = conv_options[selected_label]

                    # 切换会话
                    if selected_cid != st.session_state.get("current_conversation_id"):
                        st.session_state.current_conversation_id = selected_cid
                        # 获取该会话的 openclaw_session_id
                        try:
                            conv_info = cm.get_conversation(selected_cid)
                            st.session_state.agent_session_id = conv_info["openclaw_session_id"]
                        except Exception:
                            pass
                        _load_messages_to_state(cm, selected_cid)
                        st.rerun()
                else:
                    st.caption("暂无会话")
            except Exception as e:
                st.error(f"加载会话列表失败: {e}")

            st.markdown("---")

            # 重命名和删除按钮
            current_cid = st.session_state.get("current_conversation_id")
            if current_cid:
                col_rename, col_delete = st.columns(2)

                with col_rename:
                    if st.button("✏️ 重命名", key="btn_rename_conv", width='stretch'):
                        st.session_state.show_rename_input = True

                with col_delete:
                    if st.button("🗑️ 删除", key="btn_delete_conv", width='stretch'):
                        st.session_state.show_delete_confirm = True

                # 重命名输入框
                if st.session_state.get("show_rename_input"):
                    new_name = st.text_input("新会话标题", key="rename_input_text")
                    col_ok, col_cancel = st.columns(2)
                    with col_ok:
                        if st.button("✅ 确认", key="btn_rename_ok"):
                            if new_name.strip():
                                try:
                                    cm.rename_conversation(current_cid, new_name.strip())
                                    st.session_state.show_rename_input = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"重命名失败: {e}")
                    with col_cancel:
                        if st.button("❌ 取消", key="btn_rename_cancel"):
                            st.session_state.show_rename_input = False
                            st.rerun()

                # 删除确认
                if st.session_state.get("show_delete_confirm"):
                    st.warning("⚠️ 确定要删除此会话吗？所有消息将被永久删除。")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("🗑️ 确认删除", key="btn_delete_yes"):
                            try:
                                cm.delete_conversation(current_cid)
                                st.session_state.show_delete_confirm = False
                                st.session_state.current_conversation_id = ""
                                st.session_state.messages = []
                                st.rerun()
                            except Exception as e:
                                st.error(f"删除失败: {e}")
                    with col_no:
                        if st.button("↩️ 取消", key="btn_delete_no"):
                            st.session_state.show_delete_confirm = False
                            st.rerun()

        else:
            st.warning("会话管理不可用")

        # ── 侧边栏：OpenClaw 状态面板 ──
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.subheader("🔗 OpenClaw 状态")

        if ocs is not None:
            # 刷新按钮
            if st.button("🔄 刷新状态", key="btn_refresh_oc_status"):
                st.session_state.pop("openclaw_status", None)
                st.rerun()

            # 使用缓存或检测（使用 quick_status，纯 HTTP，不调 CLI）
            if "openclaw_status" not in st.session_state:
                with st.spinner("正在检测 OpenClaw 状态..."):
                    try:
                        st.session_state.openclaw_status = ocs.quick_status(
                            gateway_url=st.session_state.get("gateway_url", "http://127.0.0.1:18789"),
                            token=st.session_state.get("gateway_token") or None,
                        )
                    except Exception as e:
                        st.session_state.openclaw_status = {
                            "overall": "offline",
                            "models": [],
                            "gateway_latency_ms": -1,
                            "api_latency_ms": -1,
                            "error": str(e),
                        }

            oc_status = st.session_state.openclaw_status
            overall = oc_status.get("overall", "unknown")
            emoji = OpenClawStatus.status_emoji(overall)
            models = oc_status.get("models", [])
            model_name = models[0] if models else "N/A"
            gw_latency = oc_status.get("gateway_latency_ms", -1)
            api_latency = oc_status.get("api_latency_ms", -1)
            latency_display = f"{gw_latency}ms" if gw_latency > 0 else "N/A"

            status_map = {"online": "在线", "api_offline": "API离线", "degraded": "降级", "offline": "离线"}
            status_text = status_map.get(overall, "未知")

            st.markdown(f"""
            **Gateway:** {emoji} {status_text}
            **模型:** `{model_name}`
            **端口延迟:** {latency_display}
            """)
            if api_latency > 0:
                st.caption(f"API 延迟: {api_latency}ms")
        else:
            st.warning("OpenClaw 状态检测不可用")

    # ── 主区域标题 ──
    st.subheader("🤖 Agent 智能助手")
    st.markdown("与 OpenClaw Agent 对话，让 AI 帮你分析和优化通信链路")

    # ── 可滚动聊天历史 ──
    msg_container = st.container(height=380)
    with msg_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # ── 输入框 ──
    if prompt := st.chat_input("输入你的问题..."):
        # 确保有会话
        current_cid = st.session_state.get("current_conversation_id")
        if not current_cid or cm is None:
            st.error("会话未初始化，请刷新页面")
            st.stop()

        # 1. 用户消息存入 SQLite
        try:
            cm.add_message(current_cid, "user", prompt)
        except Exception as e:
            st.error(f"保存用户消息失败: {e}")

        # 立即显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. 流式调用 agent，实时显示回复
        with st.chat_message("assistant"):
            start_time = time.time()
            full_response = ""
            tool_status_slot = st.empty()
            content_slot = st.empty()

            # 加载中提示（第一个 token 到达后自动消失）
            with content_slot.container():
                with st.spinner("正在连接 OpenClaw..."):
                    pass  # spinner 会在下面被替换

            try:
                for event in ask_openclaw_stream(
                    prompt,
                    st.session_state.agent_session_id,
                    gateway_url=st.session_state.get("gateway_url"),
                    token=st.session_state.get("gateway_token"),
                ):
                    evt_type = event.get("type", "content")

                    if evt_type == "content":
                        full_response += event["text"]
                        # 实时更新正文（用 markdown 渲染已收到的部分）
                        content_slot.markdown(full_response + "▌")

                    elif evt_type == "tool_call":
                        # 工具调用开始
                        name = event.get("name", "未知工具")
                        tool_status_slot.info(f"🔧 调用工具: **{name}**")

                    elif evt_type == "status":
                        # 状态更新（参数拼接、思考中等）
                        text = event.get("text", "")
                        if text:
                            tool_status_slot.info(text)

                    elif evt_type == "tool_result":
                        # 工具返回结果
                        name = event.get("name", "")
                        result_text = event.get("result", "")[:200]
                        tool_status_slot.info(f"✅ 工具 {name} 返回: {result_text}")

                    elif evt_type == "error":
                        full_response += event["text"]
                        content_slot.markdown(full_response)

            except Exception as e:
                full_response = f"❌ 请求异常: {e}"
                content_slot.markdown(full_response)

            # 最终渲染（去掉光标）
            elapsed = time.time() - start_time
            if full_response:
                content_slot.markdown(full_response)
            # 清除工具状态（如果有的话）
            tool_status_slot.empty()
            st.caption(f"⏱️ 耗时 {elapsed:.1f}s")

        # 3. 回复存入 SQLite
        try:
            cm.add_message(current_cid, "assistant", full_response)
        except Exception as e:
            st.error(f"保存回复失败: {e}")

        # 4. 如果是第一条消息，自动设置标题
        try:
            if len(st.session_state.messages) <= 2:  # 刚加入的 user + assistant
                cm.auto_title(current_cid, prompt)
        except Exception:
            pass

        st.session_state.messages.append({"role": "assistant", "content": full_response})
        # 不再 st.rerun()，消息已经在上方实时渲染过了

# ==================== Tab 4: 仿真日志 ====================
with tab4:
    st.subheader("📋 仿真运行日志")
    
    # 日志过滤
    log_level = st.multiselect(
        "日志级别",
        ["INFO", "WARNING", "ERROR", "DEBUG"],
        default=["INFO", "WARNING", "ERROR"]
    )
    
    # 模拟日志数据
    logs = [
        {"time": "14:32:01", "level": "INFO", "source": "System", "message": "系统启动完成"},
        {"time": "14:32:02", "level": "INFO", "source": "DataLoader", "message": f"加载数据: {len(df_entity) if df_entity is not None else 0} 条记录"},
        {"time": "14:32:03", "level": "INFO", "source": "Visualization", "message": "3D轨道可视化初始化完成"},
        {"time": "14:32:04", "level": "WARNING", "source": "Analysis", "message": "检测到卫星间距离变化较大"},
        {"time": "14:32:05", "level": "INFO", "source": "Agent", "message": "Agent服务启动"},
        {"time": "14:32:06", "level": "ERROR", "source": "Data", "message": "平台3速度数据缺失，已填充默认值"},
        {"time": "14:32:07", "level": "INFO", "source": "UI", "message": f"用户选择平台: {selected_platforms}"},
        {"time": "14:32:08", "level": "INFO", "source": "Simulation", "message": f"仿真时间: {current_time:.1f}秒"},
    ]
    
    # 添加过滤后的日志
    filtered_logs = [log for log in logs if log["level"] in log_level]
    
    # 显示日志
    for log in filtered_logs:
        if log["level"] == "ERROR":
            st.error(f"`{log['time']}` [{log['level']}] ({log['source']}) {log['message']}")
        elif log["level"] == "WARNING":
            st.warning(f"`{log['time']}` [{log['level']}] ({log['source']}) {log['message']}")
        elif log["level"] == "DEBUG":
            st.info(f"`{log['time']}` [{log['level']}] ({log['source']}) {log['message']}")
        else:
            st.info(f"`{log['time']}` [{log['level']}] ({log['source']}) {log['message']}")

# ==================== Tab 5: 详细报告 ====================
with tab5:
    st.subheader("📈 仿真详细报告")
    
    if df_entity is not None:
        # 生成报告
        report_data = []
        
        for platform in selected_platforms:
            platform_data = df_entity[df_entity['platformIndex'] == platform]
            
            if len(platform_data) > 0:
                # 统计信息
                stats = {
                    '平台': f'平台 {platform}',
                    '数据点数': len(platform_data),
                    '时间范围': f"{platform_data['simTime'].min():.1f} - {platform_data['simTime'].max():.1f} 秒",
                    '平均速度 (km/s)': platform_data['velocity_magnitude'].mean(),
                    '速度标准差 (km/s)': platform_data['velocity_magnitude'].std(),
                    '最小高度 (km)': (np.sqrt(platform_data['x']**2 + platform_data['y']**2 + platform_data['z']**2) / 1000 - 6371).min(),
                    '最大高度 (km)': (np.sqrt(platform_data['x']**2 + platform_data['y']**2 + platform_data['z']**2) / 1000 - 6371).max(),
                    '位置范围 (km)': f"X: {platform_data['x'].max()/1000 - platform_data['x'].min()/1000:.1f}"
                }
                
                report_data.append(stats)
        
        # 显示报告
        if report_data:
            st.markdown("### 仿真统计报告")
            
            # 创建报告表格
            df_report = pd.DataFrame(report_data)
            st.dataframe(df_report.style.format({
                '平均速度 (km/s)': '{:.2f}',
                '速度标准差 (km/s)': '{:.2f}',
                '最小高度 (km)': '{:.1f}',
                '最大高度 (km)': '{:.1f}'
            }), width='stretch')
            
            # 生成建议
            st.markdown("### 📊 仿真分析建议")
            
            for platform in selected_platforms:
                platform_data = df_entity[df_entity['platformIndex'] == platform]
                
                if len(platform_data) > 0:
                    avg_velocity = platform_data['velocity_magnitude'].mean()
                    
                    # 判断轨道类型
                    if 7.5 <= avg_velocity <= 8.0:
                        orbit_type = "LEO"
                        recommendation = "轨道稳定，建议保持当前配置"
                    elif 3.0 <= avg_velocity <= 3.5:
                        orbit_type = "GEO"
                        recommendation = "地球同步轨道，需确保天线对准精度"
                    else:
                        orbit_type = "其他"
                        recommendation = "轨道类型特殊，需详细分析"
                    
                    st.markdown(f"""
                    **平台 {platform} ({orbit_type}):**
                    - 平均速度: {avg_velocity:.2f} km/s
                    - 建议: {recommendation}
                    """)
            
            # 导出报告
            if st.button("📄 导出完整报告"):
                # 创建完整报告
                report = f"""
                # AstraLogic 卫星通信仿真报告
                生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                
                ## 1. 仿真概览
                - 数据时间范围: {df_entity['simTime'].min():.1f} - {df_entity['simTime'].max():.1f} 秒
                - 总数据点: {len(df_entity)}
                - 参与平台: {', '.join([f'平台{p}' for p in selected_platforms])}
                
                ## 2. 平台统计
                {df_report.to_markdown()}
                
                ## 3. 通信分析
                - 最大通信距离: 10000 km
                - 通信覆盖率: {coverage_ratio:.1f}%
                
                ## 4. 建议
                1. 继续监控卫星间距离
                2. 根据轨道类型调整天线指向
                3. 定期校准时间同步
                """
                
                # 下载报告
                st.download_button(
                    label="下载报告",
                    data=report,
                    file_name=f"astra_logic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
    
    else:
        st.warning("无法生成报告，数据未加载")

# ==================== 底部 ====================
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; color: #7a7a7a; padding: 48px; background: #f5f5f7; border-radius: 18px; border: 1px solid #e0e0e0;'>
    🛰️ AstraLogic 卫星通信仿真系统 v1.0 · 基于 Agent + MCP + AFSIM · 课程设计项目 · 数据更新: {update_time}
</div>
""".format(
    update_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
), unsafe_allow_html=True)

# ==================== 运行说明 ====================
if __name__ == "__main__":
    st.write("""
    **使用说明:**
    1. 确保 `output/entity.csv` 和 `output/orbital.csv` 文件存在
    2. 运行此Streamlit应用: `streamlit run app.py`
    3. 在浏览器中访问 http://localhost:8501
    4. 使用侧边栏控制仿真参数
    5. 在不同标签页查看不同类型的分析
    """)