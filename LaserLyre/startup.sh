#!/bin/bash

LOG_DIR="/home/skynet/LaserLyre/logs"
GUI_FILE="/home/skynet/LaserLyre/GUI/lyre_gui.py"
SOUNDFONT="/usr/share/sounds/sf2/FluidR3_GM.sf2"

mkdir -p "$LOG_DIR"

echo "========================================" > "$LOG_DIR/startup.log"
echo "Laser Lyre startup began: $(date)" >> "$LOG_DIR/startup.log"

# Allow the desktop and audio system time to initialize.
sleep 5

# Stop any older FluidSynth process.
pkill fluidsynth 2>/dev/null
sleep 1

# Confirm the SoundFont exists.
if [ ! -f "$SOUNDFONT" ]; then
    echo "ERROR: SoundFont not found at $SOUNDFONT" \
        >> "$LOG_DIR/startup.log"
    exit 1
fi

# Confirm the GUI file exists.
if [ ! -f "$GUI_FILE" ]; then
    echo "ERROR: GUI not found at $GUI_FILE" \
        >> "$LOG_DIR/startup.log"
    exit 1
fi

# Start FluidSynth in server mode.
fluidsynth \
    -a alsa \
    -m alsa_seq \
    -i \
    -s \
    -g 1.0 \
    "$SOUNDFONT" \
    >> "$LOG_DIR/fluidsynth.log" 2>&1 &

FLUID_PID=$!

echo "FluidSynth started with PID $FLUID_PID" \
    >> "$LOG_DIR/startup.log"

# Launch the GUI.
echo "Launching GUI" >> "$LOG_DIR/startup.log"

python3 "$GUI_FILE" \
    >> "$LOG_DIR/gui.log" 2>&1

echo "GUI closed: $(date)" >> "$LOG_DIR/startup.log"