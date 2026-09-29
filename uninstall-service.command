#!/bin/zsh
set -e

LABEL="com.linyan.voicecopyweb"
TARGET_PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
if [[ -f "$TARGET_PLIST" ]]; then
  mv "$TARGET_PLIST" "$HOME/.Trash/$LABEL.plist"
fi
echo
echo "口播提取器后台服务已停止，开机自启已取消。"
echo
read -k 1 "?Press any key to close..."
