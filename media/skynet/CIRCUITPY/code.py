import board
import digitalio
import time
import usb_midi
import adafruit_midi

from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

SENSOR_PINS = [
    board.GP15,
    board.GP14,
    board.GP13,
    board.GP12,
    board.GP16,
    board.GP17,
    board.GP18,
    board.GP19,
]

MIDI_NOTES = [
    "C4",
    "D4",
    "E4",
    "F4",
    "G4",
    "A4",
    "B4",
    "C5",
]

DEBOUNCE_MS = 20
VELOCITY = 127

midi = adafruit_midi.MIDI(
    midi_out=usb_midi.ports[1],
    out_channel=0
)

sensors = []
last_raw_values = []
stable_values = []
last_change_times = []
notes_are_on = []

for pin in SENSOR_PINS:
    sensor = digitalio.DigitalInOut(pin)
    sensor.direction = digitalio.Direction.INPUT
    sensor.pull = digitalio.Pull.UP

    initial_value = sensor.value

    sensors.append(sensor)
    last_raw_values.append(initial_value)
    stable_values.append(initial_value)
    last_change_times.append(time.monotonic())
    notes_are_on.append(False)

print("Eight-sensor laser lyre started")

while True:
    now = time.monotonic()

    for index, sensor in enumerate(sensors):
        raw = sensor.value

        if raw != last_raw_values[index]:
            last_raw_values[index] = raw
            last_change_times[index] = now

        if (now - last_change_times[index]) * 1000 >= DEBOUNCE_MS:
            stable_values[index] = last_raw_values[index]

        # False = laser hitting sensor
        # True = beam broken
        beam_broken = stable_values[index]

        if beam_broken and not notes_are_on[index]:
            midi.send(NoteOn(MIDI_NOTES[index], VELOCITY))
            notes_are_on[index] = True

            print(
                "Beam",
                index + 1,
                "broken:",
                MIDI_NOTES[index],
                "ON"
            )

        elif not beam_broken and notes_are_on[index]:
            midi.send(NoteOff(MIDI_NOTES[index], 0))
            notes_are_on[index] = False

            print(
                "Beam",
                index + 1,
                "restored:",
                MIDI_NOTES[index],
                "OFF"
            )

    time.sleep(0.005)
