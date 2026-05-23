@echo off
REM ===== 切换到脚本所在目录的上级（项目根目录） =====
cd /d "%~dp0"

REM ===== 激活虚拟环境 =====
call env\Scripts\activate

REM ===== 安装依赖（可选，首次或更新时用） =====
pip install -r requirements.txt >nul 2>&1

REM ===== 启动 main.py =====
python main.py

pause