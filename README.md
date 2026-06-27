# DeepSeek Jarvis Proxy V2.2

OpenAI 兼容的 DeepSeek Chat API 代理网关。通过浏览器自动登录、PoW 工作量证明计算、SSE 流式转发，将 DeepSeek 官方聊天接口包装为标准的 OpenAI API 格式，支持多租户 API Key 管理。

## 架构

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  API 客户端   │────▶│  FastAPI 网关     │────▶│  DeepSeek 官方 API   │
│ (OpenAI SDK) │     │  :8888           │     │  chat.deepseek.com  │
└─────────────┘     └───────┬──────────┘     └─────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │  Node.js PoW RPC :3099    │
              │  (WASM 工作量证明求解器)    │
              └───────────────────────────┘
              ┌───────────────────────────┐
              │  SQLite 多租户 DB          │
              │  (API Key + 用量管理)      │
              └───────────────────────────┘
```

| 组件 | 技术栈 | 说明 |
|------|--------|------|
| API 网关 | Python 3.11 + FastAPI + Uvicorn | OpenAI 兼容接口，SSE 流式转发 |
| PoW 求解器 | Node.js + Express + WASM | 从 DeepSeek 提取的 PoW 算法，端口 3099 |
| 鉴权引擎 | DrissionPage + Chrome | 浏览器自动化登录，LocalStorage 令牌捕获 |
| 管理面板 | FastAPI + Jinja2 模板 | API Key 发放、用量统计仪表盘 |

## 前置依赖

| 工具 | 最低版本 | 用途 |
|------|----------|------|
| Python | 3.11+ | API 网关后端 |
| Node.js | 18+ | PoW 工作量证明 RPC |
| Chrome / Chromium | 最新稳定版 | 浏览器自动化登录（DrissionPage） |

## 快速开始

```bash
# 1. 克隆仓库
git clone <repo-url>
cd DeepSeek-Proxy-Jarvis

# 2. 一键安装（创建 venv、安装依赖、生成配置模板）
python install.py   # 跨平台（推荐）
# 或 ./setup.sh / setup.bat

# 3. 启动
./start.sh        # Linux / macOS
# 或
start.bat         # Windows
```

首次启动时，程序会自动打开 Chrome 浏览器窗口，在窗口中扫码或登录你的 DeepSeek 账号，令牌将自动保存到本地 `auth_config.json`（此文件不会提交到 Git）。

## 项目结构

```
DeepSeek-Proxy-Jarvis/
├── main.py                    # 入口：交互菜单 + uvicorn 启动
├── api/
│   ├── routes.py              # /v1/chat/completions 等核心 API
│   ├── dashboard.py           # Web 管理面板路由
│   └── utils.py               # API 工具函数
├── core/
│   ├── auth_manager.py        # DrissionPage 浏览器鉴权引擎
│   ├── config.py              # 全局配置（host/port/URL）
│   ├── ds_engine.py           # DeepSeek 请求编排
│   ├── gc_manager.py          # 异步垃圾桶清道夫
│   └── metrics_db.py          # SQLite 多租户数据库
├── cli/
│   ├── terminal.py            # 终端交互式聊天模式
│   └── server_guard.py        # Node.js PoW 服务器守护进程
├── rpc_server/
│   ├── server.js              # Express RPC 服务（端口 3099）
│   ├── deepseek_worker_adapted.js  # WASM Worker 适配器
│   └── pom_ds_code/           # 从 DeepSeek 提取的 WASM + JS
├── install.py                  # 跨平台一键安装（推荐）
├── setup.sh / setup.bat       # 安装快捷方式
├── start.sh / start.bat       # 启动脚本
├── requirements.txt           # Python 依赖
├── auth_config.json.example   # 凭据模板（复制为 auth_config.json）
└── ds_browser_profile/        # Chrome 用户数据（Git 忽略）
```

## API 端点

### 对话补全（OpenAI 兼容）

```
POST /v1/chat/completions
Authorization: Bearer sk-jarvis-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json

{
  "model": "deepseek-chat",
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "stream": true
}
```

### 管理面板

```
http://localhost:8888/dashboard
```

- 创建 / 管理 API Key（`sk-jarvis-*`）
- 查看各 Key 的对话次数与 token 用量
- 鉴权模式：面板独立的账号密码登录

## 换设备使用

项目已实现跨设备可移植：

1. **虚拟环境独立** — 每台设备通过 `setup` 脚本创建本地 venv
2. **凭据不入库** — `auth_config.json` 在 `.gitignore` 中，每台设备独立登录
3. **数据库不入库** — `*.db` 文件被忽略，每台设备有独立的运行时数据
4. **IDE 配置不入库** — `.idea/` 被忽略，不携带个人编辑器配置

换到新设备只需 `git clone` → `./setup.sh` → `./start.sh` 三步。

## 交互菜单

启动后提供 4 个选项：

```
==================================================
🦾 欢迎使用 DeepSeek Jarvis 算力接管网关 V2.2
==================================================
  1. 🌐 启动网关服务
  2. 💬 终端直连测试
  3. 💥 战术核平销毁（清理账号与本地缓存）
  4. 🚪 关闭系统
==================================================
```

也可直接跳过菜单，以 API 模式启动：

```bash
python main.py --api
```

## 技术要点

- **PoW 签名**：Node.js 端加载从 DeepSeek 前端提取的 WASM 二进制，计算 X-DS-Pow-Response 请求头，Python 端通过 HTTP RPC 调用
- **SSE 透传**：FastAPI 使用 `sse-starlette` 将 DeepSeek 的 SSE 事件流逐块转发给客户端
- **Token 刷新**：`auth_manager.py` 检测到凭据过期/缺失时，自动启动 Chrome 浏览器，轮询监听 `localStorage.userToken` 直到用户登录成功
- **垃圾回收**：后台异步任务每 180 秒清理过期的临时文件/缓存

## 许可证

仅供学习研究使用，请遵守 DeepSeek 的服务条款。
