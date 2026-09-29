#!/bin/zsh
set -e

PROJECT_DIR="${0:A:h}"
VENV_DIR="$PROJECT_DIR/.venv"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "首次运行：正在创建本地环境……"
  /Library/Frameworks/Python.framework/Versions/3.10/bin/python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install -U pip
  "$VENV_DIR/bin/python" -m pip install -r "$PROJECT_DIR/requirements.txt"
fi

cd "$PROJECT_DIR"
exec "$VENV_DIR/bin/python" -m app.main

