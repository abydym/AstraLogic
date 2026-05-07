"""
AstraLogic - AFSIM 卫星通信仿真核心模块

本模块提供：
  1. AFSIM 场景脚本生成
  2. AFSIM 仿真执行
  3. 仿真结果解析

用法：
    from core.afsim_bridge import *
"""

import os
import subprocess
import csv
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path


# ============================================================
# 配置
# ============================================================

# AFSIM 安装路径（自动检测，也可手动指定）
AFSIM_ROOT = r"D:\Projects\afsim-2.9.0"
AFSIM_BIN = os.path.join(AFSIM_ROOT, "bin")
MISSION_EXE = os.path.join(AFSIM_BIN, "mission.exe")
WIZARD_EXE = os.path.join(AFSIM_BIN, "wizard.exe")

# 默认工作目录
DEFAULT_WORK_DIR = r"D:\Projects\AFSIM_test_proj"


@dataclass
class SimConfig:
    """仿真配置"""
    afsim_exe: str = MISSION_EXE       # mission.exe 路径
    work_dir: str = DEFAULT_WORK_DIR   # 工作目录
    end_time: str = "10 min"           # 仿真时长
    start_date: str = "may 1 2026"     # 起始日期
    output_aer: str = "output.aer"     # 输出 .aer 文件名
    output_evt: str = "output.evt"     # 输出 .evt 文件名
    output_csv: str = "output.csv"     # 输出 .csv 文件名


# ============================================================
# 数据结构
# ============================================================

@dataclass
class Satellite:
    """卫星平台"""
    name: str
    semi_major_axis: float = 7000.0    # km
    eccentricity: float = 0.001
    inclination: float = 45.0          # deg
    raan: float = 0.0                  # deg
    arg_perigee: float = 0.0           # deg
    true_anomaly: float = 0.0          # deg
    update_interval: str = "10 sec"


@dataclass
class GroundStation:
    """地面站"""
    name: str
    latitude: float     # deg
    longitude: float    # deg
    altitude: float = 0.0  # m


@dataclass
class SimMessage:
    """平台间消息"""
    source: str
    destination: str
    msg_type: str = "DATA"
    send_time: str = "30 sec"   # 仿真时间


@dataclass
class RunResult:
    """仿真运行结果"""
    success: bool
    return_code: int
    stdout: str
    stderr: str
    scenario_file: str
    aer_file: str
    evt_file: str
    csv_file: str
    duration_sec: float = 0.0


# ============================================================
# 场景生成器
# ============================================================

