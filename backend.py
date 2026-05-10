# backend.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

app = FastAPI()

# 允许 Streamlit 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    tools_used: list = []
    execution_time: float = 0

@app.post("/api/agent/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """与 Agent 对话"""
    import time
    start_time = time.time()
    
    # 这里调用你的 OpenClaw Agent
    # from openclaw_agent import SatelliteAgent
    # agent = SatelliteAgent()
    # response = await agent.think(request.message)
    
    # 临时模拟响应
    response = f"""
    收到您的请求："{request.message}"
    
    ## 分析结果
    
    基于当前仿真状态：
    - **源卫星**: Sat-A (LEO, 550km)
    - **目标卫星**: Sat-B (MEO, 1200km)
    - **当前链路状态**: 正常
    
    ## 建议操作
    
    1. 保持当前发射功率 30 dBm
    2. 链路余量充足 (8.5 dB)
    3. 无需切换备用链路
    
    ---
    *执行工具: analyze_link_quality, optimize_power*
    """
    
    execution_time = time.time() - start_time
    
    return ChatResponse(
        response=response,
        tools_used=["analyze_link_quality", "optimize_power"],
        execution_time=execution_time
    )

@app.get("/api/satellites")
async def get_satellites():
    """获取卫星列表"""
    return {
        "satellites": [
            {"id": "Sat-A", "altitude": 550, "status": "online"},
            {"id": "Sat-B", "altitude": 1200, "status": "online"},
            {"id": "Sat-C", "altitude": 35786, "status": "offline"},
            {"id": "Sat-D", "altitude": 800, "status": "online"},
        ]
    }

@app.get("/api/simulation/status")
async def get_simulation_status():
    """获取仿真状态"""
    return {
        "running": True,
        "elapsed_time": 120.5,
        "active_links": 2,
        "metrics": {
            "avg_snr": 23.5,
            "throughput": 95.3,
            "latency": 45
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)