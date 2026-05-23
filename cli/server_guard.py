import sys
import time
import subprocess
import atexit

node_process = None

def start_node_server():
    global node_process
    print("🏭 [算力调度] 正在唤醒底层 Wasm 算力节点 (端口 3000)...")
    try:
        node_process = subprocess.Popen(
            ["node", "rpc_server/server.js"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1.5)
        print("✅ [算力调度] Wasm 节点引擎点火完毕！")
    except Exception as e:
        print(f"❌ [致命错误] 无法启动 Node 服务，请检查环境: {e}")
        sys.exit(1)

def cleanup():
    global node_process
    if node_process:
        print("\n🛑 [系统收尾] 正在切断 Wasm 算力节点电源...")
        node_process.terminate()
        node_process.wait()
        print("✅ [系统收尾] 所有资源清理完毕，贾维斯进入休眠。")

atexit.register(cleanup)