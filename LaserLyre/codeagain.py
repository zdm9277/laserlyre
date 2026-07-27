import board
import digitalio
import time
import usb_midi
import adafruit_midi

from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

SENSOR_PIN = board.GP15
DEBOUNCE_MS = 20

sensor = digitalio.DigitalInOut(SENSOR_PIN)
sensor.direction = digitalio.Direction.INPUT
sensor.pull = digitalio.Pull.DOWN

midi = adafruit_midi.MIDI(
    midi_out=usb_midi.ports[1],
    out_channel=0
)

last_raw = sensor.value
stable_value = last_raw
last_change = time.monotonic()
note_is_on = False

while True:
    raw = sensor.value
    now = time.monotonic()

    if raw != last_raw:
        last_raw = raw
        last_change = now

    if (now - last_change) * 1000 >= DEBOUNCE_MS:
        stable_value = last_raw

    # HIGH means the beam is broken.
    beam_broken = stable_value

    if beam_broken and not note_is_on:
        midi.send(NoteOn("C4", 100))
        note_is_on = True
        print("Beam broken: C4 ON")

    elif not beam_broken and note_is_on:
        midi.send(NoteOff("C4", 0))
        note_is_on = False
        print("Beam restored: C4 OFF")

    time.sleep(0.005)
