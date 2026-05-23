# ds_engine.py
import requests
import json
import base64
from core.config import config
from core.auth_manager import get_valid_auth


class DeepSeekEngine:
    def __init__(self):
        self.auth_data = get_valid_auth()

    def _get_base_headers(self):
        """构造基础的维生 Headers"""
        return {
            "Authorization": self.auth_data["Authorization"],
            "Cookie": self.auth_data["Cookie"],
            "Content-Type": "application/json",
            "User-Agent": config.DEFAULT_USER_AGENT,
            "x-hif-leim": config.DEFAULT_HIF_LEIM
        }

    def create_new_chat_session(self):
        """向 DS 申请全新的对话频段"""
        response = requests.post(
            config.DS_SESSION_CREATE_URL,
            headers=self._get_base_headers(),
            json={}
        )
        if response.status_code != 200:
            raise Exception(f"申请新频段失败: {response.text}")

        data = response.json()
        biz_data = data.get("data", {}).get("biz_data", {})

        # 兼容不同格式的 ID 提取
        session_id = biz_data.get("chat_session", {}).get("id") or biz_data.get("id")
        if not session_id:
            raise Exception("无法解析 Session ID")
        return session_id

    def update_session_title(self, session_id: str, title: str) -> bool:
        import re
        match = re.match(r'(https://[^/]+/api/v0)', config.DS_API_BASE)
        base_url = match.group(1) if match else "https://chat.deepseek.com/api/v0"
        url = f"{base_url}/chat_session/update_title"

        combat_headers = self.get_combat_headers()
        payload = {
            "chat_session_id": session_id,
            "title": title
        }
        try:
            response = requests.post(url, headers=combat_headers, json=payload, timeout=10)

            if response.status_code == 200:
                res_json = response.json()
                if res_json.get("code") == 0:
                    print(f"🏷️  [会话打标] 成功将官方会话重命名为: {title}")
                    return True
            print(f"⚠️ [会话打标] 失败！请参考上方透视日志。")
        except Exception as e:
            print(f"❌ [调试重命名] 请求彻底崩溃: {e}")
            print("═" * 60 + "\n")

        return False

    def generate_pow_header(self):
        """【黑盒作战】一条龙：拿题 -> 丢给Node算力 -> 组装成最终 Header 值"""
        headers = self._get_base_headers()

        # 1. 拿题
        resp = requests.post(
            f"{config.DS_API_BASE}/create_pow_challenge",
            headers=headers,
            json={"target_path": "/api/v0/chat/completion"}
        )
        challenge_data = resp.json()["data"]["biz_data"]["challenge"]

        # 2. 调用本地 Node 兵工厂
        rpc_payload = {
            "algorithm": challenge_data["algorithm"],
            "challenge": challenge_data["challenge"],
            "salt": challenge_data["salt"],
            "signature": challenge_data["signature"],
            "difficulty": challenge_data["difficulty"],
            "expireAt": challenge_data["expire_at"]
        }
        rpc_resp = requests.post(config.NODE_RPC_URL, json=rpc_payload).json()
        if rpc_resp["status"] != "success":
            raise Exception("兵工厂计算崩溃")

        # 3. 组装最终防伪印章
        pow_dict = {
            "algorithm": challenge_data["algorithm"],
            "challenge": challenge_data["challenge"],
            "salt": challenge_data["salt"],
            "answer": rpc_resp["data"]["answer"],
            "signature": challenge_data["signature"],
            "target_path": "/api/v0/chat/completion"
        }
        pow_json_str = json.dumps(pow_dict, separators=(',', ':'))
        return base64.b64encode(pow_json_str.encode('utf-8')).decode('utf-8')

    def delete_chat_session(self, session_id):
        """【幽灵协议】阅后即焚：彻底抹除服务器上的会话痕迹"""
        print(f"🧹 [幽灵协议] 正在静默销毁服务器痕迹 (Session: {session_id[:8]}...)")
        try:
            # DS 官方的删除会话接口
            delete_url = "https://chat.deepseek.com/api/v0/chat_session/delete"
            payload = {"chat_session_id": session_id}

            response = requests.post(
                delete_url,
                headers=self._get_base_headers(),
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                print(f"✅ [幽灵协议] 痕迹抹除成功！深海之中再无此记录。")
            else:
                print(f"⚠️ [幽灵协议] 抹除失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"⚠️ [幽灵协议] 抹除请求异常: {e}")

    def get_combat_headers(self):
        """生成对抗风控的伪装请求头 (配置驱动版)"""
        headers = self._get_base_headers()

        # 从外部配置注入易变的指纹特征
        headers.update({
            "x-app-version": getattr(config, "DS_APP_VERSION", "2.0.0"),
            "x-client-version": getattr(config, "DS_CLIENT_VERSION", "2.0.0"),
            "x-client-platform": getattr(config, "DS_CLIENT_PLATFORM", "web"),

            "x-client-locale": "en_US",
            "x-client-timezone-offset": "28800",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin"
        })

        # 组装 POW 签名
        headers["x-ds-pow-response"] = self.generate_pow_header()
        return headers
