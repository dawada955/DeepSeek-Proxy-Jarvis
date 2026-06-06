# 🦾 Jarvis DeepSeek Proxy Gateway (V2.5)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

Jarvis 算力接管网关是一个专为极客与私有化部署设计的 **企业级多租户 DeepSeek 网页端逆向中继网关**。项目基于纯 Python 异步生态（FastAPI + HTTPX）构建，在数据链路层全量捕获并全穿透官方 Web 端极其严苛的专属协议碎片，无缝封装并无损转化为 **OpenAI 标准 API 规范接口**。

通过与本地 Node.js 算力兵工厂并轨，网关具备自动解密 Wasm 级别工作量证明（PoW）及欺骗全新一代 **DeepSeek V4 & V4 Pro** 客户端指纹的对抗风控实力。同时，系统内嵌高性能的多租户 SQLite 账单精算引擎，并提供了一套极致美观、单屏防溢出、支持移动端响应式的白天模式数据监控观测台。

---

## ✨ 核心战术特性

### 1. 🛡️ 深度对抗官方风控层 (Anti-Bot Protocol)
* **动态 PoW 接管**：全自动拦截官方 `/create_pow_challenge` 频段，热拉起本地 Node.js 算力兵工厂进行黑盒加密盐值（DeepSeekHashV1）破解，无损组装 `x-ds-pow-response` 签名。
* **V4 护照指纹伪装**：全面对齐新一代 V4/V4 Pro 的反爬风控协议，动态注入官方 `2.0.0` 级别的客户端版本暗号（`x-app-version`, `x-client-version`, `x-client-platform`），打破客户端过期拦截。

### 2. 🧠 原生双轨思维链分流 (Pure OpenAI CoT)
* **协议原教旨主义**：彻底摒弃在正文中强插 XML 标签的污染做法。网关全量拦截官方自定义的“碎片状态机（Fragment State Machine）”，完美适配思考（`THINK`）与正式回答（`RESPONSE`）的状态跃迁。
* **SillyTavern 原生折叠**：无论是流式传输（Stream）还是非流式全量打包（Block），思维链数据均被精准抽离并灌入标准协议的 `reasoning_content` 槽位，使酒馆（ST）等主流前端能原生触发科技感十足的灰底折叠框。

### 3. 👥 多租户动态鉴权与项目隔离
* **数据库驱动**：废弃了传统的静态写死配置。网关直连本地轻量级 SQLite 数据库，实现运行时 API Key 项目的动态创建、挂载、吊销与实时校验。
* **无状态会话 GC（幽灵协议）**：延续了贾维斯经典的无状态对话树管理。每次调用在后台独立申请官方 Session，请求结束后通过跨周期异步垃圾池常驻任务（`GCManager`）触发官方 `delete` 幽灵协议，阅后即焚，服务器不留痕迹。

### 4. 📊 现代商业级白天模式观测台 (Observability Dashboard)
* **单屏极致 UX**：基于 CSS Flexbox 弹性布局锁定 `100vh` 全屏，彻底杜绝数据大盘的外侧溢出滚动，数据高密度内聚，打造完美的全面屏盯盘体验。
* **移动端响应式 (Android/iOS)**：内嵌 `@media` 智能媒体查询。在安卓或手机浏览器访问时，控制栏与多维图表自动塌陷为垂直堆叠瀑布流，操作触控区全屏放大。
* **精算级多维账单**：
  * 支持 **日账单、周账单、选中月账单、历史累计账单** 的分段精算展示。
  * 内置分轨价格配置器，支持在前端直接修改并在本地存储（LocalStorage）**Instant (V4) / Expert (V4 Pro)** 的输入/输出差异化费率，一键保存实时刷新。
* **高密度双向流速图**：
  * **Token 吞吐趋势图**：按“日”合并聚合上下行 Token。鼠标悬停时弹出的悬浮窗会显示那一天的平均首字延迟（TTFT）与总耗时。
  * **请求频次流速图**：实时描绘 Req/日 的流速面积图，并引入坐标轴最低 5 次请求的阻尼器，防止单次请求撑破图表。

---

## 📂 项目模块高内聚架构

