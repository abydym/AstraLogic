import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
import aermsg2dataframe as a2df
import pymystic

# 1. 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 2. 模拟读取你的数据（根据你提供的实际数据）
# 根据你的输出，我创建了示例DataFrame
def create_sample_dataframes():
    """根据你的输出创建示例数据"""
    
    # 实体状态数据
    entity_data = []
    
    # 平台1（卫星1）
    times = np.arange(0, 1801, 10)
    for t in times:
        # 简单的轨道模拟
        angle = t / 600 * np.pi  # 每600秒转半圈
        x = -1300000 * np.cos(angle) + 10000 * np.sin(angle * 0.1)
        y = -6950000 * np.sin(angle) + 5000 * np.cos(angle * 0.1)
        z = 100000 * np.sin(angle * 0.5)  # 小的垂直分量
        
        entity_data.append({
            'simTime': t,
            'platformIndex': 1,
            'x': x,
            'y': y,
            'z': z,
            'vx': 3936 * np.sin(angle) * 0.1,
            'vy': -741 * np.cos(angle) * 0.1,
            'vz': 5999 * np.sin(angle * 0.5),
            'damage': 0.0
        })
    
    # 平台2（卫星2）
    for t in times:
        angle = t / 600 * np.pi + np.pi  # 相位差180度
        x = 1300000 * np.cos(angle) - 10000 * np.sin(angle * 0.1)
        y = 6950000 * np.sin(angle) - 5000 * np.cos(angle * 0.1)
        z = -100000 * np.sin(angle * 0.5)
        
        entity_data.append({
            'simTime': t,
            'platformIndex': 2,
            'x': x,
            'y': y,
            'z': z,
            'vx': -3926 * np.sin(angle) * 0.1,
            'vy': 739 * np.cos(angle) * 0.1,
            'vz': -5987 * np.sin(angle * 0.5),
            'damage': 0.0
        })
    
    # 平台3（地面站）
    for t in times:
        entity_data.append({
            'simTime': t,
            'platformIndex': 3,
            'x': -2178640,
            'y': 4388842,
            'z': 4069474,
            'vx': np.nan,
            'vy': np.nan,
            'vz': np.nan,
            'damage': 0.0
        })
    
    df_entity = pd.DataFrame(entity_data)
    
    # 轨道根数数据
    orbital_data = []
    times_orb = [0, 600, 1200, 1800]
    
    for t in times_orb:
        orbital_data.append({
            'simTime': t,
            'platformIndex': 1,
            'semiMajorAxis': 7078000,
            'eccentricity': 0.001,
            'inclination': 0.92498,
            'raan': 6.279259,
            'trueAnomaly': 6.283185 - (t / 600) * np.pi / 2  # 递减
        })
        
        orbital_data.append({
            'simTime': t,
            'platformIndex': 2,
            'semiMajorAxis': 7078000,
            'eccentricity': 0.001,
            'inclination': 0.92498,
            'raan': 6.279259,
            'trueAnomaly': 3.141578 + (t / 600) * np.pi / 2  # 递增
        })
    
    df_orbital = pd.DataFrame(orbital_data)
    
    return df_entity, df_orbital

# 如果你有真实的数据文件，可以替换这个函数
df_entity = pd.read_csv('../output/entity.csv')
df_orbital = pd.read_csv('../output/orbital.csv')
# df_entity, df_orbital = a2df.parse_aer_file('../scenarios/demo_output.aer')

# with pymystic.Reader('../scenarios/demo_output.aer') as reader:
#     # for msg in reader:
#     #     print(msg)
#     messages = list(reader)
#     df_entity, df_orbital = a2df.parse_aer_messages(messages)

# df_entity, df_orbital = create_sample_dataframes()

print("=" * 60)
print("AstraLogic - AFSIM 卫星通信仿真数据分析")
print("=" * 60)

