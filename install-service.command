#!/bin/zsh
set -e

PROJECT_DIR="${0:A:h}"
LABEL="com.linyan.voicecopyweb"
SOURCE_PLIST="$PROJECT_DIR/$LABEL.plist"
TARGET_PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
SERVICE_DIR="$HOME/Library/Application Support/VoiceCopyWeb"
DOMAIN="gui/$(id -u)"

mkdir -p "$PROJECT_DIR/logs" "$HOME/Library/LaunchAgents" "$HOME/Library/Application Support"
chmod 700 "$PROJECT_DIR/logs"
if [[ -L "$SERVICE_DIR" ]]; then
  unlink "$SERVICE_DIR"
fi
mkdir -p "$SERVICE_DIR/data" "$SERVICE_DIR/logs"
chmod 700 "$SERVICE_DIR" "$SERVICE_DIR/data" "$SERVICE_DIR/logs"
ditto "$PROJECT_DIR/.venv" "$SERVICE_DIR/.venv"
ditto "$PROJECT_DIR/app" "$SERVICE_DIR/app"
ditto "$PROJECT_DIR/web" "$SERVICE_DIR/web"
cp "$PROJECT_DIR/start.sh" "$PROJECT_DIR/requirements.txt" "$SERVICE_DIR/"
if [[ -f "$PROJECT_DIR/.access_token" && ! -f "$SERVICE_DIR/.access_token" ]]; then
  cp "$PROJECT_DIR/.access_token" "$SERVICE_DIR/.access_token"
  chmod 600 "$SERVICE_DIR/.access_token"
fi
plutil -lint "$SOURCE_PLIST"
cp "$SOURCE_PLIST" "$TARGET_PLIST"
chmod 600 "$TARGET_PLIST"

launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$TARGET_PLIST"
launchctl kickstart -k "$DOMAIN/$LABEL"

echo
echo "口播提取器已设为后台常驻服务。"
echo "访问地址：http://127.0.0.1:8765"
echo "日志位置：$SERVICE_DIR/logs"
echo
read -k 1 "?Press any key to close..."
