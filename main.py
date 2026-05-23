# main.py
import os
import sys
import time
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import config
from core.auth_manager import force_logout
from api.routes import router, get_engine_and_gc
from cli.server_guard import start_node_server
from cli.terminal import terminal_chat_mode

from api.routes import router as chat_router
from api.dashboard import router as dash_router

# ==========================================
# 🪐 挂载微服务生命周期总线
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🟢 阶段一：当 FastAPI 启动完毕后，自动激活 GC 的异步轮询清道夫
    _, gc_manager, metrics_db = get_engine_and_gc()

    # 挂载巡逻任务（这里设定为每 180 秒/3分钟，自动清洗一次本地垃圾箱）
    gc_task = asyncio.create_task(gc_manager.start_patrol(interval_seconds=180))

    yield  # Web 网关服务在此区间持续提供对外的无状态穿透业务

    # 🔴 阶段二：当网关关闭或 CTRL+C 终止时，强制安全切断清道夫线圈
    print("🛑 [主控中枢] 正在注销异步清理常驻任务...")
    gc_task.cancel()
    try:
        await gc_task
    except asyncio.CancelledError:
        print("✅ [主控中枢] 清道夫异步任务已安全撤离。")


# ==========================================
# 🏛️ 代理服务网关框架声明
# ==========================================
app = FastAPI(title="DeepSeek Jarvis Proxy V2.2", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载高度聚合的干净子域控制路由
app.include_router(router)

# 挂载路由
app.include_router(chat_router)
app.include_router(dash_router)

def interactive_menu():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("==================================================")
        print("🦾 欢迎使用 DeepSeek Jarvis 算力接管网关 V2.2 (无状态解耦版)")
        print("==================================================")
        print("  1. 🌐 启动网关服务 (高内聚微服务阵列点火)")
        print("  2. 💬 终端直连测试 (控制台内极速聊天测试)")
        print("  3. 💥 战术核平销毁 (清理账号与本地缓存)")
        print("  4. 🚪 关闭系统")
        print("==================================================")

        choice = input("\n请下达指令编号 (1/2/3/4): ").strip()

        if choice == "1":
            print("\n⏳ 正在执行起飞程序...")
            start_node_server()
            print("🔋 [主控中枢] 正在初始化凭证与垃圾回收引擎...")
            get_engine_and_gc()
            print(f"\n==================================================")
            print(f"🟢 网关微服务就绪！异步清道夫后台并轨运行中...")
            print(f"🔗 数据面板: http://{config.HOST}:{config.PORT}/dashboard")
            print(f"🔑 鉴权模式: [多租户数据库接管] 请前往 Dashboard 获取/管理 API Key")
            print(f"==================================================\n")
            uvicorn.run("main:app", host=config.HOST, port=config.PORT, log_level="warning")
            break

        elif choice == "2":
            terminal_chat_mode()
        elif choice == "3":
            force_logout()
            input("\n按回车键继续...")
        elif choice == "4":
            print("👋 指挥官再见！")
            sys.exit(0)
        else:
            print("❌ 无效的指令！")
            time.sleep(1)


if __name__ == "__main__":
    if "--api" in sys.argv:
        start_node_server()
        uvicorn.run("main:app", host=config.HOST, port=config.PORT, log_level="warning")
    else:
        interactive_menu()