```text
jarvis-proxy/
├── api/
│   ├── routes.py          # 算力路由核心：租户动态鉴权、流式/阻塞双通道分流、TTFT掐表埋点
│   ├── dashboard.py       # 前端中枢：多租户增删改查 RESTful API、白天响应式单页面交付
│   └── utils.py           # 载荷处理组件
├── core/
│   ├── config.py          # 基础维生、外部兵工厂与指纹特征静态配置
│   ├── ds_engine.py       # 黑盒作战引擎：拿题、会话申请、POW签名组装、官方会话打标
│   ├── gc_manager.py      # 清道夫轮训：常驻后台的异步对话销毁队列
│   ├── auth_manager.py    # 凭证维生与会话管理
│   └── metrics_db.py      # SQLite持久化：多租户项目管理、账单日/周/月/总多维SQL精算引擎
├── cli/
│   ├── server_guard.py    # 守护进程管理
│   └── terminal.py        # 控制台极速调试模块
├── main.py                # 微服务生命周期总线、主控交互式菜单
└── server.js              # Node.js Wasm 逆向算力兵工厂服务

```

---

## 🚀 部署与点火教程

### 💻 PC/服务器端部署

1. **环境克隆与依赖并轨**：
```bash
git clone [https://github.com/your-repo/jarvis-proxy.git](https://github.com/your-repo/jarvis-proxy.git)
cd jarvis-proxy
pip install fastapi uvicorn httpx pydantic

```


2. **配置指纹**：
在 `core/config.py` 中，根据需要配置端口，并确保已在本地启动运行在 `3000` 端口的 `server.js` 算力解密服务。
3. **主控菜单起飞**：
```bash
python main.py

```


在弹出的交互式控制台菜单中按下 `1`，网关即全面并轨点火。

---

### 📱 安卓 Termux 便携服务器部署

得益于项目的低依赖高解耦架构，您可以将闲置的安卓设备改造成 24 小时低功耗算力批发枢纽：

1. **环境初始化 (F-Droid 下载最新 Termux)**：
```bash
termux-change-repo  # 勾选国内清华镜像源加速
pkg update && pkg upgrade -y
pkg install python nodejs git make clang nano -y

```


2. **依赖包加固**：
```bash
pip install --upgrade pip
pip config set global.index-url [https://pypi.tuna.tsinghua.edu.cn/simple](https://pypi.tuna.tsinghua.edu.cn/simple)
pip install fastapi uvicorn httpx pydantic

```


3. **穿透配置修改**：
打开 `core/config.py`，将 `HOST` 强制暴露修改为 `0.0.0.0`：
```python
HOST = "0.0.0.0"  # 允许全网/局域网内其他客户端接入
PORT = 8080

```


4. **后台守护点火**：
```bash
node server.js &        # 算力后台挂载
python main.py --api    # 生产模式极速运行

```



---

## 🛠️ 生产环境接入规范

### 1. 访问控制台生成密钥

访问网关的专属看板：`http://[您的服务器IP]:8080/dashboard`。
在右下角的 **🔑 API 租户管理** 控制台中，点击“+ 新建”创建一个项目（如：`酒馆专用`）。系统将利用内置的 UUID 算法在数据库中动态生成并持久化一把专属密钥：

```text
sk-jarvis-e1b2c3f4a5b6c7d8

```

### 2. 客户端接入配置（以 SillyTavern / Chatbox 为例）

在支持 OpenAI 格式的客户端中完成以下参数对称：

* **API 基础地址 (API Base)**：`http://[您的服务器IP]:8080/v1`
* **API 密钥 (API Key)**：`sk-jarvis-e1b2c3f4a5b6c7d8`（直接填入刚生成的租户密钥）
* **模型名称 (Model Name)**：根据算力路由，网关提供四大功能排列模型，客户端可按需手填：
* `deepseek-instant`：基础极速版 (官方 V4)
* `deepseek-instant-think`：极速版 + 原生思维链适配 (V4 + R1)
* `deepseek-expert`：高级专家版 (官方 V4 Pro 算力)
* `deepseek-expert-think`：满血终极版 (V4 Pro 算力 + 原生 R1 深度思考思维链)



---

## ⚖️ 计费核算免责声明

网关内嵌的账单管理系统仅用于量化和评估本地算力消耗和请求流速趋势。由于网页端不提供官方 Token 审计数据，系统中的输入/输出 Token 消耗量是由网关对文本字符长度（Length）进行的高稳定近似模拟计算得来。请根据实际需求和计价规则动态调整单价配置器中的系数。

---

*Commanded by Jarvis. Built for Engineering Aesthetics.*

```

这份文档不仅完整记录了我们项目的技术亮点，还为之后可能的使用者（包括你自己在换新环境部署时）提供了完美的指引。直接保存它，我们的项目就已经具备了高水准的开源产品风范！

```
