"""
OpenClaw Gateway 状态检测模块

提供 OpenClaw Gateway 运行状态、模型配置、响应延迟等信息的结构化检测。
支持 CLI 检测（check_gateway / full_status）和 HTTP API 检测（check_http_api / quick_status）。
"""

import subprocess
import json
import sys
import time
import socket
from datetime import datetime, timezone

__all__ = ["OpenClawStatus"]

# 尝试导入 requests，不可用时回退到 urllib
try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    _HAS_REQUESTS = False


class OpenClawStatus:
    """检测 OpenClaw Gateway 运行状态，返回结构化信息。"""

    def __init__(self, gateway_url="http://127.0.0.1:18789", token=None):
        """初始化，设置平台兼容的命令名。

        参数:
            gateway_url: Gateway HTTP API 地址，默认 http://127.0.0.1:18789
            token: 可选的 Bearer token，用于需要认证的 API 调用
        """
        self._cmd = "openclaw.cmd" if sys.platform == "win32" else "openclaw"
        self.gateway_url = gateway_url.rstrip("/")
        self.token = token

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _run(self, args: list[str], timeout: int = 15) -> subprocess.CompletedProcess:
        """安全执行 subprocess，统一超时和异常处理。"""
        return subprocess.run(
            [self._cmd, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )

    # ------------------------------------------------------------------
    # 公开检测方法
    # ------------------------------------------------------------------

    def check_gateway(self) -> dict:
        """检测 Gateway 是否在运行。

        返回:
            {"running": bool, "pid": int|None, "uptime": str|None, "error": str|None}
        """
        result: dict = {"running": False, "pid": None, "uptime": None, "error": None}

        # 快速路径：先用端口探测（毫秒级）
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            probe = sock.connect_ex(("127.0.0.1", 18789))
            sock.close()
            if probe == 0:
                result["running"] = True
                # 端口通了，跳过慢速 CLI 检测
                return result
        except Exception:
            pass

        # 慢速路径：调用 CLI
        try:
            proc = self._run(["gateway", "status"], timeout=20)
            output = proc.stdout.strip()

            # 尝试解析 JSON
            try:
                data = json.loads(output)
                result["running"] = bool(data.get("running", data.get("status") == "running"))
                result["pid"] = data.get("pid")
                result["uptime"] = data.get("uptime")
            except (json.JSONDecodeError, ValueError):
                # 回退：根据关键字判断
                lower = output.lower()
                if any(kw in lower for kw in ["running", "online", "rpc probe: ok", "listening:", "probe: ok"]):
                    result["running"] = True
                # 尝试提取 PID
                for line in output.splitlines():
                    if "pid" in line.lower():
                        for token in line.split():
                            if token.isdigit():
                                result["pid"] = int(token)
                                break

            if proc.returncode != 0 and not result["running"]:
                result["error"] = proc.stderr.strip() or f"exit code {proc.returncode}"

        except FileNotFoundError:
            result["error"] = f"命令 '{self._cmd}' 未找到，请确认已安装 OpenClaw CLI"
        except subprocess.TimeoutExpired:
            result["error"] = "检测超时 (10s)"
        except Exception as exc:
            result["error"] = str(exc)

        return result

    def check_model(self) -> dict:
        """获取当前配置的模型信息。

        返回:
            {"primary": str, "fallbacks": list[str], "error": str|None}
        """
        result: dict = {"primary": "", "fallbacks": [], "error": None}
        try:
            proc = self._run(["config", "get", "agents.defaults.model"], timeout=10)
            output = proc.stdout.strip()

            try:
                data = json.loads(output)
                if isinstance(data, str):
                    result["primary"] = data
                elif isinstance(data, dict):
                    result["primary"] = data.get("model", data.get("primary", ""))
                    result["fallbacks"] = data.get("fallbacks", [])
                elif isinstance(data, list) and data:
                    result["primary"] = data[0]
                    result["fallbacks"] = data[1:]
            except (json.JSONDecodeError, ValueError):
                # 纯文本输出视为模型名
                result["primary"] = output

            if proc.returncode != 0:
                result["error"] = proc.stderr.strip() or f"exit code {proc.returncode}"

        except FileNotFoundError:
            result["error"] = f"命令 '{self._cmd}' 未找到"
        except subprocess.TimeoutExpired:
            result["error"] = "检测超时 (10s)"
        except Exception as exc:
            result["error"] = str(exc)

        return result

    def ping(self) -> dict:
        """测量 agent 响应延迟（毫秒）。

        返回:
            {"latency_ms": int, "success": bool, "error": str|None}
        """
        result: dict = {"latency_ms": -1, "success": False, "error": None}
        try:
            import uuid
            ping_session = f"ping-{uuid.uuid4().hex[:8]}"
            start = time.monotonic()
            proc = self._run(
                ["agent", "--session-id", ping_session, "--message", "ping", "--json"],
                timeout=60,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)
            result["latency_ms"] = elapsed_ms

            if proc.returncode == 0:
                result["success"] = True
            else:
                # 即使返回非零，如果有 stdout 输出也算部分成功
                if proc.stdout.strip():
                    result["success"] = True
                else:
                    result["error"] = proc.stderr.strip() or f"exit code {proc.returncode}"

        except FileNotFoundError:
            result["error"] = f"命令 '{self._cmd}' 未找到"
        except subprocess.TimeoutExpired:
            result["latency_ms"] = 60000
            result["error"] = "ping 超时 (60s)"
        except Exception as exc:
            result["error"] = str(exc)

        return result

    def full_status(self) -> dict:
        """一次性获取所有状态。

        返回:
            {
                "gateway": {...},
                "model": {...},
                "ping": {...},
                "overall": "online" | "degraded" | "offline",
                "checked_at": str (ISO 时间)
            }
        """
        gateway = self.check_gateway()
        model = self.check_model()
        ping = self.ping()

        # overall 判断
        if gateway["running"] and ping["success"]:
            overall = "online"
        elif gateway["running"]:
            overall = "online"  # Gateway 在线就算 online，ping 失败可能是模型慢
        else:
            overall = "offline"

        return {
            "gateway": gateway,
            "model": model,
            "ping": ping,
            "overall": overall,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # 格式化输出
    # ------------------------------------------------------------------

    @staticmethod
    def status_emoji(overall: str) -> str:
        """返回状态对应的 emoji。"""
        emoji_map = {"online": "🟢", "degraded": "🟡", "offline": "🔴"}
        return emoji_map.get(overall, "⚪")

    def format_status(self, status: dict) -> str:
        """格式化为可读的 Markdown 文本。"""
        overall = status.get("overall", "unknown")
        emoji = self.status_emoji(overall)
        checked = status.get("checked_at", "N/A")

        gw = status.get("gateway", {})
        model = status.get("model", {})
        ping = status.get("ping", {})

        lines = [
            f"# {emoji} OpenClaw 状态: {overall.upper()}",
            "",
            f"**检测时间:** {checked}",
            "",
            "## Gateway",
            f"- 运行: {'✅ 是' if gw.get('running') else '❌ 否'}",
        ]
        if gw.get("pid"):
            lines.append(f"- PID: `{gw['pid']}`")
        if gw.get("uptime"):
            lines.append(f"- 运行时间: {gw['uptime']}")
        if gw.get("error"):
            lines.append(f"- ⚠️ 错误: {gw['error']}")

        lines += [
            "",
            "## 模型配置",
            f"- 主模型: `{model.get('primary') or 'N/A'}`",
        ]
        if model.get("fallbacks"):
            lines.append(f"- 备用模型: `{'`, `'.join(model['fallbacks'])}`")
        if model.get("error"):
            lines.append(f"- ⚠️ 错误: {model['error']}")

        lines += [
            "",
            "## Ping",
            f"- 延迟: `{ping.get('latency_ms', -1)}ms`",
            f"- 状态: {'✅ 成功' if ping.get('success') else '❌ 失败'}",
        ]
        if ping.get("error"):
            lines.append(f"- ⚠️ 错误: {ping['error']}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # HTTP API 检测（纯 HTTP，不调 CLI）
    # ------------------------------------------------------------------

    def _http_get_json(self, url: str, timeout: int = 5, token: str | None = None) -> tuple[int, dict | None, str | None]:
        """发起 GET 请求并解析 JSON，返回 (status_code, data, error)。"""
        tok = token if token is not None else self.token
        headers = {}
        if tok:
            headers["Authorization"] = f"Bearer {tok}"

        if _HAS_REQUESTS:
            resp = _requests.get(url, headers=headers, timeout=timeout)
            return resp.status_code, resp.json() if resp.text.strip() else None, None
        else:
            req = urllib.request.Request(url, headers=headers, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    body = resp.read().decode("utf-8")
                    data = json.loads(body) if body.strip() else None
                    return resp.status, data, None
            except urllib.error.HTTPError as exc:
                return exc.code, None, str(exc)
            except Exception as exc:
                return -1, None, str(exc)

    def check_http_api(self, gateway_url=None, token=None) -> dict:
        """检测 HTTP API 是否可用。

        参数:
            gateway_url: API 地址，默认使用 self.gateway_url
            token: Bearer token，默认使用 self.token

        返回:
            {"available": bool, "models": list[str], "latency_ms": int, "error": str|None}
        """
        url = (gateway_url or self.gateway_url).rstrip("/")
        tok = token if token is not None else self.token
        result: dict = {"available": False, "models": [], "latency_ms": -1, "error": None}

        try:
            start = time.monotonic()
            status_code, data, err = self._http_get_json(f"{url}/v1/models", token=tok)
            result["latency_ms"] = int((time.monotonic() - start) * 1000)

            if err:
                result["error"] = err
                return result

            if status_code == 200 and isinstance(data, dict) and "data" in data:
                result["available"] = True
                result["models"] = [
                    m.get("id", str(m)) for m in data["data"] if isinstance(m, dict)
                ]
            elif status_code == 200 and isinstance(data, list):
                # 某些版本直接返回 list
                result["available"] = True
                result["models"] = [m.get("id", str(m)) if isinstance(m, dict) else str(m) for m in data]
            else:
                result["error"] = f"HTTP {status_code}"
        except Exception as exc:
            result["error"] = str(exc)

        return result

    def quick_status(self, gateway_url=None, token=None) -> dict:
        """快速检测状态，不调用任何 CLI 进程。

        参数:
            gateway_url: API 地址，默认使用 self.gateway_url
            token: Bearer token，默认使用 self.token

        返回:
            {
                "gateway_online": bool,
                "http_api_available": bool,
                "models": list[str],
                "gateway_latency_ms": int,
                "api_latency_ms": int,
                "overall": "online" | "api_offline" | "offline",
                "checked_at": str (ISO 时间)
            }
        """
        url = (gateway_url or self.gateway_url).rstrip("/")
        tok = token if token is not None else self.token
        result: dict = {
            "gateway_online": False,
            "http_api_available": False,
            "models": [],
            "gateway_latency_ms": -1,
            "api_latency_ms": -1,
            "overall": "offline",
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        # 1. Socket 端口探测
        try:
            # 从 URL 解析 host 和 port
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 18789

            start = time.monotonic()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            probe = sock.connect_ex((host, port))
            sock.close()
            result["gateway_latency_ms"] = int((time.monotonic() - start) * 1000)
            result["gateway_online"] = (probe == 0)
        except Exception:
            result["gateway_online"] = False

        # 2. HTTP API 探测（仅当端口可达时）
        if result["gateway_online"]:
            api = self.check_http_api(url, tok)
            result["http_api_available"] = api["available"]
            result["models"] = api["models"]
            result["api_latency_ms"] = api["latency_ms"]

        # 3. overall 判断
        if result["gateway_online"] and result["http_api_available"]:
            result["overall"] = "online"
        elif result["gateway_online"]:
            result["overall"] = "api_offline"
        else:
            result["overall"] = "offline"

        return result

    @staticmethod
    def format_quick_status(status: dict) -> str:
        """将 quick_status 返回值格式化为 Markdown。

        参数:
            status: quick_status() 返回的 dict

        返回:
            Markdown 格式的状态文本
        """
        overall = status.get("overall", "unknown")
        emoji_map = {"online": "🟢", "api_offline": "🟡", "offline": "🔴"}
        emoji = emoji_map.get(overall, "⚪")
        checked = status.get("checked_at", "N/A")

        gw_online = status.get("gateway_online", False)
        api_avail = status.get("http_api_available", False)
        models = status.get("models", [])
        gw_lat = status.get("gateway_latency_ms", -1)
        api_lat = status.get("api_latency_ms", -1)

        lines = [
            f"# {emoji} OpenClaw 快速状态: {overall.upper()}",
            "",
            f"**检测时间:** {checked}",
            "",
            "## Gateway",
            f"- 端口探测: {'✅ 在线' if gw_online else '❌ 离线'}",
            f"- 延迟: `{gw_lat}ms`",
            "",
            "## HTTP API",
            f"- 状态: {'✅ 可用' if api_avail else '❌ 不可用'}",
            f"- 延迟: `{api_lat}ms`",
        ]

        if models:
            lines += [
                "",
                "## 可用模型",
            ]
            for m in models:
                lines.append(f"- `{m}`")
        elif api_avail:
            lines += ["", "## 可用模型", "- （无模型）"]

        return "\n".join(lines)


# ======================================================================
# 测试入口
# ======================================================================
if __name__ == "__main__":
    # Windows 控制台 UTF-8 支持
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    checker = OpenClawStatus()

    # === 快速状态检测 ===
    print("=== 快速状态检测 (quick_status) ===")
    qs = checker.quick_status()
    print(json.dumps(qs, indent=2, ensure_ascii=False))
    print()
    print(checker.format_quick_status(qs))
    print()

    # === 完整状态检测 ===
    status = checker.full_status()

    # 打印 JSON
    print("=== JSON 输出 ===")
    print(json.dumps(status, indent=2, ensure_ascii=False))
    print()

    # 打印 Markdown
    print("=== Markdown 格式 ===")
    print(checker.format_status(status))