# 3. 数据摘要
print("\n📊 数据摘要:")
print(f"实体状态数据点: {len(df_entity)}")
print(f"轨道根数数据点: {len(df_orbital)}")
print(f"仿真时间范围: {df_entity['simTime'].min():.1f} - {df_entity['simTime'].max():.1f} 秒")
print(f"平台数量: {df_entity['platformIndex'].nunique()}")
print(f"  平台1 (卫星1): {len(df_entity[df_entity['platformIndex']==1])} 条记录")
print(f"  平台2 (卫星2): {len(df_entity[df_entity['platformIndex']==2])} 条记录")
print(f"  平台3 (地面站): {len(df_entity[df_entity['platformIndex']==3])} 条记录")

# 4. 检查是否有通信链路数据（根据你的AER文件分析）
# 在你的示例数据中，没有明确的通信状态字段
# 但我们可以模拟一些通信链路状态
has_comm_data = 'MsgCommStatus' in df_entity.columns  # 假设

print(f"\n📡 通信链路数据: {'检测到' if has_comm_data else '未检测到'}")

# 5. 开始可视化
print("\n🎨 生成可视化图表...")

# ============================================================
# 图表1: 3D卫星轨道轨迹（使用Plotly，交互式）
# ============================================================
print("\n1. 3D卫星轨道轨迹（使用Plotly）")

fig_3d = go.Figure()

# 为每个平台添加轨迹
colors = ['blue', 'red', 'green']
platform_names = ['卫星1', '卫星2', '地面站']

for platform_idx, color, name in zip([1, 2, 3], colors, platform_names):
    df_platform = df_entity[df_entity['platformIndex'] == platform_idx]
    
    # 轨迹线
    fig_3d.add_trace(go.Scatter3d(
        x=df_platform['x'] / 1000,  # 转换为km
        y=df_platform['y'] / 1000,
        z=df_platform['z'] / 1000,
        mode='lines+markers',
        name=f'{name}轨迹',
        line=dict(color=color, width=3),
        marker=dict(size=2, color=color),
        legendgroup=name
    ))
    
    # 最新位置标记
    if len(df_platform) > 0:
        latest = df_platform.iloc[-1]
        fig_3d.add_trace(go.Scatter3d(
            x=[latest['x'] / 1000],
            y=[latest['y'] / 1000],
            z=[latest['z'] / 1000],
            mode='markers+text',
            name=f'{name}最新位置',
            marker=dict(size=8, color=color, symbol='circle'),
            text=[f'{name}\n{latest["simTime"]:.0f}s'],
            textposition='top center',
            textfont=dict(size=10, color='black'),
            legendgroup=name
        ))

# 添加地球参考（简化为一个球面）
u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
r_earth = 6371  # 地球半径 km
x_earth = r_earth * np.cos(u) * np.sin(v)
y_earth = r_earth * np.sin(u) * np.sin(v)
z_earth = r_earth * np.cos(v)

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
        text='AstraLogic - 3D卫星轨道轨迹',
        font=dict(size=20, family='SimHei'),
        x=0.5
    ),
    scene=dict(
        xaxis_title='X (km)',
        yaxis_title='Y (km)',
        zaxis_title='Z (km)',
        aspectmode='data',
        camera=dict(
            eye=dict(x=1.5, y=1.5, z=1.0)
        ),
        xaxis=dict(backgroundcolor="rgb(200, 200, 230)"),
        yaxis=dict(backgroundcolor="rgb(230, 200, 230)"),
        zaxis=dict(backgroundcolor="rgb(230, 230, 200)")
    ),
    width=1000,
    height=800,
    showlegend=True,
    legend=dict(x=0.02, y=0.98)
)

# 显示图表
fig_3d.show()
print("  ✅ 3D轨道图已显示")

# ============================================================
# 图表2: 轨道参数时间序列图（使用Matplotlib）
# ============================================================
print("\n2. 轨道参数时间序列图（使用Matplotlib）")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('AstraLogic - 轨道参数时间序列分析', fontsize=16, y=1.02)

# 为每个平台绘制
platforms = [1, 2]
platform_colors = ['blue', 'red']

