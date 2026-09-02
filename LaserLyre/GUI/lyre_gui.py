import tkinter as tk
from tkinter import ttk
import mido


class LaserLyreGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Laser Lyre")
        self.root.configure(bg="#111827")
        self.root.attributes("-fullscreen", True)

        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.protocol("WM_DELETE_WINDOW", self.close_program)

        # Base notes used by the eight laser strings.
        self.notes = ["C", "D", "E", "F", "G", "A", "B", "C"]

        # Original MIDI notes sent by the Pico.
        self.base_midi_notes = [
            60, 62, 64, 65, 67, 69, 71, 72
        ]

        # MIDI note numbers sent by the Pico mapped to beam numbers.
        self.midi_note_to_beam = {
            60: 0,
            62: 1,
            64: 2,
            65: 3,
            67: 4,
            69: 5,
            71: 6,
            72: 7,
        }

        # Note names for displaying transposed notes.
        self.note_names = [
            "C",
            "C#",
            "D",
            "D#",
            "E",
            "F",
            "F#",
            "G",
            "G#",
            "A",
            "A#",
            "B",
        ]

        # Key offsets from C in semitones.
        self.key_offsets = {
            "C": 0,
            "C#": 1,
            "D": 2,
            "D#": 3,
            "E": 4,
            "F": 5,
            "F#": 6,
            "G": 7,
            "G#": 8,
            "A": 9,
            "A#": 10,
            "B": 11,
        }

        # General MIDI program numbers.
        self.instrument_programs = {
            "Grand Piano": 0,
            "Electric Piano": 4,
            "Music Box": 10,
            "Organ": 19,
            "Acoustic Guitar": 24,
            "Electric Guitar": 27,
            "Violin": 40,
            "Synth Lead": 80,
        }

        # Beam state.
        self.beam_states = [False] * 8
        self.beam_buttons = []

        # Note timers.
        self.note_off_timers = [None] * 8

        # Keep track of the actual transposed MIDI note being played
        # by each beam.
        self.active_output_notes = [None] * 8

        # Calibration state.
        self.calibration_active = False
        self.calibration_beam = 0
        self.calibration_passed = [False] * 8

        # MIDI connections.
        self.midi_input = None
        self.midi_output = None

        # GUI variables.
        self.instrument_var = tk.StringVar(
            value="Grand Piano"
        )

        self.volume_var = tk.IntVar(
            value=80
        )

        self.key_var = tk.StringVar(
            value="C"
        )

        self.octave_var = tk.IntVar(
            value=0
        )

        self.octave_text = tk.StringVar(
            value="0"
        )

        self.note_duration_var = tk.DoubleVar(
            value=2.0
        )

        self.note_duration_text = tk.StringVar(
            value="2.00 s"
        )

        self.status_var = tk.StringVar(
            value="Starting MIDI connections..."
        )

        # Build GUI.
        self.create_header()
        self.create_beam_section()
        self.create_controls()
        self.create_status_bar()

        # Connect MIDI devices.
        self.connect_to_pico()
        self.connect_to_fluidsynth()

        # Continuously check Pico MIDI input.
        self.root.after(10, self.check_midi)

    # ============================================================
    # GUI
    # ============================================================

    def create_header(self):
        header = tk.Frame(
            self.root,
            bg="#0f172a",
            height=80
        )

        header.pack(
            fill="x"
        )

        title = tk.Label(
            header,
            text="LASER LYRE",
            font=("Arial", 28, "bold"),
            fg="white",
            bg="#0f172a"
        )

        title.pack(
            side="left",
            padx=25,
            pady=18
        )

        exit_button = tk.Button(
            header,
            text="Exit",
            font=("Arial", 14, "bold"),
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            command=self.close_program,
            width=8
        )

        exit_button.pack(
            side="right",
            padx=25,
            pady=18
        )

    def create_beam_section(self):
        beam_frame = tk.Frame(
            self.root,
            bg="#111827"
        )

        beam_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        beam_title = tk.Label(
            beam_frame,
            text="Laser Strings",
            font=("Arial", 20, "bold"),
            fg="white",
            bg="#111827"
        )

        beam_title.pack(
            pady=(0, 15)
        )

        button_frame = tk.Frame(
            beam_frame,
            bg="#111827"
        )

        button_frame.pack(
            expand=True
        )

        for index in range(8):
            button = tk.Button(
                button_frame,
                text=(
                    f"Beam {index + 1}\n"
                    f"{self.get_beam_note_name(index)}"
                ),
                width=8,
                height=5,
                font=("Arial", 14, "bold"),
                bg="#1f2937",
                fg="white",
                activebackground="#2563eb",
                activeforeground="white",
                command=lambda i=index:
                    self.manual_beam_test(i)
            )

            button.grid(
                row=0,
                column=index,
                padx=5,
                pady=5,
                sticky="nsew"
            )

            self.beam_buttons.append(button)

            button_frame.grid_columnconfigure(
                index,
                weight=1
            )

    def create_controls(self):
        controls = tk.Frame(
            self.root,
            bg="#1f2937"
        )

        controls.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )

        # --------------------------------------------------------
        # Instrument
        # --------------------------------------------------------

        instrument_label = tk.Label(
            controls,
            text="Instrument:",
            font=("Arial", 15, "bold"),
            fg="white",
            bg="#1f2937"
        )

        instrument_label.grid(
            row=0,
            column=0,
            padx=(15, 5),
            pady=18
        )

        instrument_menu = ttk.Combobox(
            controls,
            textvariable=self.instrument_var,
            values=list(
                self.instrument_programs.keys()
            ),
            state="readonly",
            font=("Arial", 14),
            width=17
        )

        instrument_menu.grid(
            row=0,
            column=1,
            padx=5,
            pady=18
        )

        instrument_menu.bind(
            "<<ComboboxSelected>>",
            self.instrument_changed
        )

        # --------------------------------------------------------
        # Volume
        # --------------------------------------------------------

        volume_label = tk.Label(
            controls,
            text="Volume:",
            font=("Arial", 15, "bold"),
            fg="white",
            bg="#1f2937"
        )

        volume_label.grid(
            row=0,
            column=2,
            padx=(20, 5),
            pady=18
        )

        volume_slider = tk.Scale(
            controls,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.volume_var,
            command=self.volume_changed,
            length=200,
            font=("Arial", 12),
            bg="#1f2937",
            fg="white",
            troughcolor="#374151",
            highlightthickness=0
        )

        volume_slider.grid(
            row=0,
            column=3,
            padx=5,
            pady=8
        )

        # --------------------------------------------------------
        # Key
        # --------------------------------------------------------

        key_label = tk.Label(
            controls,
            text="Key:",
            font=("Arial", 15, "bold"),
            fg="white",
            bg="#1f2937"
        )

        key_label.grid(
            row=0,
            column=4,
            padx=(20, 5),
            pady=18
        )

        key_menu = ttk.Combobox(
            controls,
            textvariable=self.key_var,
            values=list(
                self.key_offsets.keys()
            ),
            state="readonly",
            font=("Arial", 14),
            width=4
        )

        key_menu.grid(
            row=0,
            column=5,
            padx=5,
            pady=18
        )

        key_menu.bind(
            "<<ComboboxSelected>>",
            self.key_changed
        )

        # --------------------------------------------------------
        # Octave
        # --------------------------------------------------------

        octave_label = tk.Label(
            controls,
            text="Octave:",
            font=("Arial", 15, "bold"),
            fg="white",
            bg="#1f2937"
        )

        octave_label.grid(
            row=0,
            column=6,
            padx=(20, 5),
            pady=18
        )

        octave_down_button = tk.Button(
            controls,
            text="-",
            font=("Arial", 14, "bold"),
            command=self.octave_down,
            width=3
        )

        octave_down_button.grid(
            row=0,
            column=7,
            padx=4,
            pady=18
        )

        octave_value = tk.Label(
            controls,
            textvariable=self.octave_text,
            font=("Arial", 15, "bold"),
            fg="white",
            bg="#1f2937",
            width=3
        )

        octave_value.grid(
            row=0,
            column=8,
            padx=2,
            pady=18
        )

        octave_up_button = tk.Button(
            controls,
            text="+",
            font=("Arial", 14, "bold"),
            command=self.octave_up,
            width=3
        )

        octave_up_button.grid(
            row=0,
            column=9,
            padx=4,
            pady=18
        )

        # --------------------------------------------------------
        # Calibrate
        # --------------------------------------------------------

        calibration_button = tk.Button(
            controls,
            text="Calibrate",
            font=("Arial", 14, "bold"),
            bg="#f59e0b",
            fg="black",
            activebackground="#d97706",
            activeforeground="black",
            command=self.calibrate,
            width=11
        )

        calibration_button.grid(
            row=0,
            column=10,
            padx=20,
            pady=18
        )

        # --------------------------------------------------------
        # Note duration
        # --------------------------------------------------------

        duration_label = tk.Label(
            controls,
            text="Note Duration:",
            font=("Arial", 15, "bold"),
            fg="white",
            bg="#1f2937"
        )

        duration_label.grid(
            row=1,
            column=0,
            padx=15,
            pady=(0, 12)
        )

        duration_slider = tk.Scale(
            controls,
            from_=0.25,
            to=5.0,
            resolution=0.25,
            orient="horizontal",
            variable=self.note_duration_var,
            command=self.note_duration_changed,
            length=500,
            font=("Arial", 12),
            bg="#1f2937",
            fg="white",
            troughcolor="#374151",
            highlightthickness=0,
            showvalue=False
        )

        duration_slider.grid(
            row=1,
            column=1,
            columnspan=7,
            padx=10,
            pady=(0, 12),
            sticky="ew"
        )

        duration_value_label = tk.Label(
            controls,
            textvariable=self.note_duration_text,
            font=("Arial", 15, "bold"),
            fg="#86efac",
            bg="#1f2937",
            width=7
        )

        duration_value_label.grid(
            row=1,
            column=8,
            columnspan=2,
            padx=10,
            pady=(0, 12)
        )

        controls.grid_columnconfigure(
            3,
            weight=1
        )

    def create_status_bar(self):
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            font=("Arial", 13),
            fg="#86efac",
            bg="#0f172a",
            padx=20,
            pady=10
        )

        status_bar.pack(
            fill="x",
            side="bottom"
        )

    # ============================================================
    # MIDI CONNECTIONS
    # ============================================================

    def connect_to_pico(self):
        try:
            # Do not open another connection if one already exists.
            if self.midi_input is not None:
                return

            pico_port_name = None

            for port_name in mido.get_input_names():
                if (
                    "Pico W" in port_name
                    or "CircuitPython" in port_name
                ):
                    pico_port_name = port_name
                    break

            if pico_port_name is None:
                self.status_var.set(
                    "Pico MIDI not found. Retrying..."
                )

                self.root.after(
                    2000,
                    self.connect_to_pico
                )

                return

            self.midi_input = mido.open_input(
                pico_port_name
            )

            self.status_var.set(
                f"Pico connected: {pico_port_name}"
            )

        except Exception as error:
            self.midi_input = None

            self.status_var.set(
                f"Pico connection error: {error}"
            )

            self.root.after(
                2000,
                self.connect_to_pico
            )

    def connect_to_fluidsynth(self):
        try:
            # Do not open another connection if one already exists.
            if self.midi_output is not None:
                return

            fluid_port_name = None

            for port_name in mido.get_output_names():
                if "FLUID Synth" in port_name:
                    fluid_port_name = port_name
                    break

            if fluid_port_name is None:
                self.status_var.set(
                    "FluidSynth MIDI output not found. "
                    "Retrying..."
                )

                self.root.after(
                    2000,
                    self.connect_to_fluidsynth
                )

                return

            self.midi_output = mido.open_output(
                fluid_port_name
            )

            # Apply default instrument.
            self.send_program_change()

            # Apply default volume.
            self.volume_changed(
                self.volume_var.get()
            )

            self.status_var.set(
                f"Ready — "
                f"{self.instrument_var.get()} — "
                f"Key {self.key_var.get()} — "
                f"Octave {self.octave_text.get()}"
            )

        except Exception as error:
            self.midi_output = None

            self.status_var.set(
                f"FluidSynth connection error: {error}"
            )

            self.root.after(
                2000,
                self.connect_to_fluidsynth
            )

    def check_midi(self):
        try:
            if self.midi_input is not None:
                for message in self.midi_input.iter_pending():
                    self.handle_midi_message(message)

        except Exception as error:
            self.status_var.set(
                f"Pico disconnected: {error}"
            )

            try:
                if self.midi_input is not None:
                    self.midi_input.close()
            except Exception:
                pass

            self.midi_input = None

            self.root.after(
                2000,
                self.connect_to_pico
            )

        self.root.after(
            10,
            self.check_midi
        )

    # ============================================================
    # MIDI NOTE HANDLING
    # ============================================================

    def handle_midi_message(self, message):
        if not hasattr(message, "note"):
            return

        if message.note not in self.midi_note_to_beam:
            return

        beam_index = self.midi_note_to_beam[
            message.note
        ]

        # --------------------------------------------------------
        # Calibration mode
        # --------------------------------------------------------

        if self.calibration_active:
            if (
                message.type == "note_on"
                and message.velocity > 0
            ):
                self.handle_calibration_note(
                    beam_index
                )

            return

        # --------------------------------------------------------
        # Beam broken / Note ON
        # --------------------------------------------------------

        if (
            message.type == "note_on"
            and message.velocity > 0
        ):
            # Cancel an old timer if this beam is triggered again.
            self.cancel_note_off_timer(
                beam_index
            )

            # Stop any older note still assigned to this beam.
            self.stop_output_note(
                beam_index
            )

            # Apply key and octave transposition.
            output_note = self.transpose_note(
                message.note
            )

            # Send the transformed note to FluidSynth.
            if self.midi_output is not None:
                try:
                    self.midi_output.send(
                        mido.Message(
                            "note_on",
                            channel=0,
                            note=output_note,
                            velocity=message.velocity
                        )
                    )

                    self.active_output_notes[
                        beam_index
                    ] = output_note

                except Exception as error:
                    self.status_var.set(
                        f"MIDI output error: {error}"
                    )

                    return

            # Update GUI.
            self.set_beam_active(
                beam_index
            )

            # Start maximum note-duration timer.
            self.schedule_note_off(
                beam_index,
                output_note
            )

        # --------------------------------------------------------
        # Beam restored / Note OFF
        # --------------------------------------------------------

        elif (
            message.type == "note_off"
            or (
                message.type == "note_on"
                and message.velocity == 0
            )
        ):
            self.cancel_note_off_timer(
                beam_index
            )

            self.stop_output_note(
                beam_index
            )

            self.set_beam_inactive(
                beam_index
            )

    # ============================================================
    # NOTE TRANSFORMATION
    # ============================================================

    def get_transpose_amount(self):
        key_shift = self.key_offsets[
            self.key_var.get()
        ]

        octave_shift = (
            self.octave_var.get() * 12
        )

        return (
            key_shift
            + octave_shift
        )

    def transpose_note(self, midi_note):
        new_note = (
            midi_note
            + self.get_transpose_amount()
        )

        # Valid MIDI note range is 0 through 127.
        return max(
            0,
            min(127, new_note)
        )

    def get_note_name(self, midi_note):
        note_name = self.note_names[
            midi_note % 12
        ]

        octave_number = (
            midi_note // 12
        ) - 1

        return (
            f"{note_name}"
            f"{octave_number}"
        )

    def get_beam_note_name(self, index):
        midi_note = self.transpose_note(
            self.base_midi_notes[index]
        )

        return self.get_note_name(
            midi_note
        )

    def refresh_beam_labels(self):
        if self.calibration_active:
            return

        for index in range(8):
            if not self.beam_states[index]:
                self.beam_buttons[index].configure(
                    text=(
                        f"Beam {index + 1}\n"
                        f"{self.get_beam_note_name(index)}"
                    )
                )

    # ============================================================
    # KEY CONTROL
    # ============================================================

    def key_changed(self, event=None):
        # Stop notes before changing the musical configuration.
        self.stop_all_active_notes()

        self.refresh_beam_labels()

        self.status_var.set(
            f"Key changed to "
            f"{self.key_var.get()}"
        )

    # ============================================================
    # OCTAVE CONTROL
    # ============================================================

    def octave_down(self):
        new_octave = (
            self.octave_var.get() - 1
        )

        # Limit octave shifting.
        if new_octave < -3:
            self.status_var.set(
                "Minimum octave reached"
            )
            return

        self.stop_all_active_notes()

        self.octave_var.set(
            new_octave
        )

        self.update_octave_text()

        self.refresh_beam_labels()

        self.status_var.set(
            f"Octave changed to "
            f"{self.octave_text.get()}"
        )

    def octave_up(self):
        new_octave = (
            self.octave_var.get() + 1
        )

        # Limit octave shifting.
        if new_octave > 3:
            self.status_var.set(
                "Maximum octave reached"
            )
            return

        self.stop_all_active_notes()

        self.octave_var.set(
            new_octave
        )

        self.update_octave_text()

        self.refresh_beam_labels()

        self.status_var.set(
            f"Octave changed to "
            f"{self.octave_text.get()}"
        )

    def update_octave_text(self):
        octave = self.octave_var.get()

        if octave > 0:
            self.octave_text.set(
                f"+{octave}"
            )
        else:
            self.octave_text.set(
                str(octave)
            )

    # ============================================================
    # NOTE TIMERS
    # ============================================================

    def schedule_note_off(
        self,
        beam_index,
        midi_note
    ):
        self.cancel_note_off_timer(
            beam_index
        )

        duration_ms = max(
            1,
            int(
                self.note_duration_var.get()
                * 1000
            )
        )

        self.note_off_timers[
            beam_index
        ] = self.root.after(
            duration_ms,
            lambda i=beam_index, n=midi_note:
                self.stop_note_after_duration(
                    i,
                    n
                )
        )

    def cancel_note_off_timer(
        self,
        beam_index
    ):
        timer_id = self.note_off_timers[
            beam_index
        ]

        if timer_id is not None:
            try:
                self.root.after_cancel(
                    timer_id
                )
            except Exception:
                pass

            self.note_off_timers[
                beam_index
            ] = None

    def stop_note_after_duration(
        self,
        beam_index,
        midi_note
    ):
        self.note_off_timers[
            beam_index
        ] = None

        self.stop_output_note(
            beam_index
        )

        self.set_beam_inactive(
            beam_index
        )

        self.status_var.set(
            f"Beam {beam_index + 1} stopped after "
            f"{self.note_duration_var.get():.2f} seconds"
        )

    def stop_output_note(
        self,
        beam_index
    ):
        note = self.active_output_notes[
            beam_index
        ]

        if note is None:
            return

        if self.midi_output is not None:
            try:
                self.midi_output.send(
                    mido.Message(
                        "note_off",
                        channel=0,
                        note=note,
                        velocity=0
                    )
                )

            except Exception as error:
                self.status_var.set(
                    f"Note-off error: {error}"
                )

        self.active_output_notes[
            beam_index
        ] = None

    def stop_all_active_notes(self):
        for index in range(8):
            self.cancel_note_off_timer(
                index
            )

            self.stop_output_note(
                index
            )

            self.beam_states[
                index
            ] = False

        self.refresh_beam_labels()

    # ============================================================
    # BEAM DISPLAY
    # ============================================================

    def set_beam_active(self, index):
        self.beam_states[index] = True

        self.beam_buttons[index].configure(
            bg="#22c55e",
            activebackground="#16a34a",
            text=(
                f"Beam {index + 1}\n"
                f"ACTIVE"
            )
        )

        self.status_var.set(
            f"Beam {index + 1} broken — "
            f"{self.get_beam_note_name(index)} playing"
        )

    def set_beam_inactive(self, index):
        self.beam_states[index] = False

        self.beam_buttons[index].configure(
            bg="#1f2937",
            activebackground="#2563eb",
            text=(
                f"Beam {index + 1}\n"
                f"{self.get_beam_note_name(index)}"
            )
        )

        self.status_var.set(
            f"Beam {index + 1} restored"
        )

    # ============================================================
    # MANUAL BEAM TEST
    # ============================================================

    def manual_beam_test(self, index):
        if self.calibration_active:
            return

        if self.beam_states[index]:
            self.cancel_note_off_timer(
                index
            )

            self.stop_output_note(
                index
            )

            self.set_beam_inactive(
                index
            )

        else:
            output_note = self.transpose_note(
                self.base_midi_notes[index]
            )

            if self.midi_output is not None:
                try:
                    self.midi_output.send(
                        mido.Message(
                            "note_on",
                            channel=0,
                            note=output_note,
                            velocity=127
                        )
                    )

                    self.active_output_notes[
                        index
                    ] = output_note

                except Exception as error:
                    self.status_var.set(
                        f"Manual MIDI test failed: {error}"
                    )

                    return

            self.set_beam_active(
                index
            )

            self.schedule_note_off(
                index,
                output_note
            )

    # ============================================================
    # INSTRUMENT CONTROL
    # ============================================================

    def send_program_change(self):
        if self.midi_output is None:
            return

        instrument = self.instrument_var.get()

        program_number = self.instrument_programs[
            instrument
        ]

        message = mido.Message(
            "program_change",
            channel=0,
            program=program_number
        )

        self.midi_output.send(
            message
        )

    def instrument_changed(self, event=None):
        try:
            if self.midi_output is None:
                self.status_var.set(
                    "FluidSynth is not connected"
                )

                return

            # Stop currently playing notes before changing instrument.
            self.stop_all_active_notes()

            self.send_program_change()

            self.status_var.set(
                f"Instrument changed to "
                f"{self.instrument_var.get()}"
            )

        except Exception as error:
            self.status_var.set(
                f"Instrument change failed: {error}"
            )

    # ============================================================
    # VOLUME CONTROL
    # ============================================================

    def volume_changed(self, value):
        volume_percent = int(
            float(value)
        )

        if self.midi_output is None:
            return

        # MIDI volume range is 0 through 127.
        midi_volume = int(
            (volume_percent / 100)
            * 127
        )

        try:
            message = mido.Message(
                "control_change",
                channel=0,
                control=7,
                value=midi_volume
            )

            self.midi_output.send(
                message
            )

            self.status_var.set(
                f"Volume: "
                f"{volume_percent}%"
            )

        except Exception as error:
            self.status_var.set(
                f"Volume change failed: {error}"
            )

    # ============================================================
    # NOTE DURATION
    # ============================================================

    def note_duration_changed(self, value):
        duration = float(value)

        self.note_duration_text.set(
            f"{duration:.2f} s"
        )

        self.status_var.set(
            f"Note duration: "
            f"{duration:.2f} seconds"
        )

    # ============================================================
    # CALIBRATION
    # ============================================================

    def calibrate(self):
        # Stop any notes that are currently playing.
        self.stop_all_active_notes()

        self.calibration_active = True
        self.calibration_beam = 0

        self.calibration_passed = [
            False
        ] * 8

        for index in range(8):
            self.cancel_note_off_timer(
                index
            )

            self.beam_states[
                index
            ] = False

            self.beam_buttons[index].configure(
                bg="#1f2937",
                activebackground="#2563eb",
                text=(
                    f"Beam {index + 1}\n"
                    f"{self.get_beam_note_name(index)}"
                )
            )

        self.highlight_calibration_beam()

        self.status_var.set(
            "Calibration started — break Beam 1"
        )

    def highlight_calibration_beam(self):
        for index in range(8):
            if self.calibration_passed[index]:
                self.beam_buttons[index].configure(
                    bg="#22c55e",
                    activebackground="#16a34a",
                    text=(
                        f"Beam {index + 1}\n"
                        f"PASSED"
                    )
                )

            elif index == self.calibration_beam:
                self.beam_buttons[index].configure(
                    bg="#f59e0b",
                    activebackground="#d97706",
                    text=(
                        f"Beam {index + 1}\n"
                        f"TEST"
                    )
                )

            else:
                self.beam_buttons[index].configure(
                    bg="#1f2937",
                    activebackground="#2563eb",
                    text=(
                        f"Beam {index + 1}\n"
                        f"{self.get_beam_note_name(index)}"
                    )
                )

    def handle_calibration_note(
        self,
        beam_index
    ):
        if beam_index != self.calibration_beam:
            self.status_var.set(
                f"Wrong beam — break Beam "
                f"{self.calibration_beam + 1}"
            )

            return

        self.calibration_passed[
            beam_index
        ] = True

        self.beam_buttons[
            beam_index
        ].configure(
            bg="#22c55e",
            activebackground="#16a34a",
            text=(
                f"Beam {beam_index + 1}\n"
                f"PASSED"
            )
        )

        # Final beam.
        if self.calibration_beam == 7:
            self.status_var.set(
                "Calibration complete — "
                "all 8 beams passed"
            )

            # Keep final result visible for two seconds.
            self.root.after(
                2000,
                self.reset_after_calibration
            )

            return

        self.calibration_beam += 1

        self.highlight_calibration_beam()

        self.status_var.set(
            f"Beam {beam_index + 1} passed — "
            f"break Beam "
            f"{self.calibration_beam + 1}"
        )

    def reset_after_calibration(self):
        self.calibration_active = False
        self.calibration_beam = 0

        self.calibration_passed = [
            False
        ] * 8

        self.beam_states = [
            False
        ] * 8

        for index in range(8):
            self.beam_buttons[index].configure(
                bg="#1f2937",
                activebackground="#2563eb",
                text=(
                    f"Beam {index + 1}\n"
                    f"{self.get_beam_note_name(index)}"
                )
            )

        self.status_var.set(
            f"Ready — "
            f"{self.instrument_var.get()} — "
            f"Key {self.key_var.get()} — "
            f"Octave {self.octave_text.get()}"
        )

    # ============================================================
    # WINDOW / EXIT
    # ============================================================

    def exit_fullscreen(self, event=None):
        self.root.attributes(
            "-fullscreen",
            False
        )

    def close_program(self):
        # Stop all notes first.
        for index in range(8):
            self.cancel_note_off_timer(
                index
            )

            self.stop_output_note(
                index
            )

        # MIDI panic in case anything remains sounding.
        if self.midi_output is not None:
            try:
                self.midi_output.send(
                    mido.Message(
                        "control_change",
                        channel=0,
                        control=123,
                        value=0
                    )
                )
            except Exception:
                pass

        try:
            if self.midi_input is not None:
                self.midi_input.close()
        except Exception:
            pass

        try:
            if self.midi_output is not None:
                self.midi_output.close()
        except Exception:
            pass

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = LaserLyreGUI(root)
    root.mainloop()