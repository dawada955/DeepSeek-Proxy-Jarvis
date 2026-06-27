# config.py
import os

class Settings:
    # ---------------- 基础网关配置 ----------------
    HOST = "0.0.0.0"
    PORT = 8888

    # ---------------- 外部兵工厂配置 ----------------
    NODE_RPC_URL = "http://127.0.0.1:3099/api/solve_pow"

    # ---------------- DeepSeek 官方接口配置 ----------------
    DS_API_BASE = "https://chat.deepseek.com/api/v0/chat"
    DS_SESSION_CREATE_URL = "https://chat.deepseek.com/api/v0/chat_session/create"

    # 伪装指纹
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    DEFAULT_HIF_LEIM = "tdmrKLrjcb+V82V1ejErlCxVbz2CFO5sBBT8Z+pYif09FKESBn0xt2k=.TZ+mk7ilbl5PhjHX"

config = Settings()