for idx, (platform, color) in enumerate(zip(platforms, platform_colors)):
    df_plat = df_orbital[df_orbital['platformIndex'] == platform]
    
    # 半长轴
    axes[0, 0].plot(df_plat['simTime'], df_plat['semiMajorAxis'] / 1000, 
                    color=color, linewidth=2, marker='o', label=f'卫星{platform}')
    
    # 偏心率
    axes[0, 1].plot(df_plat['simTime'], df_plat['eccentricity'],
                    color=color, linewidth=2, marker='s', label=f'卫星{platform}')
    
    # 轨道倾角（转换为度）
    axes[1, 0].plot(df_plat['simTime'], np.degrees(df_plat['inclination']),
                    color=color, linewidth=2, marker='^', label=f'卫星{platform}')
    
    # 真近点角
    axes[1, 1].plot(df_plat['simTime'], np.degrees(df_plat['trueAnomaly']),
                    color=color, linewidth=2, marker='d', label=f'卫星{platform}')

# 设置图表标签
axes[0, 0].set_title('半长轴变化', fontsize=12)
axes[0, 0].set_xlabel('仿真时间 (s)')
axes[0, 0].set_ylabel('半长轴 (km)')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend()

axes[0, 1].set_title('偏心率变化', fontsize=12)
axes[0, 1].set_xlabel('仿真时间 (s)')
axes[0, 1].set_ylabel('偏心率')
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].legend()

axes[1, 0].set_title('轨道倾角变化', fontsize=12)
axes[1, 0].set_xlabel('仿真时间 (s)')
axes[1, 0].set_ylabel('倾角 (°)')
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].legend()

axes[1, 1].set_title('真近点角变化', fontsize=12)
axes[1, 1].set_xlabel('仿真时间 (s)')
axes[1, 1].set_ylabel('真近点角 (°)')
axes[1, 1].grid(True, alpha=0.3)
axes[1, 1].legend()

plt.tight_layout()
plt.show()
print("  ✅ 轨道参数时间序列图已显示")

# ============================================================
# 图表3: 卫星位置分离图（使用Matplotlib）
# ============================================================
print("\n3. 卫星位置分离图")

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('AstraLogic - 卫星位置坐标变化', fontsize=16, y=1.02)

for platform, color, name in zip([1, 2, 3], ['blue', 'red', 'green'], ['卫星1', '卫星2', '地面站']):
    df_plat = df_entity[df_entity['platformIndex'] == platform]
    
    if len(df_plat) > 0:
        # X坐标
        axes[0].plot(df_plat['simTime'], df_plat['x'] / 1000, 
                    color=color, linewidth=1.5, label=name, alpha=0.8)
        
        # Y坐标
        axes[1].plot(df_plat['simTime'], df_plat['y'] / 1000, 
                    color=color, linewidth=1.5, label=name, alpha=0.8)
        
        # Z坐标
        axes[2].plot(df_plat['simTime'], df_plat['z'] / 1000, 
                    color=color, linewidth=1.5, label=name, alpha=0.8)

# 设置图表标签
axes[0].set_title('X坐标变化', fontsize=12)
axes[0].set_xlabel('仿真时间 (s)')
axes[0].set_ylabel('X坐标 (km)')
axes[0].grid(True, alpha=0.3)
axes[0].legend()

axes[1].set_title('Y坐标变化', fontsize=12)
axes[1].set_xlabel('仿真时间 (s)')
axes[1].set_ylabel('Y坐标 (km)')
axes[1].grid(True, alpha=0.3)
axes[1].legend()

axes[2].set_title('Z坐标变化', fontsize=12)
axes[2].set_xlabel('仿真时间 (s)')
axes[2].set_ylabel('Z坐标 (km)')
axes[2].grid(True, alpha=0.3)
axes[2].legend()

plt.tight_layout()
plt.show()
print("  ✅ 位置分离图已显示")

# ============================================================
# 图表4: 速度矢量图（使用Plotly）
# ============================================================
print("\n4. 速度矢量可视化")

fig_vel = go.Figure()