class ScenarioBuilder:
    """生成 AFSIM 场景脚本"""

    def __init__(self, config: SimConfig = None):
        self.config = config or SimConfig()
        self.satellites: List[Satellite] = []
        self.ground_stations: List[GroundStation] = []
        self.messages: List[SimMessage] = []
        self.extra_blocks: List[str] = []

    def add_satellite(self, sat: Satellite) -> 'ScenarioBuilder':
        self.satellites.append(sat)
        return self

    def add_ground_station(self, gs: GroundStation) -> 'ScenarioBuilder':
        self.ground_stations.append(gs)
        return self

    def add_message(self, msg: SimMessage) -> 'ScenarioBuilder':
        self.messages.append(msg)
        return self

    def add_block(self, block: str) -> 'ScenarioBuilder':
        """添加自定义 AFSIM 脚本块"""
        self.extra_blocks.append(block)
        return self

    def build(self, filename: str = None) -> str:
        """生成场景文件，返回文件路径"""
        if filename is None:
            filename = "astra_scenario.txt"

        work = Path(self.config.work_dir)
        work.mkdir(parents=True, exist_ok=True)
        filepath = work / filename

        parts = [
            self._header(),
            self._sim_control(),
            self._event_output(),
            self._platforms(),
            self._messages(),
            "\n".join(self.extra_blocks),
        ]

        content = "\n".join(p for p in parts if p)
        filepath.write_text(content, encoding='utf-8')
        print(f"[AstraLogic] 场景已生成: {filepath}")
        return str(filepath)

    def _header(self) -> str:
        return """# ============================================
# AstraLogic - 卫星通信仿真场景
# 自动生成
# ============================================

"""

    def _sim_control(self) -> str:
        return f"""start_date {self.config.start_date}
start_time 00:00:00.00
end_time {self.config.end_time}

"""

    def _event_output(self) -> str:
        return f"""event_pipe
  file {self.config.output_aer}
  maximum_mover_update_interval 0 sec
end_event_pipe

event_output
  file {self.config.output_evt}
  enable all
  time_format s
end_event_output

csv_event_output
  file {self.config.output_csv}
  enable all
end_csv_event_output

"""

    def _platforms(self) -> str:
        lines = []

        for sat in self.satellites:
            lines.append(f"""platform {sat.name} WSF_PLATFORM
  icon satellite
  side blue
  empty_mass 100 kg

  add mover WSF_SPACE_MOVER
    update_interval {sat.update_interval}
    eccentricity {sat.eccentricity}
    semi_major_axis {sat.semi_major_axis} km
    raan {sat.raan} deg
    inclination {sat.inclination} deg
    true_anomaly {sat.true_anomaly} deg
    argument_of_periapsis {sat.arg_perigee} deg
  end_mover
end_platform

""")

        for gs in self.ground_stations:
            # AFSIM position 格式：lat_n/s lon_e/w
            lat_str = f"{abs(gs.latitude)}{'n' if gs.latitude >= 0 else 's'}"
            lon_str = f"{abs(gs.longitude)}{'e' if gs.longitude >= 0 else 'w'}"
            lines.append(f"""platform {gs.name} WSF_PLATFORM
  side blue
  position {lat_str} {lon_str}
end_platform

""")

        return "\n".join(lines)

    def _messages(self) -> str:
        if not self.messages:
            return ""
        lines = ["# 消息脚本\n"]
        for i, msg in enumerate(self.messages):
            lines.append(f"""# 消息 {i+1}: {msg.msg_type}
execute at_time {msg.send_time} absolute
  writeln("[MSG] {msg.msg_type} sent from {msg.source} to {msg.destination} @ T=", TIME_NOW);
end_execute

""")
        return "\n".join(lines)


# ============================================================
# 仿真运行器
# ============================================================

class SimRunner:
    """执行 AFSIM 仿真"""

    def __init__(self, config: SimConfig = None):
        self.config = config or SimConfig()

    def run(self, scenario_file: str, timeout: float = 120.0) -> RunResult:
        """运行指定场景"""
        import time

        # 解析路径
        if not os.path.isabs(scenario_file):
            scenario_file = os.path.join(self.config.work_dir, scenario_file)

        if not os.path.exists(scenario_file):
            return RunResult(False, -1, "", f"文件不存在: {scenario_file}", scenario_file, "", "", "")

        exe = self.config.afsim_exe
        if not os.path.exists(exe):
            return RunResult(False, -1, "", f"AFSIM 不存在: {exe}", scenario_file, "", "", "")

        # 工作目录设为场景文件所在目录（输出文件会生成在这里）
        scenario_dir = os.path.dirname(os.path.abspath(scenario_file))

        cmd = [exe, scenario_file]
        print(f"[AstraLogic] 执行: {' '.join(cmd)}")
        print(f"[AstraLogic] 工作目录: {scenario_dir}")

        t0 = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                                  cwd=scenario_dir)
            elapsed = time.time() - t0

            # 推断输出文件（在场景文件同目录下）
            base = os.path.splitext(os.path.basename(scenario_file))[0]
            result = RunResult(
                success=(proc.returncode == 0),
                return_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                scenario_file=scenario_file,
                aer_file=os.path.join(scenario_dir, base + ".aer"),
                evt_file=os.path.join(scenario_dir, base + ".evt"),
                csv_file=os.path.join(scenario_dir, base + ".csv"),
                duration_sec=elapsed,
            )

            if result.success:
                print(f"[AstraLogic] 仿真完成 ({elapsed:.2f}s)")
            else:
                print(f"[AstraLogic] 仿真失败 (code={proc.returncode})")

            return result

        except subprocess.TimeoutExpired:
            return RunResult(False, -1, "", f"超时 ({timeout}s)", scenario_file, "", "", "")
        except Exception as e:
            return RunResult(False, -1, "", str(e), scenario_file, "", "", "")


