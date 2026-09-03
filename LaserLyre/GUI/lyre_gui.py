import tkinter as tk
from tkinter import ttk
import mido


class LaserLyreGUI:
    def __init__(self, root):
        self.root = root

        # ------------------------------------------------------------
        # Main window
        # ------------------------------------------------------------
        self.root.title("Laser Lyre")
        self.root.configure(bg="#111827")
        self.root.attributes("-fullscreen", True)

        # Keyboard/window controls.
        self.root.bind("<Escape>", self.exit_fullscreen_mode)
        self.root.bind("<F11>", self.toggle_fullscreen_mode)
        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close_application
        )

        # ------------------------------------------------------------
        # Musical configuration
        # ------------------------------------------------------------

        # MIDI notes originally sent by the Pico for the eight beams.
        self.base_midi_notes = [
            60, 62, 64, 65, 67, 69, 71, 72
        ]

        # Map each Pico MIDI note to its beam index.
        self.midi_note_to_beam_index = {
            60: 0,
            62: 1,
            64: 2,
            65: 3,
            67: 4,
            69: 5,
            71: 6,
            72: 7,
        }

        # Chromatic note names used for display.
        self.chromatic_note_names = [
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

        # Number of semitones each key is above C.
        self.key_semitone_offsets = {
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

        # General MIDI instrument program numbers.
        self.instrument_program_numbers = {
            "Grand Piano": 0,
            "Electric Piano": 4,
            "Music Box": 10,
            "Organ": 19,
            "Acoustic Guitar": 24,
            "Electric Guitar": 27,
            "Violin": 40,
            "Synth Lead": 80,
        }

        # ------------------------------------------------------------
        # Beam state
        # ------------------------------------------------------------
        self.beam_is_active = [False] * 8
        self.beam_buttons = []

        # One automatic note-off timer per beam.
        self.beam_note_off_timers = [None] * 8

        # Actual transposed note currently sounding for each beam.
        self.active_midi_note_for_beam = [None] * 8

        # ------------------------------------------------------------
        # Calibration state
        # ------------------------------------------------------------
        self.calibration_is_active = False
        self.calibration_beam_index = 0
        self.calibration_beam_passed = [False] * 8

        # ------------------------------------------------------------
        # MIDI connections
        # ------------------------------------------------------------
        self.pico_midi_input = None
        self.fluidsynth_midi_output = None

        # ------------------------------------------------------------
        # Tkinter variables
        # ------------------------------------------------------------
        self.selected_instrument = tk.StringVar(
            value="Grand Piano"
        )

        self.volume_percent = tk.IntVar(
            value=80
        )

        self.selected_key = tk.StringVar(
            value="C"
        )

        self.octave_shift = tk.IntVar(
            value=0
        )

        self.octave_display_text = tk.StringVar(
            value="0"
        )

        self.note_duration_seconds = tk.DoubleVar(
            value=2.0
        )

        self.note_duration_display_text = tk.StringVar(
            value="2.00 s"
        )

        self.status_message = tk.StringVar(
            value="Starting MIDI connections..."
        )

        # Header fullscreen button is created later.
        self.fullscreen_toggle_button = None

        # ------------------------------------------------------------
        # Build the GUI
        # ------------------------------------------------------------
        self.build_header()
        self.build_beam_section()
        self.build_control_panel()
        self.build_status_bar()

        # ------------------------------------------------------------
        # Connect MIDI
        # ------------------------------------------------------------
        self.connect_pico_midi_input()
        self.connect_fluidsynth_midi_output()

        # Continuously poll for Pico MIDI messages.
        self.root.after(
            10,
            self.poll_pico_midi_messages
        )

    # ==============================================================
    # GUI CONSTRUCTION
    # ==============================================================

    def build_header(self):
        header_frame = tk.Frame(
            self.root,
            bg="#0f172a",
            height=80
        )

        header_frame.pack(
            fill="x"
        )

        title_label = tk.Label(
            header_frame,
            text="LASER LYRE",
            font=("Arial", 28, "bold"),
            fg="white",
            bg="#0f172a"
        )

        title_label.pack(
            side="left",
            padx=25,
            pady=18
        )

        # Exit button stays on the far-right side.
        exit_button = tk.Button(
            header_frame,
            text="Exit",
            font=("Arial", 14, "bold"),
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            command=self.close_application,
            width=10
        )

        exit_button.pack(
            side="right",
            padx=(10, 25),
            pady=18
        )

        # Fullscreen / Restore button appears beside Exit.
        self.fullscreen_toggle_button = tk.Button(
            header_frame,
            text="Restore",
            font=("Arial", 14, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            command=self.toggle_fullscreen_mode,
            width=12
        )

        self.fullscreen_toggle_button.pack(
            side="right",
            padx=(10, 0),
            pady=18
        )

        self.update_fullscreen_button_text()

    def build_beam_section(self):
        beam_section_frame = tk.Frame(
            self.root,
            bg="#111827"
        )

        beam_section_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        beam_section_title = tk.Label(
            beam_section_frame,
            text="Laser Strings",
            font=("Arial", 20, "bold"),
            fg="white",
            bg="#111827"
        )

        beam_section_title.pack(
            pady=(0, 15)
        )

        beam_button_frame = tk.Frame(
            beam_section_frame,
            bg="#111827"
        )

        beam_button_frame.pack(
            expand=True
        )

        for beam_index in range(8):
            beam_button = tk.Button(
                beam_button_frame,
                text=(
                    f"Beam {beam_index + 1}\n"
                    f"{self.get_beam_display_note_name(beam_index)}"
                ),
                width=8,
                height=5,
                font=("Arial", 14, "bold"),
                bg="#1f2937",
                fg="white",
                activebackground="#2563eb",
                activeforeground="white",
                command=lambda index=beam_index:
                    self.toggle_manual_beam_test(index)
            )

            beam_button.grid(
                row=0,
                column=beam_index,
                padx=5,
                pady=5,
                sticky="nsew"
            )

            self.beam_buttons.append(
                beam_button
            )

            beam_button_frame.grid_columnconfigure(
                beam_index,
                weight=1
            )

    def build_control_panel(self):
        controls_frame = tk.Frame(
            self.root,
            bg="#1f2937"
        )

        controls_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )

        # ----------------------------------------------------------
        # Instrument
        # ----------------------------------------------------------

        instrument_label = tk.Label(
            controls_frame,
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
            controls_frame,
            textvariable=self.selected_instrument,
            values=list(
                self.instrument_program_numbers.keys()
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
            self.handle_instrument_selection_changed
        )

        # ----------------------------------------------------------
        # Volume
        # ----------------------------------------------------------

        volume_label = tk.Label(
            controls_frame,
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
            controls_frame,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.volume_percent,
            command=self.handle_volume_slider_changed,
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

        # ----------------------------------------------------------
        # Key
        # ----------------------------------------------------------

        key_label = tk.Label(
            controls_frame,
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
            controls_frame,
            textvariable=self.selected_key,
            values=list(
                self.key_semitone_offsets.keys()
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
            self.handle_key_selection_changed
        )

        # ----------------------------------------------------------
        # Octave
        # ----------------------------------------------------------

        octave_label = tk.Label(
            controls_frame,
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
            controls_frame,
            text="-",
            font=("Arial", 14, "bold"),
            command=self.decrease_octave_shift,
            width=3
        )

        octave_down_button.grid(
            row=0,
            column=7,
            padx=4,
            pady=18
        )

        octave_value_label = tk.Label(
            controls_frame,
            textvariable=self.octave_display_text,
            font=("Arial", 15, "bold"),
            fg="white",
            bg="#1f2937",
            width=3
        )

        octave_value_label.grid(
            row=0,
            column=8,
            padx=2,
            pady=18
        )

        octave_up_button = tk.Button(
            controls_frame,
            text="+",
            font=("Arial", 14, "bold"),
            command=self.increase_octave_shift,
            width=3
        )

        octave_up_button.grid(
            row=0,
            column=9,
            padx=4,
            pady=18
        )

        # ----------------------------------------------------------
        # Calibration
        # ----------------------------------------------------------

        calibration_button = tk.Button(
            controls_frame,
            text="Calibrate",
            font=("Arial", 14, "bold"),
            bg="#f59e0b",
            fg="black",
            activebackground="#d97706",
            activeforeground="black",
            command=self.start_beam_calibration,
            width=11
        )

        calibration_button.grid(
            row=0,
            column=10,
            padx=20,
            pady=18
        )

        # ----------------------------------------------------------
        # Note duration
        # ----------------------------------------------------------

        note_duration_label = tk.Label(
            controls_frame,
            text="Note Duration:",
            font=("Arial", 15, "bold"),
            fg="white",
            bg="#1f2937"
        )

        note_duration_label.grid(
            row=1,
            column=0,
            padx=15,
            pady=(0, 12)
        )

        note_duration_slider = tk.Scale(
            controls_frame,
            from_=0.25,
            to=5.0,
            resolution=0.25,
            orient="horizontal",
            variable=self.note_duration_seconds,
            command=self.handle_note_duration_slider_changed,
            length=500,
            font=("Arial", 12),
            bg="#1f2937",
            fg="white",
            troughcolor="#374151",
            highlightthickness=0,
            showvalue=False
        )

        note_duration_slider.grid(
            row=1,
            column=1,
            columnspan=7,
            padx=10,
            pady=(0, 12),
            sticky="ew"
        )

        note_duration_value_label = tk.Label(
            controls_frame,
            textvariable=self.note_duration_display_text,
            font=("Arial", 15, "bold"),
            fg="#86efac",
            bg="#1f2937",
            width=7
        )

        note_duration_value_label.grid(
            row=1,
            column=8,
            columnspan=2,
            padx=10,
            pady=(0, 12)
        )

        controls_frame.grid_columnconfigure(
            3,
            weight=1
        )

    def build_status_bar(self):
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_message,
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

    # ==============================================================
    # MIDI CONNECTIONS
    # ==============================================================

    def connect_pico_midi_input(self):
        try:
            # Do not open a duplicate connection.
            if self.pico_midi_input is not None:
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
                self.status_message.set(
                    "Pico MIDI not found. Retrying..."
                )

                self.root.after(
                    2000,
                    self.connect_pico_midi_input
                )

                return

            self.pico_midi_input = mido.open_input(
                pico_port_name
            )

            self.status_message.set(
                f"Pico connected: {pico_port_name}"
            )

        except Exception as error:
            self.pico_midi_input = None

            self.status_message.set(
                f"Pico connection error: {error}"
            )

            self.root.after(
                2000,
                self.connect_pico_midi_input
            )

    def connect_fluidsynth_midi_output(self):
        try:
            # Do not open a duplicate connection.
            if self.fluidsynth_midi_output is not None:
                return

            fluidsynth_port_name = None

            for port_name in mido.get_output_names():
                if "FLUID Synth" in port_name:
                    fluidsynth_port_name = port_name
                    break

            if fluidsynth_port_name is None:
                self.status_message.set(
                    "FluidSynth MIDI output not found. Retrying..."
                )

                self.root.after(
                    2000,
                    self.connect_fluidsynth_midi_output
                )

                return

            self.fluidsynth_midi_output = mido.open_output(
                fluidsynth_port_name
            )

            self.send_selected_instrument_program_change()

            self.handle_volume_slider_changed(
                self.volume_percent.get()
            )

            self.status_message.set(
                f"Ready — "
                f"{self.selected_instrument.get()} — "
                f"Key {self.selected_key.get()} — "
                f"Octave {self.octave_display_text.get()}"
            )

        except Exception as error:
            self.fluidsynth_midi_output = None

            self.status_message.set(
                f"FluidSynth connection error: {error}"
            )

            self.root.after(
                2000,
                self.connect_fluidsynth_midi_output
            )

    def poll_pico_midi_messages(self):
        try:
            if self.pico_midi_input is not None:
                for message in self.pico_midi_input.iter_pending():
                    self.process_pico_midi_message(
                        message
                    )

        except Exception as error:
            self.status_message.set(
                f"Pico disconnected: {error}"
            )

            try:
                if self.pico_midi_input is not None:
                    self.pico_midi_input.close()
            except Exception:
                pass

            self.pico_midi_input = None

            self.root.after(
                2000,
                self.connect_pico_midi_input
            )

        self.root.after(
            10,
            self.poll_pico_midi_messages
        )

    # ==============================================================
    # MIDI NOTE PROCESSING
    # ==============================================================

    def process_pico_midi_message(self, message):
        if not hasattr(message, "note"):
            return

        if message.note not in self.midi_note_to_beam_index:
            return

        beam_index = self.midi_note_to_beam_index[
            message.note
        ]

        # Calibration mode uses the Pico trigger only for testing.
        if self.calibration_is_active:
            if (
                message.type == "note_on"
                and message.velocity > 0
            ):
                self.process_calibration_beam_trigger(
                    beam_index
                )

            return

        # ----------------------------------------------------------
        # Beam broken / MIDI Note ON
        # ----------------------------------------------------------

        if (
            message.type == "note_on"
            and message.velocity > 0
        ):
            self.cancel_beam_note_off_timer(
                beam_index
            )

            self.send_note_off_for_beam(
                beam_index
            )

            transposed_note = self.transpose_midi_note(
                message.note
            )

            if self.fluidsynth_midi_output is not None:
                try:
                    self.fluidsynth_midi_output.send(
                        mido.Message(
                            "note_on",
                            channel=0,
                            note=transposed_note,
                            velocity=message.velocity
                        )
                    )

                    self.active_midi_note_for_beam[
                        beam_index
                    ] = transposed_note

                except Exception as error:
                    self.status_message.set(
                        f"MIDI output error: {error}"
                    )
                    return

            self.mark_beam_as_active(
                beam_index
            )

            self.schedule_beam_note_off(
                beam_index
            )

        # ----------------------------------------------------------
        # Beam restored / MIDI Note OFF
        # ----------------------------------------------------------

        elif (
            message.type == "note_off"
            or (
                message.type == "note_on"
                and message.velocity == 0
            )
        ):
            self.cancel_beam_note_off_timer(
                beam_index
            )

            self.send_note_off_for_beam(
                beam_index
            )

            self.mark_beam_as_inactive(
                beam_index
            )

    # ==============================================================
    # NOTE TRANSPOSITION / DISPLAY
    # ==============================================================

    def calculate_total_transposition_semitones(self):
        key_shift = self.key_semitone_offsets[
            self.selected_key.get()
        ]

        octave_shift = (
            self.octave_shift.get() * 12
        )

        return key_shift + octave_shift

    def transpose_midi_note(self, original_midi_note):
        transposed_note = (
            original_midi_note
            + self.calculate_total_transposition_semitones()
        )

        # MIDI note numbers must remain between 0 and 127.
        return max(
            0,
            min(127, transposed_note)
        )

    def format_midi_note_name(self, midi_note):
        note_name = self.chromatic_note_names[
            midi_note % 12
        ]

        octave_number = (
            midi_note // 12
        ) - 1

        return f"{note_name}{octave_number}"

    def get_beam_display_note_name(self, beam_index):
        transposed_note = self.transpose_midi_note(
            self.base_midi_notes[beam_index]
        )

        return self.format_midi_note_name(
            transposed_note
        )

    def refresh_beam_note_labels(self):
        if self.calibration_is_active:
            return

        for beam_index in range(8):
            if not self.beam_is_active[beam_index]:
                self.beam_buttons[beam_index].configure(
                    text=(
                        f"Beam {beam_index + 1}\n"
                        f"{self.get_beam_display_note_name(beam_index)}"
                    )
                )

    # ==============================================================
    # KEY CONTROL
    # ==============================================================

    def handle_key_selection_changed(self, event=None):
        self.stop_all_active_notes()

        self.refresh_beam_note_labels()

        self.status_message.set(
            f"Key changed to {self.selected_key.get()}"
        )

    # ==============================================================
    # OCTAVE CONTROL
    # ==============================================================

    def decrease_octave_shift(self):
        new_octave_shift = (
            self.octave_shift.get() - 1
        )

        if new_octave_shift < -3:
            self.status_message.set(
                "Minimum octave reached"
            )
            return

        self.stop_all_active_notes()

        self.octave_shift.set(
            new_octave_shift
        )

        self.update_octave_display_text()
        self.refresh_beam_note_labels()

        self.status_message.set(
            f"Octave changed to "
            f"{self.octave_display_text.get()}"
        )

    def increase_octave_shift(self):
        new_octave_shift = (
            self.octave_shift.get() + 1
        )

        if new_octave_shift > 3:
            self.status_message.set(
                "Maximum octave reached"
            )
            return

        self.stop_all_active_notes()

        self.octave_shift.set(
            new_octave_shift
        )

        self.update_octave_display_text()
        self.refresh_beam_note_labels()

        self.status_message.set(
            f"Octave changed to "
            f"{self.octave_display_text.get()}"
        )

    def update_octave_display_text(self):
        octave_value = self.octave_shift.get()

        if octave_value > 0:
            self.octave_display_text.set(
                f"+{octave_value}"
            )
        else:
            self.octave_display_text.set(
                str(octave_value)
            )

    # ==============================================================
    # NOTE TIMERS
    # ==============================================================

    def schedule_beam_note_off(self, beam_index):
        self.cancel_beam_note_off_timer(
            beam_index
        )

        note_duration_milliseconds = max(
            1,
            int(
                self.note_duration_seconds.get()
                * 1000
            )
        )

        self.beam_note_off_timers[
            beam_index
        ] = self.root.after(
            note_duration_milliseconds,
            lambda index=beam_index:
                self.stop_beam_note_after_duration(index)
        )

    def cancel_beam_note_off_timer(self, beam_index):
        timer_id = self.beam_note_off_timers[
            beam_index
        ]

        if timer_id is None:
            return

        try:
            self.root.after_cancel(
                timer_id
            )
        except Exception:
            pass

        self.beam_note_off_timers[
            beam_index
        ] = None

    def stop_beam_note_after_duration(self, beam_index):
        self.beam_note_off_timers[
            beam_index
        ] = None

        self.send_note_off_for_beam(
            beam_index
        )

        self.mark_beam_as_inactive(
            beam_index
        )

        self.status_message.set(
            f"Beam {beam_index + 1} stopped after "
            f"{self.note_duration_seconds.get():.2f} seconds"
        )

    def send_note_off_for_beam(self, beam_index):
        active_note = self.active_midi_note_for_beam[
            beam_index
        ]

        if active_note is None:
            return

        if self.fluidsynth_midi_output is not None:
            try:
                self.fluidsynth_midi_output.send(
                    mido.Message(
                        "note_off",
                        channel=0,
                        note=active_note,
                        velocity=0
                    )
                )

            except Exception as error:
                self.status_message.set(
                    f"Note-off error: {error}"
                )

        self.active_midi_note_for_beam[
            beam_index
        ] = None

    def stop_all_active_notes(self):
        for beam_index in range(8):
            self.cancel_beam_note_off_timer(
                beam_index
            )

            self.send_note_off_for_beam(
                beam_index
            )

            self.beam_is_active[
                beam_index
            ] = False

        self.refresh_beam_note_labels()

    # ==============================================================
    # BEAM DISPLAY
    # ==============================================================

    def mark_beam_as_active(self, beam_index):
        self.beam_is_active[
            beam_index
        ] = True

        self.beam_buttons[
            beam_index
        ].configure(
            bg="#22c55e",
            activebackground="#16a34a",
            text=(
                f"Beam {beam_index + 1}\n"
                f"ACTIVE"
            )
        )

        self.status_message.set(
            f"Beam {beam_index + 1} broken — "
            f"{self.get_beam_display_note_name(beam_index)} playing"
        )

    def mark_beam_as_inactive(self, beam_index):
        self.beam_is_active[
            beam_index
        ] = False

        self.beam_buttons[
            beam_index
        ].configure(
            bg="#1f2937",
            activebackground="#2563eb",
            text=(
                f"Beam {beam_index + 1}\n"
                f"{self.get_beam_display_note_name(beam_index)}"
            )
        )

        self.status_message.set(
            f"Beam {beam_index + 1} restored"
        )

    # ==============================================================
    # MANUAL BEAM TEST
    # ==============================================================

    def toggle_manual_beam_test(self, beam_index):
        if self.calibration_is_active:
            return

        # If already active, clicking again stops the beam.
        if self.beam_is_active[beam_index]:
            self.cancel_beam_note_off_timer(
                beam_index
            )

            self.send_note_off_for_beam(
                beam_index
            )

            self.mark_beam_as_inactive(
                beam_index
            )

            return

        transposed_note = self.transpose_midi_note(
            self.base_midi_notes[beam_index]
        )

        if self.fluidsynth_midi_output is not None:
            try:
                self.fluidsynth_midi_output.send(
                    mido.Message(
                        "note_on",
                        channel=0,
                        note=transposed_note,
                        velocity=127
                    )
                )

                self.active_midi_note_for_beam[
                    beam_index
                ] = transposed_note

            except Exception as error:
                self.status_message.set(
                    f"Manual MIDI test failed: {error}"
                )
                return

        self.mark_beam_as_active(
            beam_index
        )

        self.schedule_beam_note_off(
            beam_index
        )

    # ==============================================================
    # INSTRUMENT CONTROL
    # ==============================================================

    def send_selected_instrument_program_change(self):
        if self.fluidsynth_midi_output is None:
            return

        instrument_name = self.selected_instrument.get()

        program_number = self.instrument_program_numbers[
            instrument_name
        ]

        self.fluidsynth_midi_output.send(
            mido.Message(
                "program_change",
                channel=0,
                program=program_number
            )
        )

    def handle_instrument_selection_changed(self, event=None):
        try:
            if self.fluidsynth_midi_output is None:
                self.status_message.set(
                    "FluidSynth is not connected"
                )
                return

            self.stop_all_active_notes()

            self.send_selected_instrument_program_change()

            self.status_message.set(
                f"Instrument changed to "
                f"{self.selected_instrument.get()}"
            )

        except Exception as error:
            self.status_message.set(
                f"Instrument change failed: {error}"
            )

    # ==============================================================
    # VOLUME CONTROL
    # ==============================================================

    def handle_volume_slider_changed(self, slider_value):
        volume_percent = int(
            float(slider_value)
        )

        if self.fluidsynth_midi_output is None:
            return

        # Convert 0-100 GUI volume into MIDI's 0-127 range.
        midi_volume = int(
            (volume_percent / 100)
            * 127
        )

        try:
            self.fluidsynth_midi_output.send(
                mido.Message(
                    "control_change",
                    channel=0,
                    control=7,
                    value=midi_volume
                )
            )

            self.status_message.set(
                f"Volume: {volume_percent}%"
            )

        except Exception as error:
            self.status_message.set(
                f"Volume change failed: {error}"
            )

    # ==============================================================
    # NOTE DURATION CONTROL
    # ==============================================================

    def handle_note_duration_slider_changed(self, slider_value):
        duration_seconds = float(
            slider_value
        )

        self.note_duration_display_text.set(
            f"{duration_seconds:.2f} s"
        )

        self.status_message.set(
            f"Note duration: "
            f"{duration_seconds:.2f} seconds"
        )

    # ==============================================================
    # CALIBRATION
    # ==============================================================

    def start_beam_calibration(self):
        self.stop_all_active_notes()

        self.calibration_is_active = True
        self.calibration_beam_index = 0
        self.calibration_beam_passed = [False] * 8

        for beam_index in range(8):
            self.cancel_beam_note_off_timer(
                beam_index
            )

            self.beam_is_active[
                beam_index
            ] = False

            self.beam_buttons[
                beam_index
            ].configure(
                bg="#1f2937",
                activebackground="#2563eb",
                text=(
                    f"Beam {beam_index + 1}\n"
                    f"{self.get_beam_display_note_name(beam_index)}"
                )
            )

        self.refresh_calibration_beam_display()

        self.status_message.set(
            "Calibration started — break Beam 1"
        )

    def refresh_calibration_beam_display(self):
        for beam_index in range(8):
            if self.calibration_beam_passed[beam_index]:
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

            elif beam_index == self.calibration_beam_index:
                self.beam_buttons[
                    beam_index
                ].configure(
                    bg="#f59e0b",
                    activebackground="#d97706",
                    text=(
                        f"Beam {beam_index + 1}\n"
                        f"TEST"
                    )
                )

            else:
                self.beam_buttons[
                    beam_index
                ].configure(
                    bg="#1f2937",
                    activebackground="#2563eb",
                    text=(
                        f"Beam {beam_index + 1}\n"
                        f"{self.get_beam_display_note_name(beam_index)}"
                    )
                )

    def process_calibration_beam_trigger(self, beam_index):
        if beam_index != self.calibration_beam_index:
            self.status_message.set(
                f"Wrong beam — break Beam "
                f"{self.calibration_beam_index + 1}"
            )
            return

        self.calibration_beam_passed[
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

        # If this was Beam 8, calibration is complete.
        if self.calibration_beam_index == 7:
            self.status_message.set(
                "Calibration complete — all 8 beams passed"
            )

            self.root.after(
                2000,
                self.reset_after_completed_calibration
            )

            return

        self.calibration_beam_index += 1

        self.refresh_calibration_beam_display()

        self.status_message.set(
            f"Beam {beam_index + 1} passed — "
            f"break Beam "
            f"{self.calibration_beam_index + 1}"
        )

    def reset_after_completed_calibration(self):
        self.calibration_is_active = False
        self.calibration_beam_index = 0
        self.calibration_beam_passed = [False] * 8
        self.beam_is_active = [False] * 8

        for beam_index in range(8):
            self.beam_buttons[
                beam_index
            ].configure(
                bg="#1f2937",
                activebackground="#2563eb",
                text=(
                    f"Beam {beam_index + 1}\n"
                    f"{self.get_beam_display_note_name(beam_index)}"
                )
            )

        self.status_message.set(
            f"Ready — "
            f"{self.selected_instrument.get()} — "
            f"Key {self.selected_key.get()} — "
            f"Octave {self.octave_display_text.get()}"
        )

    # ==============================================================
    # WINDOW / FULLSCREEN CONTROL
    # ==============================================================

    def exit_fullscreen_mode(self, event=None):
        self.root.attributes(
            "-fullscreen",
            False
        )

        self.update_fullscreen_button_text()

    def toggle_fullscreen_mode(self, event=None):
        fullscreen_is_enabled = bool(
            self.root.attributes("-fullscreen")
        )

        self.root.attributes(
            "-fullscreen",
            not fullscreen_is_enabled
        )

        # Give Tkinter time to apply the window state before updating
        # the button label.
        self.root.after(
            50,
            self.update_fullscreen_button_text
        )

    def update_fullscreen_button_text(self):
        if self.fullscreen_toggle_button is None:
            return

        fullscreen_is_enabled = bool(
            self.root.attributes("-fullscreen")
        )

        if fullscreen_is_enabled:
            self.fullscreen_toggle_button.configure(
                text="Restore"
            )
        else:
            self.fullscreen_toggle_button.configure(
                text="Fullscreen"
            )

    # ==============================================================
    # APPLICATION SHUTDOWN
    # ==============================================================

    def close_application(self):
        # Stop every scheduled timer and sounding note first.
        self.stop_all_active_notes()

        # MIDI panic: tell FluidSynth to stop any remaining notes.
        if self.fluidsynth_midi_output is not None:
            try:
                self.fluidsynth_midi_output.send(
                    mido.Message(
                        "control_change",
                        channel=0,
                        control=123,
                        value=0
                    )
                )
            except Exception:
                pass

        # Close Pico MIDI input.
        try:
            if self.pico_midi_input is not None:
                self.pico_midi_input.close()
        except Exception:
            pass

        # Close FluidSynth MIDI output.
        try:
            if self.fluidsynth_midi_output is not None:
                self.fluidsynth_midi_output.close()
        except Exception:
            pass

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    laser_lyre_gui = LaserLyreGUI(root)
    root.mainloop()