for platform, color, name in zip([1, 2], ['blue', 'red'], ['卫星1', '卫星2']):
    df_plat = df_entity[(df_entity['platformIndex'] == platform) & 
                       (df_entity['vx'].notna())]  # 只选有速度数据的
    
    if len(df_plat) > 0:
        # 计算速度大小
        df_plat['v_magnitude'] = np.sqrt(df_plat['vx']**2 + df_plat['vy']**2 + df_plat['vz']**2)
        
        fig_vel.add_trace(go.Scatter(
            x=df_plat['simTime'],
            y=df_plat['v_magnitude'] / 1000,  # km/s
            mode='lines+markers',
            name=f'{name} 速度大小',
            line=dict(color=color, width=2),
            marker=dict(size=4)
        ))

# 添加参考线
fig_vel.add_hline(y=7.8, line_dash="dash", line_color="green", 
                  annotation_text="LEO轨道速度 (~7.8 km/s)")
fig_vel.add_hline(y=3.07, line_dash="dash", line_color="orange", 
                  annotation_text="GEO轨道速度 (~3.07 km/s)")

fig_vel.update_layout(
    title=dict(
        text='卫星速度大小随时间变化',
        font=dict(size=16)
    ),
    xaxis_title='仿真时间 (秒)',
    yaxis_title='速度大小 (km/s)',
    width=1000,
    height=500,
    showlegend=True,
    legend=dict(x=0.02, y=0.98)
)

fig_vel.show()
print("  ✅ 速度矢量图已显示")

# ============================================================
# 图表5: 卫星间距离分析（模拟通信链路）
# ============================================================
print("\n5. 卫星间距离与通信链路分析")

# 计算卫星1和卫星2之间的距离
df_s1 = df_entity[df_entity['platformIndex'] == 1].reset_index(drop=True)
df_s2 = df_entity[df_entity['platformIndex'] == 2].reset_index(drop=True)

if len(df_s1) == len(df_s2):
    # 计算距离
    distances = []
    times = []
    
    for i in range(len(df_s1)):
        if not np.isnan(df_s1.loc[i, 'x']) and not np.isnan(df_s2.loc[i, 'x']):
            dx = df_s1.loc[i, 'x'] - df_s2.loc[i, 'x']
            dy = df_s1.loc[i, 'y'] - df_s2.loc[i, 'y']
            dz = df_s1.loc[i, 'z'] - df_s2.loc[i, 'z']
            dist = np.sqrt(dx**2 + dy**2 + dz**2) / 1000  # km
            distances.append(dist)
            times.append(df_s1.loc[i, 'simTime'])
    
    # 创建距离图表
    fig_dist = go.Figure()
    
    fig_dist.add_trace(go.Scatter(
        x=times,
        y=distances,
        mode='lines+markers',
        name='卫星1-卫星2距离',
        line=dict(color='purple', width=3),
        marker=dict(size=4)
    ))
    
    # 添加通信阈值线
    max_comm_range = 10000  # 10000 km最大通信距离
    fig_dist.add_hline(y=max_comm_range, line_dash="dash", line_color="red", 
                      annotation_text="最大通信距离")
    
    # 计算最小距离和最大距离
    min_dist = min(distances)
    max_dist = max(distances)
    
    fig_dist.add_annotation(
        x=times[np.argmin(distances)],
        y=min_dist,
        text=f"最小距离: {min_dist:.1f} km",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-40
    )
    
    fig_dist.update_layout(
        title=dict(
            text='卫星间距离分析（通信链路评估）',
            font=dict(size=16)
        ),
        xaxis_title='仿真时间 (秒)',
        yaxis_title='距离 (km)',
        width=1000,
        height=500,
        yaxis=dict(range=[0, max(max_dist, max_comm_range) * 1.1])
    )
    
    fig_dist.show()
    print("  ✅ 距离与通信分析图已显示")
else:
    print("  ⚠️ 卫星1和卫星2数据点数不一致，无法计算距离")

# ============================================================
# 图表6: 数据统计分析
# ============================================================
print("\n6. 数据统计分析")

