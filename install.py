"""
DeepSeek Jarvis Proxy — One-time setup script.
Run via:  python install.py   or   setup.bat / setup.sh
"""
import subprocess
import sys
import os
import shutil

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def step(step_num: int, total: int, msg: str):
    print(f"📦 [{step_num}/{total}] {msg}")


def ok(msg: str):
    print(f"✅ {msg}")


def warn(msg: str):
    print(f"⚠️ {msg}")


def fail(msg: str):
    print(f"❌ {msg}")


def main():
    print("=" * 50)
    print("🛠️  DeepSeek Jarvis Proxy — 环境安装向导")
    print("=" * 50)
    print()

    TOTAL = 4

    # ---- 1. Python virtual environment ----
    if os.path.exists(os.path.join(PROJECT_ROOT, "env", "Scripts", "python.exe")):
        ok("虚拟环境已存在，跳过创建。")
    elif os.path.exists(os.path.join(PROJECT_ROOT, "env", "bin", "python")):
        ok("虚拟环境已存在，跳过创建。")
    else:
        step(1, TOTAL, "创建 Python 虚拟环境...")
        r = subprocess.run(
            [sys.executable, "-m", "venv", os.path.join(PROJECT_ROOT, "env")],
            capture_output=True, text=True
        )
        if r.returncode != 0:
            fail(f"创建虚拟环境失败！\n{r.stderr}")
            print("请确认已安装 Python 3.11+ 并已添加到 PATH。")
            return 1
        ok("虚拟环境创建完成。")

    # ---- 2. pip install ----
    step(2, TOTAL, "安装 Python 依赖...")
    pip = os.path.join(PROJECT_ROOT, "env", "Scripts", "pip.exe") if os.name == "nt" \
        else os.path.join(PROJECT_ROOT, "env", "bin", "pip")
    r = subprocess.run([pip, "install", "-r", os.path.join(PROJECT_ROOT, "requirements.txt")])
    if r.returncode != 0:
        warn("部分依赖安装可能失败，请检查网络连接。")
    else:
        ok("Python 依赖安装完成。")

    # ---- 3. npm install ----
    node_modules = os.path.join(PROJECT_ROOT, "rpc_server", "node_modules")
    if os.path.exists(node_modules):
        ok("Node.js 依赖已存在，跳过。")
    else:
        step(3, TOTAL, "安装 Node.js 依赖...")
        r = subprocess.run(
            ["npm", "install"],
            cwd=os.path.join(PROJECT_ROOT, "rpc_server"),
            shell=(os.name == "nt")
        )
        if r.returncode != 0:
            warn("npm install 失败！请确认已安装 Node.js。")
        else:
            ok("Node.js 依赖安装完成。")

    # ---- 4. auth config ----
    auth_file = os.path.join(PROJECT_ROOT, "auth_config.json")
    auth_example = os.path.join(PROJECT_ROOT, "auth_config.json.example")
    core_auth = os.path.join(PROJECT_ROOT, "core", "auth_config.json")
    core_example = os.path.join(PROJECT_ROOT, "core", "auth_config.json.example")

    if os.path.exists(auth_file):
        ok("auth_config.json 已存在，跳过。")
    else:
        step(4, TOTAL, "创建 auth_config.json 模板...")
        shutil.copy(auth_example, auth_file)
        warn("请编辑 auth_config.json 填入 DeepSeek 凭据，或首次启动时通过浏览器登录。")

    if not os.path.exists(core_auth) and os.path.exists(core_example):
        shutil.copy(core_example, core_auth)

    print()
    print("=" * 50)
    print("✅ 安装完成！运行 start.bat 启动项目。")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
