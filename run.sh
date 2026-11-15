#!/usr/bin/env bash
set -euo pipefail

# xcb is a Linux Qt backend.  macOS uses Qt's native Cocoa backend by default.
if [[ "$(uname -s)" == "Linux" ]]; then
  export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
fi

exec uv run python main.py