# 统计信息
stats_data = []

for platform in [1, 2, 3]:
    df_plat = df_entity[df_entity['platformIndex'] == platform]
    
    if len(df_plat) > 0:
        # 计算位置范围
        x_range = (df_plat['x'].max() - df_plat['x'].min()) / 1000
        y_range = (df_plat['y'].max() - df_plat['y'].min()) / 1000
        z_range = (df_plat['z'].max() - df_plat['z'].min()) / 1000
        
        # 计算平均位置
        x_mean = df_plat['x'].mean() / 1000
        y_mean = df_plat['y'].mean() / 1000
        z_mean = df_plat['z'].mean() / 1000
        
        stats_data.append({
            '平台': f'平台{platform}',
            '数据点数': len(df_plat),
            'X范围(km)': f"{x_range:.1f}",
            'Y范围(km)': f"{y_range:.1f}",
            'Z范围(km)': f"{z_range:.1f}",
            '平均X(km)': f"{x_mean:.1f}",
            '平均Y(km)': f"{y_mean:.1f}",
            '平均Z(km)': f"{z_mean:.1f}"
        })

# 创建统计表格
if stats_data:
    df_stats = pd.DataFrame(stats_data)
    
    print("\n📊 位置统计信息:")
    print(df_stats.to_string(index=False))
    
    # 创建统计图表
    fig_stats, ax = plt.subplots(figsize=(10, 4))
    ax.axis('tight')
    ax.axis('off')
    
    # 创建表格
    table_data = []
    headers = df_stats.columns.tolist()
    
    for _, row in df_stats.iterrows():
        table_data.append(row.tolist())
    
    table = ax.table(cellText=table_data,
                    colLabels=headers,
                    cellLoc='center',
                    loc='center')
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    plt.title('卫星位置统计信息表', fontsize=14, y=0.8)
    plt.tight_layout()
    plt.show()
    print("  ✅ 统计图表已显示")

# ============================================================
# 最终总结
# ============================================================
print("\n" + "=" * 60)
print("🎯 AstraLogic 分析总结")
print("=" * 60)
print(f"• 仿真时间: {df_entity['simTime'].min():.0f} - {df_entity['simTime'].max():.0f} 秒")
print(f"• 卫星数量: 2颗LEO卫星 + 1个地面站")
print(f"• 轨道类型: 近圆轨道 (偏心率 = {df_orbital['eccentricity'].iloc[0]:.3f})")
print(f"• 轨道高度: 约 {df_orbital['semiMajorAxis'].iloc[0]/1000 - 6371:.1f} km")
print(f"• 轨道周期: 约 {2*np.pi*np.sqrt((df_orbital['semiMajorAxis'].iloc[0]/1000)**3/398600)/60:.1f} 分钟")

# 计算覆盖分析
if len(distances) > 0:
    coverage_ratio = sum(1 for d in distances if d <= max_comm_range) / len(distances) * 100
    print(f"• 通信覆盖率: {coverage_ratio:.1f}% (在 {max_comm_range} km 范围内)")
else:
    print(f"• 通信覆盖率: 数据不足")

print("\n🔍 关键发现:")
print("1. 两颗卫星呈对称轨道运行，相位差约180度")
print("2. 卫星间距离呈周期性变化，最小距离约 {:.1f} km".format(min_dist if 'min_dist' in locals() else 0))
print("3. 地面站位置固定，坐标为 ({:.1f}, {:.1f}, {:.1f}) km".format(
    df_entity[df_entity['platformIndex']==3]['x'].iloc[0]/1000,
    df_entity[df_entity['platformIndex']==3]['y'].iloc[0]/1000,
    df_entity[df_entity['platformIndex']==3]['z'].iloc[0]/1000))

print("\n💡 项目建议:")
print("1. 可在此基础上添加真实的通信链路计算")
print("2. 实现覆盖率地图可视化")
print("3. 添加信号强度和误码率分析")
print("4. 集成到Streamlit中实现实时交互")