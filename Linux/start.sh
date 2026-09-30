#!/usr/bin/env bash

pkill -f chromium
pkill -f brave

sleep 1

if command -v brave &> /dev/null; then
    brave --remote-debugging-port=9222 &
elif command -v brave-browser &> /dev/null; then
    brave-browser --remote-debugging-port=9222 &
elif command -v chromium &> /dev/null; then
    chromium --remote-debugging-port=9222 &
else
    echo "No chromium or brave binary found in PATH."
    exit 1
fi

disown
