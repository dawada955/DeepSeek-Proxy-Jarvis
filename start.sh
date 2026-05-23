#!/bin/bash

# ===== 切换到脚本所在目录的上级（项目根目录） =====
cd "$(dirname "$0")"

# ===== 激活虚拟环境 =====
source env/bin/activate

# ===== 安装依赖（可选） =====
pip install -r requirements.txt

# ===== 启动 main.py =====
python main.py