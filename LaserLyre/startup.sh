#!/bin/bash

LOG_DIR="/home/skynet/LaserLyre/logs"
GUI_FILE="/home/skynet/LaserLyre/GUI/lyre_gui.py"
SOUNDFONT="/usr/share/sounds/sf2/FluidR3_GM.sf2"

mkdir -p "$LOG_DIR"

echo "========================================" > "$LOG_DIR/startup.log"
echo "Laser Lyre startup began: $(date)" >> "$LOG_DIR/startup.log"

# Allow the desktop, audio system, and Pico time to initialize.
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

# Wait until both the Pico and FluidSynth MIDI ports appear.
CONNECTED=false

for attempt in $(seq 1 30); do
    echo "Connection attempt $attempt" \
        >> "$LOG_DIR/startup.log"

    if aconnect -i | grep -q "Pico W" &&
       aconnect -o | grep -q "FLUID Synth"; then

        aconnect "Pico W":0 "FLUID Synth":0 \
            >> "$LOG_DIR/startup.log" 2>&1

        if [ $? -eq 0 ]; then
            echo "Pico connected to FluidSynth" \
                >> "$LOG_DIR/startup.log"

            CONNECTED=true
            break
        fi
    fi

    sleep 1
done

if [ "$CONNECTED" = false ]; then
    echo "ERROR: Could not connect Pico to FluidSynth" \
        >> "$LOG_DIR/startup.log"
else
    echo "Laser Lyre audio is ready" \
        >> "$LOG_DIR/startup.log"
fi

# Launch the GUI.
echo "Launching GUI" >> "$LOG_DIR/startup.log"

python3 "$GUI_FILE" \
    >> "$LOG_DIR/gui.log" 2>&1

echo "GUI closed: $(date)" >> "$LOG_DIR/startup.log"
