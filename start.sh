#!/bin/bash
set -e

echo "Starting Xvfb..."
Xvfb :99 -screen 0 1280x720x24 &
XVFB_PID=$!

# Wait for Xvfb to initialize
sleep 2

# Verify Xvfb is running
if ! kill -0 $XVFB_PID 2>/dev/null; then
  echo "Xvfb failed to start!"
  exit 1
fi

export DISPLAY=:99

echo "Starting Vybe Analytics Bot..."
# Trap to ensure Xvfb is killed on script exit (e.g., error or Ctrl+C)
trap 'kill $XVFB_PID 2>/dev/null; exit 1' INT TERM EXIT

# Run the bot with unbuffered output
exec python -u bot.py