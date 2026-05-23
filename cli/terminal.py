import json
import os

import requests

from cli.server_guard import start_node_server, node_process
from core.config import config


def terminal_chat_mode():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("==================================================")
    print("💬 [终端直连模式] 战术通讯链路已激活")
    print("💡 提示: 输入 '/exit' 或 '/quit' 撤退。")
    print("==================================================")

    try:
        if node_process is None:
            start_node_server()

        engine = start_node_server()
        print("⏳ 正在开辟专属测试频段...")
        session_id = engine.create_new_chat_session()
        parent_id = None
        print(f"✅ 频段建立完毕 (ID: {session_id[:8]}...)！开始通讯。\n")

        while True:
            user_input = input("🧑‍💻 极客提问: ").strip()
            if not user_input: continue
            if user_input.lower() in ['/exit', '/quit']:
                print("\n👋 结束通讯，正在切断链路...")
                engine.delete_chat_session(session_id)
                break

            print("🤖 Jarvis: ", end="", flush=True)
            combat_headers = engine.get_combat_headers()
            payload = {"chat_session_id": session_id, "parent_message_id": parent_id, "prompt": user_input,
                       "thinking_enabled": False, "ref_file_ids": []}

            with requests.post(f"{config.DS_API_BASE}/completion", headers=combat_headers, json=payload, stream=True,
                               timeout=60) as response:
                if response.status_code != 200:
                    print(f"\n[💥 敌方拦截: HTTP {response.status_code}]")
                    continue
                for line in response.iter_lines():
                    if not line: continue
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[6:]
                        if not data_str or data_str == "{}" or data_str == "[DONE]": continue
                        try:
                            chunk = json.loads(data_str)
                            if isinstance(chunk, dict):
                                if "response_message_id" in chunk:
                                    parent_id = chunk["response_message_id"]
                                elif "v" in chunk and isinstance(chunk["v"], dict) and "message_id" in chunk["v"].get(
                                        "response", {}):
                                    parent_id = chunk["v"]["response"]["message_id"]
                                elif "v" in chunk and isinstance(chunk["v"], str) and (
                                        chunk.get("p") is None or "content" in str(chunk.get("p"))):
                                    print(chunk["v"], end="", flush=True)
                        except json.JSONDecodeError:
                            pass
            print("\n" + "-" * 50)
    except KeyboardInterrupt:
        print("\n\n⚠️ 检测到强制中断，撤退。")
    except Exception as e:
        print(f"\n❌ [通讯故障] {e}")

    input("\n按回车键返回主控中枢...")
    return  # 👈 优雅退出，而非递归调用菜单
