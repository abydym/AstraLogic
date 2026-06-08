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
import os
import warnings
warnings.filterwarnings('ignore')

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
        
        # 数据预处理
        df_entity['vx'] = df_entity['vx'].fillna(0)
        df_entity['vy'] = df_entity['vy'].fillna(0)
        df_entity['vz'] = df_entity['vz'].fillna(0)
        
        # 计算额外字段
        df_entity['velocity_magnitude'] = np.sqrt(
            df_entity['vx']**2 + df_entity['vy']**2 + df_entity['vz']**2
        ) / 1000  # 转换为km/s
        
        # 计算卫星间距离
        platform1_data = df_entity[df_entity['platformIndex'] == 1].reset_index(drop=True)
        platform2_data = df_entity[df_entity['platformIndex'] == 2].reset_index(drop=True)
        
        if len(platform1_data) == len(platform2_data):
            distances = []
            for i in range(len(platform1_data)):
                dx = platform1_data.loc[i, 'x'] - platform2_data.loc[i, 'x']
                dy = platform1_data.loc[i, 'y'] - platform2_data.loc[i, 'y']
                dz = platform1_data.loc[i, 'z'] - platform2_data.loc[i, 'z']
                dist = np.sqrt(dx**2 + dy**2 + dz**2) / 1000
                distances.append(dist)
            
            # 创建距离DataFrame
            df_distance = pd.DataFrame({
                'simTime': platform1_data['simTime'],
                'distance': distances
            })
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
def ask_openclaw_stream(message, session_id):
    """通过 openclaw CLI 流式发送消息给 agent，逐 chunk yield 回复文本"""
    cmd = "openclaw.cmd" if sys.platform == "win32" else "openclaw"
    proc = subprocess.Popen(
        [cmd, "agent", "--session-id", session_id, "--message", message],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # 逐字节读取 stdout，遇到换行或缓冲满就 yield
    buf = b""
    while True:
        ch = proc.stdout.read(1)
        if not ch:
            break
        buf += ch
        # 遇到换行或缓冲超过 60 字节就 flush 一次
        if ch == b"\n" or len(buf) >= 60:
            if buf:
                yield buf.decode("utf-8", errors="replace")
                buf = b""
    if buf:
        yield buf.decode("utf-8", errors="replace")

    proc.wait()
    # 如果返回码非零，检查 stderr
    if proc.returncode != 0:
        stderr_text = proc.stderr.read().decode("utf-8", errors="replace").strip()
        yield f"\n❌ CLI 错误 (code {proc.returncode}): {stderr_text[:300]}"

# ─── 会话持久化 ───
SESSION_DIR = "sessions"
SESSION_FILE = os.path.join(SESSION_DIR, "chat_history.json")

def load_all_sessions():
    """加载所有历史会话"""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

def save_all_sessions(sessions):
    """保存所有会话到文件"""
    os.makedirs(SESSION_DIR, exist_ok=True)
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

def create_new_session():
    """创建新会话"""
    sid = str(uuid.uuid4())
    return {
        "id": sid,
        "title": f"新对话 {datetime.now().strftime('%H:%M')}",
        "created_at": datetime.now().isoformat(),
        "messages": []
    }

def update_session_title(session):
    """根据第一条用户消息自动更新会话标题"""
    for m in session.get("messages", []):
        if m["role"] == "user":
            title = m["content"].strip()[:40]
            session["title"] = title + ("…" if len(m["content"].strip()) > 40 else "")
            break

# ==================== 初始化会话状态 ====================
if 'running' not in st.session_state:
    st.session_state.running = False
if 'sim_time' not in st.session_state:
    st.session_state.sim_time = 0.0
if 'selected_platforms' not in st.session_state:
    st.session_state.selected_platforms = [1, 2, 3]
# ── 会话管理状态 ──
if 'sessions' not in st.session_state:
    st.session_state.sessions = load_all_sessions()
if 'sessions_loaded' not in st.session_state:
    st.session_state.sessions_loaded = st.session_state.sessions.copy() if st.session_state.sessions else None
if 'active_session_id' not in st.session_state:
    existing = st.session_state.sessions
    if existing:
        latest = existing[-1]  # 最新会话
        st.session_state.active_session_id = latest["id"]
    else:
        # 没有历史会话，创建默认空会话
        sid = str(uuid.uuid4())
        st.session_state.active_session_id = sid
        st.session_state.sessions = [{"id": sid, "title": "新对话", "created_at": datetime.now().isoformat(), "messages": []}]
        save_all_sessions(st.session_state.sessions)
if 'agent_session_id' not in st.session_state:
    # agent_session_id 跟随 active_session_id
    st.session_state.agent_session_id = st.session_state.active_session_id

def get_active_session():
    """获取当前活跃会话对象"""
    for s in st.session_state.sessions:
        if s["id"] == st.session_state.active_session_id:
            return s
    return None

def save_active_session():
    """将当前活跃会话写回 sessions 列表并持久化"""
    active = get_active_session()
    if active is None:
        return
    # 更新 sessions 中的对应条目
    for i, s in enumerate(st.session_state.sessions):
        if s["id"] == active["id"]:
            st.session_state.sessions[i] = active
            break
    save_all_sessions(st.session_state.sessions)

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

    /* ── 会话历史列表样式 ── */
    .session-item {
        padding: 10px 12px;
        margin: 4px 0;
        border-radius: 10px;
        cursor: pointer;
        border: 1px solid var(--apple-hairline);
        transition: background 0.15s;
        font-size: 13px;
    }
    .session-item:hover {
        background: var(--apple-parchment);
    }
    .session-item.active {
        background: var(--apple-primary);
        color: white;
        border-color: var(--apple-primary);
    }
    .session-item .session-title {
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .session-item .session-meta {
        font-size: 11px;
        color: var(--apple-ink-muted);
        margin-top: 2px;
    }
    .session-item.active .session-meta {
        color: rgba(255,255,255,0.8);
    }
    .session-delete-btn button {
        font-size: 11px !important;
        padding: 2px 8px !important;
        border-radius: 6px !important;
        border: 1px solid #e0e0e0 !important;
        background: transparent !important;
        color: #999 !important;
    }
    .session-delete-btn button:hover {
        background: #fee !important;
        color: #c00 !important;
        border-color: #fcc !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 加载数据 ====================
df_entity, df_orbital, df_distance = load_data()

# ==================== 侧边栏 ====================
with st.sidebar:
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
    avg_velocity = current_data[current_data['platformIndex'].isin(selected_platforms)]['velocity_magnitude'].mean()
    
    # 计算卫星间距离
    if df_distance is not None and current_time in df_distance['simTime'].values:
        current_distance = df_distance[df_distance['simTime'] == current_time]['distance'].values[0]
    else:
        current_distance = 0
    
    # 通信覆盖率
    if len(df_distance) > 0:
        max_comm_range = 10000  # 10000 km
        coverage_ratio = sum(1 for d in df_distance['distance'] if d <= max_comm_range) / len(df_distance) * 100
    else:
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
                    y=df_distance['distance'],
                    mode='lines+markers',
                    name='卫星间距离',
                    line=dict(color='purple', width=3),
                    marker=dict(size=4)
                ))
                
                # 添加通信阈值线
                max_comm_range = 10000  # 10000 km
                fig_dist.add_hline(y=max_comm_range, line_dash="dash", line_color="red",
                                  annotation_text="最大通信距离")
                
                fig_dist.update_layout(
                    title='卫星间距离随时间变化（通信链路评估）',
                    xaxis_title='仿真时间 (秒)',
                    yaxis_title='距离 (km)',
                    height=500,
                    showlegend=True,
                    yaxis=dict(range=[0, max(df_distance['distance']) * 1.1])
                )
                apply_apple_chart_style(fig_dist)
                
                st.plotly_chart(fig_dist, width='stretch')
                render_plot_export(fig_dist, "distance_timeseries", "dist_timeseries")
                
                # 距离统计
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    min_dist = df_distance['distance'].min()
                    st.metric("最小距离", f"{min_dist:.1f} km")
                
                with col2:
                    max_dist = df_distance['distance'].max()
                    st.metric("最大距离", f"{max_dist:.1f} km")
                
                with col3:
                    avg_dist = df_distance['distance'].mean()
                    st.metric("平均距离", f"{avg_dist:.1f} km")
            
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
with tab3:
    st.markdown("""
    <style>
    footer, .stApp footer { display: none !important; }
    section[data-testid="stBottom"] > div:first-child { padding-bottom: 0; }
    .main > div:last-child .stMarkdown:last-child { display: none; }
    </style>
    """, unsafe_allow_html=True)

    # ── 左右分栏：左 会话列表 | 右 聊天区 ──
    col_left, col_right = st.columns([1, 2.5])

    # ======= 左侧：会话历史面板 =======
    with col_left:
        st.markdown("**💬 历史会话**")

        if st.button("➕ 新建对话", use_container_width=True, key="tab3_new_chat"):
            new_s = create_new_session()
            st.session_state.sessions.append(new_s)
            save_all_sessions(st.session_state.sessions)
            st.session_state.active_session_id = new_s["id"]
            st.session_state.agent_session_id = new_s["id"]
            st.rerun()

        sessions_list = list(st.session_state.sessions)
        if sessions_list:
            st.caption(f"共 {len(sessions_list)} 个会话")
            for s in reversed(sessions_list):
                sid = s["id"]
                is_active = (sid == st.session_state.active_session_id)
                title = s.get("title", "无标题")
                msg_count = len(s.get("messages", []))
                created = s.get("created_at", "")[:16].replace("T", " ")

                row_col1, row_col2 = st.columns([9, 1])
                with row_col1:
                    label = f"{'📌 ' if is_active else ''}{title}"
                    if st.button(
                        label, key=f"t3_sw_{sid}",
                        help=f"{msg_count} 条消息 · {created}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary",
                    ):
                        st.session_state.active_session_id = sid
                        st.session_state.agent_session_id = sid
                        st.rerun()
                with row_col2:
                    if st.button("🗑", key=f"t3_del_{sid}", help="删除此会话"):
                        st.session_state.sessions = [x for x in st.session_state.sessions if x["id"] != sid]
                        save_all_sessions(st.session_state.sessions)
                        if sid == st.session_state.active_session_id:
                            remaining = st.session_state.sessions
                            if remaining:
                                st.session_state.active_session_id = remaining[-1]["id"]
                                st.session_state.agent_session_id = remaining[-1]["id"]
                            else:
                                new_s = create_new_session()
                                st.session_state.sessions = [new_s]
                                save_all_sessions(st.session_state.sessions)
                                st.session_state.active_session_id = new_s["id"]
                                st.session_state.agent_session_id = new_s["id"]
                        st.rerun()
        else:
            st.caption("暂无历史会话")

    # ======= 右侧：聊天区 =======
    with col_right:
        active_session = get_active_session()

        if active_session:
            st.caption(
                f"当前: **{active_session.get('title', '未命名')}** · "
                f"{len(active_session.get('messages', []))} 条消息"
            )
        else:
            st.caption("选择或新建一个会话开始对话")

        # 消息列表
        msg_container = st.container(height=400)
        with msg_container:
            if active_session:
                for msg in active_session.get("messages", []):
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
            else:
                st.info("👋 在左侧选择或新建一个会话")

    # ⚠️ chat_input 必须放在 columns 外面，放在 tab3 层级
    if prompt := st.chat_input("输入你的问题..."):
        active_session = get_active_session()
        if active_session is None:
            new_s = create_new_session()
            st.session_state.sessions.append(new_s)
            save_all_sessions(st.session_state.sessions)
            st.session_state.active_session_id = new_s["id"]
            st.session_state.agent_session_id = new_s["id"]
            active_session = new_s

        active_session.setdefault("messages", []).append({"role": "user", "content": prompt})
        update_session_title(active_session)
        save_active_session()

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = st.write_stream(
                ask_openclaw_stream(prompt, st.session_state.agent_session_id)
            )

        active_session["messages"].append({"role": "assistant", "content": response})
        save_active_session()
        st.rerun()

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