# ============================================================
# 结果解析器
# ============================================================

class ResultParser:
    """解析 AFSIM 输出文件"""

    @staticmethod
    def parse_evt(filepath: str) -> List[Dict]:
        """解析 .evt 文件"""
        events = []
        if not os.path.exists(filepath):
            return events

        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(None, 3)
                if len(parts) >= 2:
                    try:
                        events.append({
                            "time": float(parts[0]),
                            "event": parts[1],
                            "detail": parts[2] if len(parts) > 2 else ""
                        })
                    except ValueError:
                        continue

        print(f"[AstraLogic] 解析 {len(events)} 条事件 (evt)")
        return events

    @staticmethod
    def parse_csv(filepath: str) -> List[Dict]:
        """解析 .csv 文件"""
        events = []
        if not os.path.exists(filepath):
            return events

        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0].startswith('#'):
                    continue
                try:
                    events.append({
                        "time": float(row[0]),
                        "event": row[1] if len(row) > 1 else "",
                        "detail": ",".join(row[2:]) if len(row) > 2 else ""
                    })
                except (ValueError, IndexError):
                    continue

        print(f"[AstraLogic] 解析 {len(events)} 条事件 (csv)")
        return events

    @staticmethod
    def summary(events: List[Dict]) -> Dict:
        """统计摘要"""
        if not events:
            return {"total": 0}

        types = {}
        for e in events:
            t = e["event"]
            types[t] = types.get(t, 0) + 1

        return {
            "total": len(events),
            "types": types,
            "time_range": (events[0]["time"], events[-1]["time"]),
        }


# ============================================================
# 便捷函数
# ============================================================

def quick_run(satellites: List[Satellite],
              ground_stations: List[GroundStation] = None,
              messages: List[SimMessage] = None,
              config: SimConfig = None,
              scenario_name: str = "astra_quick") -> RunResult:
    """
    一步到位：生成场景 → 运行仿真 → 返回结果
    """
    config = config or SimConfig()

    builder = ScenarioBuilder(config)
    for s in satellites:
        builder.add_satellite(s)
    for g in (ground_stations or []):
        builder.add_ground_station(g)
    for m in (messages or []):
        builder.add_message(m)

    filename = f"{scenario_name}.txt"
    builder.build(filename)

    runner = SimRunner(config)
    return runner.run(filename)


# ============================================================
# 测试
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("AstraLogic - AFSIM Bridge 测试")
    print("=" * 50)

    config = SimConfig()
    print(f"AFSIM: {config.afsim_exe}")
    print(f"工作目录: {config.work_dir}")

    # 创建 1 颗卫星
    sat = Satellite(name="LEO_1", semi_major_axis=7000, inclination=45)

    # 生成场景
    builder = ScenarioBuilder(config)
    builder.add_satellite(sat)
    path = builder.build("bridge_test.txt")

    # 运行仿真
    runner = SimRunner(config)
    result = runner.run("bridge_test.txt")

    print(f"\n结果: {'成功' if result.success else '失败'}")
    print(f"耗时: {result.duration_sec:.2f}s")

    if result.success:
        parser = ResultParser()
        events = parser.parse_evt(result.evt_file)
        s = parser.summary(events)
        print(f"事件数: {s.get('total', 0)}")
        print(f"事件类型: {s.get('types', {})}")
