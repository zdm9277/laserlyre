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

        # Notes used by the eight laser strings.
        self.notes = ["C", "D", "E", "F", "G", "A", "B", "C"]

        # MIDI note numbers sent by the Pico.
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

        self.beam_states = [False] * 8
        self.beam_buttons = []

        # Calibration state.
        self.calibration_active = False
        self.calibration_beam = 0
        self.calibration_passed = [False] * 8

        # MIDI connections.
        self.midi_input = None
        self.midi_output = None

        # GUI variables.
        self.instrument_var = tk.StringVar(value="Grand Piano")
        self.volume_var = tk.IntVar(value=80)
        self.status_var = tk.StringVar(
            value="Starting MIDI connections..."
        )

        self.create_header()
        self.create_beam_section()
        self.create_controls()
        self.create_status_bar()

        self.connect_to_pico()
        self.connect_to_fluidsynth()

        self.root.after(10, self.check_midi)

    def create_header(self):
        header = tk.Frame(
            self.root,
            bg="#0f172a",
            height=80
        )
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="LASER LYRE",
            font=("Arial", 28, "bold"),
            fg="white",
            bg="#0f172a"
        )
        title.pack(side="left", padx=25, pady=18)

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
        exit_button.pack(side="right", padx=25, pady=18)

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
        beam_title.pack(pady=(0, 15))

        button_frame = tk.Frame(
            beam_frame,
            bg="#111827"
        )
        button_frame.pack(expand=True)

        for index in range(8):
            button = tk.Button(
                button_frame,
                text=f"Beam {index + 1}\n{self.notes[index]}",
                width=8,
                height=5,
                font=("Arial", 14, "bold"),
                bg="#1f2937",
                fg="white",
                activebackground="#2563eb",
                activeforeground="white",
                command=lambda i=index: self.manual_beam_test(i)
            )

            button.grid(
                row=0,
                column=index,
                padx=5,
                pady=5,
                sticky="nsew"
            )

            self.beam_buttons.append(button)
            button_frame.grid_columnconfigure(index, weight=1)

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
            padx=15,
            pady=18
        )

        instrument_menu = ttk.Combobox(
            controls,
            textvariable=self.instrument_var,
            values=list(self.instrument_programs.keys()),
            state="readonly",
            font=("Arial", 14),
            width=20
        )
        instrument_menu.grid(
            row=0,
            column=1,
            padx=10,
            pady=18
        )

        instrument_menu.bind(
            "<<ComboboxSelected>>",
            self.instrument_changed
        )

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
            padx=(30, 10),
            pady=18
        )

        volume_slider = tk.Scale(
            controls,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.volume_var,
            command=self.volume_changed,
            length=250,
            font=("Arial", 12),
            bg="#1f2937",
            fg="white",
            troughcolor="#374151",
            highlightthickness=0
        )
        volume_slider.grid(
            row=0,
            column=3,
            padx=10,
            pady=8
        )

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
            column=4,
            padx=20,
            pady=18
        )

        controls.grid_columnconfigure(3, weight=1)

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
        status_bar.pack(fill="x", side="bottom")

    def connect_to_pico(self):
        try:
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
                self.root.after(2000, self.connect_to_pico)
                return

            self.midi_input = mido.open_input(pico_port_name)

            self.status_var.set(
                f"Pico connected: {pico_port_name}"
            )

        except Exception as error:
            self.midi_input = None

            self.status_var.set(
                f"Pico connection error: {error}"
            )

            self.root.after(2000, self.connect_to_pico)

    def connect_to_fluidsynth(self):
        try:
            fluid_port_name = None

            for port_name in mido.get_output_names():
                if "FLUID Synth" in port_name:
                    fluid_port_name = port_name
                    break

            if fluid_port_name is None:
                self.status_var.set(
                    "FluidSynth MIDI output not found. Retrying..."
                )
                self.root.after(
                    2000,
                    self.connect_to_fluidsynth
                )
                return

            self.midi_output = mido.open_output(
                fluid_port_name
            )

            # Apply the default instrument and volume.
            self.send_program_change()
            self.volume_changed(self.volume_var.get())

            self.status_var.set(
                f"Ready — {self.instrument_var.get()}"
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
            self.root.after(2000, self.connect_to_pico)

        self.root.after(10, self.check_midi)

    def handle_midi_message(self, message):
        if not hasattr(message, "note"):
            return

        if message.note not in self.midi_note_to_beam:
            return

        beam_index = self.midi_note_to_beam[message.note]

        if self.calibration_active:
            # During calibration, only beam breaks matter.
            # Note-off messages are ignored so PASSED beams stay green.
            if (
                message.type == "note_on"
                and message.velocity > 0
            ):
                self.handle_calibration_note(beam_index)

            return

        if (
            message.type == "note_on"
            and message.velocity > 0
        ):
            self.set_beam_active(beam_index)

        elif message.type == "note_off":
            self.set_beam_inactive(beam_index)

        elif (
            message.type == "note_on"
            and message.velocity == 0
        ):
            self.set_beam_inactive(beam_index)

    def set_beam_active(self, index):
        self.beam_states[index] = True

        self.beam_buttons[index].configure(
            bg="#22c55e",
            activebackground="#16a34a",
            text=f"Beam {index + 1}\nACTIVE"
        )

        self.status_var.set(
            f"Beam {index + 1} broken — "
            f"{self.notes[index]} playing"
        )

    def set_beam_inactive(self, index):
        self.beam_states[index] = False

        self.beam_buttons[index].configure(
            bg="#1f2937",
            activebackground="#2563eb",
            text=f"Beam {index + 1}\n{self.notes[index]}"
        )

        self.status_var.set(
            f"Beam {index + 1} restored"
        )

    def manual_beam_test(self, index):
        if self.calibration_active:
            return

        if self.beam_states[index]:
            self.set_beam_inactive(index)
        else:
            self.set_beam_active(index)

    def send_program_change(self):
        if self.midi_output is None:
            return

        instrument = self.instrument_var.get()
        program_number = self.instrument_programs[instrument]

        message = mido.Message(
            "program_change",
            channel=0,
            program=program_number
        )

        self.midi_output.send(message)

    def instrument_changed(self, event=None):
        try:
            if self.midi_output is None:
                self.status_var.set(
                    "FluidSynth is not connected"
                )
                return

            self.send_program_change()

            self.status_var.set(
                f"Instrument changed to "
                f"{self.instrument_var.get()}"
            )

        except Exception as error:
            self.status_var.set(
                f"Instrument change failed: {error}"
            )

    def volume_changed(self, value):
        volume_percent = int(float(value))

        if self.midi_output is None:
            return

        # MIDI volume ranges from 0 through 127.
        midi_volume = int(
            (volume_percent / 100) * 127
        )

        try:
            message = mido.Message(
                "control_change",
                channel=0,
                control=7,
                value=midi_volume
            )

            self.midi_output.send(message)

            self.status_var.set(
                f"Volume: {volume_percent}%"
            )

        except Exception as error:
            self.status_var.set(
                f"Volume change failed: {error}"
            )

    def calibrate(self):
        self.calibration_active = True
        self.calibration_beam = 0
        self.calibration_passed = [False] * 8

        for index in range(8):
            self.beam_states[index] = False

            self.beam_buttons[index].configure(
                bg="#1f2937",
                activebackground="#2563eb",
                text=f"Beam {index + 1}\n{self.notes[index]}"
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
                    text=f"Beam {index + 1}\nPASSED"
                )

            elif index == self.calibration_beam:
                self.beam_buttons[index].configure(
                    bg="#f59e0b",
                    activebackground="#d97706",
                    text=f"Beam {index + 1}\nTEST"
                )

            else:
                self.beam_buttons[index].configure(
                    bg="#1f2937",
                    activebackground="#2563eb",
                    text=f"Beam {index + 1}\n{self.notes[index]}"
                )

    def handle_calibration_note(self, beam_index):
        if beam_index != self.calibration_beam:
            self.status_var.set(
                f"Wrong beam — break Beam "
                f"{self.calibration_beam + 1}"
            )
            return

        self.calibration_passed[beam_index] = True

        self.beam_buttons[beam_index].configure(
            bg="#22c55e",
            activebackground="#16a34a",
            text=f"Beam {beam_index + 1}\nPASSED"
        )

        if self.calibration_beam == 7:
            self.status_var.set(
                "Calibration complete — all 8 beams passed"
            )

            # Keep calibration active briefly so the final
            # note-off does not erase the PASSED display.
            self.root.after(
                2000,
                self.reset_after_calibration
            )
            return

        self.calibration_beam += 1
        self.highlight_calibration_beam()

        self.status_var.set(
            f"Beam {beam_index + 1} passed — "
            f"break Beam {self.calibration_beam + 1}"
        )

    def reset_after_calibration(self):
        self.calibration_active = False
        self.calibration_beam = 0
        self.calibration_passed = [False] * 8
        self.beam_states = [False] * 8

        for index in range(8):
            self.beam_buttons[index].configure(
                bg="#1f2937",
                activebackground="#2563eb",
                text=f"Beam {index + 1}\n{self.notes[index]}"
            )

        self.status_var.set(
            f"Ready — {self.instrument_var.get()}"
        )

    def exit_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", False)

    def close_program(self):
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
