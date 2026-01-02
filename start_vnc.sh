#!/bin/bash

# Port 6080 for noVNC
PORT=6080

echo "Starting noVNC on port $PORT..."
echo "Access http://localhost:$PORT/vnc.html to view the GUI."

# Start noVNC proxy pointing to local VNC server (5900)
/workspaces/Airport/noVNC/utils/novnc_proxy --vnc localhost:5900 --listen $PORT
