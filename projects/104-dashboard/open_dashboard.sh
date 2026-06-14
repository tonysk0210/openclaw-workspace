#!/bin/bash
# 早安！開啟求職晨報
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
open "$SCRIPT_DIR/morning_briefing.html"
echo "☕ 求職晨報已開啟！"
