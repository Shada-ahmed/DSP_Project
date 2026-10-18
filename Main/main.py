import sys
import tempfile
from functools import partial
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap, QPolygonF
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QCheckBox,
    QFormLayout,
    QScrollArea,
    QSizePolicy,
    QAbstractItemView,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from Functionality import (
    read_signal,
    delay,
    advance,
    fold_signal,
    multiply_signal,
    add_signals,
    subtract_signals,
    generate_signal,
    generate_discrete_signal,
)


def create_arrow_icons():
    """
    Draw the small up/down arrows used by spin boxes and drop-downs.

    Once spin boxes / combo boxes get a custom border in the stylesheet, Qt no
    longer draws their arrows (they end up clipped or missing), so we paint
    them ourselves and reference the PNGs from the stylesheet.
    """
    folder = Path(tempfile.gettempdir()) / "dsp_project_ui"
    folder.mkdir(exist_ok=True)

    paths = {}
    for name, points in (
        ("up", [(1, 7), (5, 2), (9, 7)]),
        ("down", [(1, 3), (5, 8), (9, 3)]),
    ):
        pixmap = QPixmap(10, 10)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#4A5B75"))
        painter.drawPolygon(QPolygonF([QPointF(x, y) for x, y in points]))
        painter.end()

        file_path = folder / f"{name}.png"
        pixmap.save(str(file_path))
        paths[name] = file_path.as_posix()

    return paths


class SignalCanvas(FigureCanvas):

    def __init__(self):
        self.figure = Figure(figsize=(8, 5))
        self.ax = self.figure.add_subplot(111)

        super().__init__(self.figure)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(220)

        self.plot_empty()

    def plot_empty(self):
        self.ax.clear()
        self.figure.legends.clear()

        self.ax.set_title("Signal Plot", color="#17243A", pad=14, fontsize=14)
        self.ax.set_xlabel("n")
        self.ax.set_ylabel("x[n]")
        self.ax.grid(True, color="#DCE4EF", linewidth=0.8)

        self.ax.axhline(0, linewidth=1, color="#8290A5")
        self.ax.axvline(0, linewidth=1, color="#8290A5")

        self.figure.tight_layout()
        self.draw()

    def plot_signal(self, signal, title):

        self.ax.clear()
        self.figure.legends.clear()

        self.ax.stem(
            signal.indices,
            signal.values
        )

        self.ax.set_title(title, color="#17243A", pad=14, fontsize=14)
        self.ax.set_xlabel("n")
        self.ax.set_ylabel("x[n]")

        self.ax.grid(True, color="#DCE4EF", linewidth=0.8)

        self.ax.axhline(0, linewidth=1, color="#8290A5")
        self.ax.axvline(0, linewidth=1, color="#8290A5")

        self.figure.tight_layout()

        self.draw()

    def plot_generated_signals(self, signals, representation):
        self.ax.clear()
        self.figure.legends.clear()

        for signal in signals:
            if representation == "continuous":
                self.ax.plot(
                    signal["times"],
                    signal["values"],
                    color=signal["color"],
                    label=signal["label"],
                )
            else:
                indices = range(len(signal["values"]))
                self.ax.stem(
                    indices,
                    signal["values"],
                    linefmt=f'{signal["color"]}-',
                    markerfmt=f'{signal["color"]}o',
                    basefmt=" ",
                    label=signal["label"],
                )

        self.ax.set_title("Generated Signals", color="#17243A", pad=14, fontsize=14)
        if representation == "continuous":
            self.ax.set_xlabel("Time (s)")
            self.ax.set_ylabel("x(t)")
        else:
            self.ax.set_xlabel("Sample index n")
            self.ax.set_ylabel("x[n]")

        self.ax.grid(True, color="#DCE4EF", linewidth=0.8)
        self.ax.axhline(0, linewidth=1, color="#8290A5")
        if representation == "discrete":
            self.ax.axvline(0, linewidth=1, color="#8290A5")

        # Legend goes in its own strip at the bottom of the figure, so it
        # never hides the signals or collides with the x-axis label.
        handles, labels = self.ax.get_legend_handles_labels()
        self.figure.legend(
            handles,
            labels,
            loc="lower center",
            ncol=max(1, len(signals)),
            frameon=False,
        )

        self.figure.tight_layout(rect=(0, 0.1, 1, 1))
        self.draw()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("DSP Signal Processing")
        self.resize(1280, 900)
        self.setMinimumSize(1060, 780)

        # Input Signals list: (display name, Signal) - files or generated
        self.input_signals = []
        self.signal_controls = {}

        self.create_ui()

    def create_ui(self):
        self.create_signal_generation_menu()
        arrows = create_arrow_icons()
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #F3F6FB;
                color: #243247;
                font-family: "Segoe UI";
                font-size: 10pt;
            }
            QGroupBox {
                background-color: #FFFFFF;
                border: 1px solid #DCE4EF;
                border-radius: 10px;
                margin-top: 9px;
                padding: 8px 10px 8px 10px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                color: #34445C;
            }
            QComboBox, QDoubleSpinBox, QListWidget {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 1px 7px;
                selection-background-color: #DBEAFE;
                selection-color: #173B70;
            }
            QLabel, QCheckBox {
                background: transparent;
            }
            QComboBox, QDoubleSpinBox {
                min-height: 26px;
            }
            QComboBox {
                padding: 1px 28px 1px 8px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 24px;
                border-left: 1px solid #CBD5E1;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                image: url(%(down)s);
                width: 10px;
                height: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                selection-background-color: #DBEAFE;
                selection-color: #173B70;
                outline: 0;
            }
            QDoubleSpinBox {
                padding: 1px 26px 1px 8px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                subcontrol-origin: padding;
                width: 22px;
                border-left: 1px solid #CBD5E1;
                background-color: transparent;
            }
            QDoubleSpinBox::up-button {
                subcontrol-position: top right;
                border-top-right-radius: 5px;
                border-bottom: 1px solid #CBD5E1;
            }
            QDoubleSpinBox::down-button {
                subcontrol-position: bottom right;
                border-bottom-right-radius: 5px;
            }
            QDoubleSpinBox::up-button:hover,
            QDoubleSpinBox::down-button:hover {
                background-color: #E4EDF9;
            }
            QDoubleSpinBox::up-arrow {
                image: url(%(up)s);
                width: 10px;
                height: 10px;
            }
            QDoubleSpinBox::down-arrow {
                image: url(%(down)s);
                width: 10px;
                height: 10px;
            }
            QComboBox:hover, QDoubleSpinBox:hover, QListWidget:hover {
                border-color: #8AA8D0;
            }
            QComboBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #3974C6;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 9px 12px;
                color: #33445D;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F1F6FD;
                border-color: #9CB4D4;
            }
            QPushButton:pressed {
                background-color: #E4EDF9;
            }
            QPushButton#primaryButton {
                background-color: #2563C7;
                border-color: #2563C7;
                color: #FFFFFF;
                font-weight: 700;
                padding: 10px 16px;
            }
            QPushButton#primaryButton:hover {
                background-color: #1E55AD;
                border-color: #1E55AD;
            }
            QPushButton#secondaryButton {
                color: #43536A;
            }
            QCheckBox {
                spacing: 7px;
                color: #43536A;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QMenuBar {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E3E9F1;
                padding: 4px;
            }
            QMenuBar::item {
                padding: 7px 12px;
                border-radius: 5px;
            }
            QMenuBar::item:selected, QMenu::item:selected {
                background-color: #EAF1FB;
                color: #1D4E89;
            }
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #DCE4EF;
                padding: 5px;
            }
            QMenu::item {
                padding: 7px 24px 7px 12px;
                border-radius: 4px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QWidget#controlContent {
                background: transparent;
            }
        """ % arrows)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        workspace_layout = QHBoxLayout()
        workspace_layout.setSpacing(12)
        root_layout.addLayout(workspace_layout, stretch=1)

        control_layout = QVBoxLayout()
        control_layout.setSpacing(9)

        signal_group = QGroupBox("Input Signals")
        signal_layout = QVBoxLayout()
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.file_list.setToolTip(
            "Operations use the selected signals, or all signals when "
            "nothing is selected."
        )
        self.file_list.setWordWrap(True)
        self.file_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.file_list.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        signal_layout.addWidget(self.file_list)
        add_button = QPushButton("Add Signal")
        add_button.clicked.connect(self.add_signal_file)
        signal_layout.addWidget(add_button)
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_signal_file)
        signal_layout.addWidget(remove_button)
        signal_group.setLayout(signal_layout)
        control_layout.addWidget(signal_group)

        operation_group = QGroupBox("Operation")
        operation_layout = QVBoxLayout()
        operation_label = QLabel("Select Operation:")
        operation_label.setWordWrap(True)
        self.operation_combo = QComboBox()
        self.operation_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self.operation_combo.addItems([
            "Add", "Subtract", "Multiply", "Delay", "Advance", "Fold"
        ])
        self.operation_combo.setMinimumWidth(
            self.operation_combo.sizeHint().width()
        )
        self.operation_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.operation_combo.currentTextChanged.connect(self.operation_changed)
        operation_layout.addWidget(operation_label)
        operation_layout.addWidget(self.operation_combo)
        operation_group.setLayout(operation_layout)
        control_layout.addWidget(operation_group)

        parameter_group = QGroupBox("Parameter")
        parameter_layout = QVBoxLayout()
        self.parameter_label = QLabel("No parameter required")
        self.parameter_label.setWordWrap(True)
        parameter_layout.addWidget(self.parameter_label)
        self.parameter_spin = QDoubleSpinBox()
        self.parameter_spin.setRange(-100000, 100000)
        self.parameter_spin.setValue(1)
        self.parameter_spin.setDecimals(2)
        parameter_layout.addWidget(self.parameter_spin)
        parameter_group.setLayout(parameter_layout)
        self._configure_numeric_input(self.parameter_spin)
        control_layout.addWidget(parameter_group)

        self.apply_button = QPushButton("Apply Operation")
        self.apply_button.clicked.connect(self.apply_operation)
        control_layout.addWidget(self.apply_button)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_all)
        control_layout.addWidget(clear_button)
        control_layout.addStretch()

        self.generation_group = QGroupBox("Signal Generation")
        generation_layout = QVBoxLayout()
        generation_layout.setSpacing(10)

        self.generation_target_combo = QComboBox()
        self.generation_target_combo.addItems(["Signal 1", "Signal 2"])
        self.generation_target_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self.generation_target_combo.setMinimumWidth(
            self.generation_target_combo.sizeHint().width()
        )
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Menu actions apply to:"))
        target_layout.addWidget(self.generation_target_combo)
        target_layout.addStretch()
        generation_layout.addLayout(target_layout)

        generator_panels_layout = QHBoxLayout()
        generator_panels_layout.setSpacing(12)
        self._create_generator_panel(
            generator_panels_layout, 1, "sine", "C0"
        )
        self._create_generator_panel(
            generator_panels_layout, 2, "cosine", "C1"
        )
        generation_layout.addLayout(generator_panels_layout)

        representation_layout = QHBoxLayout()
        representation_layout.addWidget(QLabel("Representation:"))
        self.representation_combo = QComboBox()
        self.representation_combo.addItems(["Continuous", "Discrete"])
        self.representation_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self.representation_combo.setMinimumWidth(
            self.representation_combo.sizeHint().width()
        )
        self.representation_combo.setCurrentText("Discrete")
        representation_layout.addWidget(self.representation_combo)
        representation_layout.addStretch()
        generation_layout.addLayout(representation_layout)

        self.generate_button = QPushButton("Generate Signal")
        self.generate_button.setObjectName("primaryButton")
        self.generate_button.clicked.connect(self.generate_selected_signals)
        self.add_generated_button = QPushButton("Add to Input Signals")
        self.add_generated_button.setObjectName("secondaryButton")
        self.add_generated_button.setToolTip(
            "Add the checked generated signals (sampled) to the Input "
            "Signals list so the operations can use them."
        )
        self.add_generated_button.clicked.connect(
            self.add_generated_to_inputs
        )
        self.clear_plot_button = QPushButton("Clear Plot")
        self.clear_plot_button.setObjectName("secondaryButton")
        self.clear_plot_button.clicked.connect(self.clear_plot)
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        action_layout.addWidget(self.add_generated_button)
        action_layout.addWidget(self.clear_plot_button)
        action_layout.addWidget(self.generate_button)
        generation_layout.addLayout(action_layout)

        self.generation_group.setLayout(generation_layout)

        control_widget = QWidget()
        control_widget.setObjectName("controlContent")
        control_widget.setLayout(control_layout)
        control_widget.setMinimumWidth(280)
        control_widget.setMaximumWidth(310)
        self.controls_scroll = QScrollArea()
        self.controls_scroll.setWidgetResizable(True)
        self.controls_scroll.setWidget(control_widget)
        self.controls_scroll.setMinimumWidth(280)
        self.controls_scroll.setMaximumWidth(310)
        workspace_layout.insertWidget(0, self.controls_scroll)

        plot_workspace = QWidget()
        plot_layout = QVBoxLayout(plot_workspace)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(10)
        plot_layout.addWidget(self.generation_group)
        self.canvas = SignalCanvas()
        plot_layout.addWidget(self.canvas, stretch=1)
        workspace_layout.addWidget(plot_workspace, stretch=1)

        for combo in self.findChildren(QComboBox):
            combo.ensurePolished()
            combo.setMinimumWidth(combo.sizeHint().width())
            combo.view().setMinimumWidth(combo.sizeHint().width() + 20)

        self.operation_changed(self.operation_combo.currentText())

    def create_signal_generation_menu(self):
        generation_menu = self.menuBar().addMenu("Signal Generation")
        sine_action = generation_menu.addAction("Sine Wave")
        cosine_action = generation_menu.addAction("Cosine Wave")

        sine_action.triggered.connect(
            partial(self.set_selected_wave_type, "Sine")
        )
        cosine_action.triggered.connect(
            partial(self.set_selected_wave_type, "Cosine")
        )

    def _create_generator_panel(self, parent_layout, number, wave_type, color):
        panel = QGroupBox(f"Signal {number}")
        form_layout = QFormLayout()
        form_layout.setHorizontalSpacing(6)
        form_layout.setVerticalSpacing(2)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setContentsMargins(6, 10, 6, 6)

        visible = QCheckBox("Display")
        visible.setChecked(True)
        visible.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Fixed,
        )

        wave_combo = QComboBox()
        wave_combo.addItems(["Sine", "Cosine"])
        wave_combo.setCurrentText(wave_type.title())
        wave_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        wave_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        wave_combo.setMinimumWidth(wave_combo.sizeHint().width())

        amplitude = QDoubleSpinBox()
        amplitude.setRange(-1_000_000_000, 1_000_000_000)
        amplitude.setDecimals(4)
        amplitude.setValue(1)

        frequency = QDoubleSpinBox()
        frequency.setRange(0, 1_000_000_000)
        frequency.setDecimals(4)
        frequency.setValue(5 if number == 1 else 7)

        phase = QDoubleSpinBox()
        phase.setRange(-360_000, 360_000)
        phase.setDecimals(2)

        sampling_frequency = QDoubleSpinBox()
        sampling_frequency.setRange(0, 1_000_000_000)
        sampling_frequency.setDecimals(4)
        sampling_frequency.setValue(100)

        duration = QDoubleSpinBox()
        duration.setRange(0, 1_000_000_000)
        duration.setDecimals(4)
        duration.setValue(1)

        form_layout.addRow("Display:", visible)
        form_layout.addRow("Wave type:", wave_combo)
        form_layout.addRow("Amplitude:", amplitude)
        form_layout.addRow("Frequency (Hz):", frequency)
        form_layout.addRow("Phase (deg):", phase)
        form_layout.addRow("Sampling rate (Hz):", sampling_frequency)
        form_layout.addRow("Duration (s):", duration)
        panel.setLayout(form_layout)
        panel.ensurePolished()
        for spin_box in (
            amplitude,
            frequency,
            phase,
            sampling_frequency,
            duration,
        ):
            self._configure_numeric_input(spin_box)
        panel.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        parent_layout.addWidget(panel)

        self.signal_controls[number] = {
            "visible": visible,
            "wave_type": wave_combo,
            "amplitude": amplitude,
            "frequency": frequency,
            "phase": phase,
            "sampling_frequency": sampling_frequency,
            "duration": duration,
            "color": color,
        }

    @staticmethod
    def _configure_numeric_input(spin_box):
        endpoint_widths = (
            spin_box.lineEdit().fontMetrics().horizontalAdvance(
                spin_box.textFromValue(value)
            )
            for value in (spin_box.minimum(), spin_box.maximum())
        )
        spin_box.setMinimumWidth(max(endpoint_widths) + 70)
        spin_box.setAlignment(Qt.AlignmentFlag.AlignRight)
        spin_box.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

    def set_selected_wave_type(self, wave_type):
        signal_number = self.generation_target_combo.currentIndex() + 1
        controls = self.signal_controls[signal_number]
        controls["wave_type"].setCurrentText(wave_type)
        controls["wave_type"].setFocus()

    @staticmethod
    def _generator_arguments(controls):
        """Values of one generator panel, in generate_signal() order."""
        return (
            controls["wave_type"].currentText(),
            controls["amplitude"].value(),
            controls["frequency"].value(),
            controls["phase"].value(),
            controls["sampling_frequency"].value(),
            controls["duration"].value(),
        )

    def generate_selected_signals(self):
        representation = self.representation_combo.currentText().lower()
        generated = []

        for signal_number, controls in self.signal_controls.items():
            if not controls["visible"].isChecked():
                continue

            try:
                times, values = generate_signal(
                    *self._generator_arguments(controls),
                    representation,
                )
            except ValueError as error:
                QMessageBox.warning(
                    self,
                    "Invalid Signal Parameters",
                    f"Signal {signal_number}: {error}",
                )
                return

            generated.append({
                "label": f"Signal {signal_number} "
                f"({controls['wave_type'].currentText()})",
                "times": times,
                "values": values,
                "color": controls["color"],
            })

        if not generated:
            QMessageBox.warning(
                self,
                "Invalid Signal Parameters",
                "Select at least one signal to display.",
            )
            return

        self.canvas.plot_generated_signals(generated, representation)

    def add_generated_to_inputs(self):
        """Add the checked generator panels to the Input Signals list."""
        new_entries = []

        for signal_number, controls in self.signal_controls.items():
            if not controls["visible"].isChecked():
                continue

            arguments = self._generator_arguments(controls)

            try:
                signal = generate_discrete_signal(*arguments)
            except ValueError as error:
                QMessageBox.warning(
                    self,
                    "Invalid Signal Parameters",
                    f"Signal {signal_number}: {error}",
                )
                return

            wave, amplitude, frequency, phase, fs, _ = arguments
            new_entries.append((
                f"Signal {signal_number}: {wave} A={amplitude:g} "
                f"f={frequency:g}Hz phase={phase:g}deg fs={fs:g}Hz",
                signal,
            ))

        if not new_entries:
            QMessageBox.warning(
                self,
                "Invalid Signal Parameters",
                "Select at least one signal to add.",
            )
            return

        for name, signal in new_entries:
            self._add_input_signal(name, signal)

    # =========================================================
    # SIGNAL FILE MANAGEMENT
    # =========================================================

    def _add_input_signal(self, name, signal):
        """Append a signal to the list, keeping display names unique."""
        existing = {entry_name for entry_name, _ in self.input_signals}
        unique_name = name
        counter = 2
        while unique_name in existing:
            unique_name = f"{name} ({counter})"
            counter += 1

        self.input_signals.append((unique_name, signal))

        item_text = unique_name
        self.file_list.addItem(item_text)
        self.file_list.item(self.file_list.count() - 1).setToolTip(unique_name)

    def add_signal_file(self):

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Signal Files",
            str(Path.cwd() / "data"),
            "Text Files (*.txt)"
        )

        loaded = {name for name, _ in self.input_signals}

        for file in files:

            name = Path(file).name

            if name in loaded:
                continue

            try:
                signal = read_signal(file)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not read {name}:\n{e}"
                )
                continue

            self._add_input_signal(name, signal)
            loaded.add(name)

    def remove_signal_file(self):

        rows = sorted(
            {index.row() for index in self.file_list.selectedIndexes()},
            reverse=True,
        )

        for row in rows:

            self.file_list.takeItem(row)

            self.input_signals.pop(row)

    # =========================================================
    # OPERATION PARAMETER
    # =========================================================

    def operation_changed(self, operation):

        if operation == "Multiply":

            self.parameter_label.setText(
                "Constant:"
            )

            self.parameter_spin.setValue(2)

            self.parameter_spin.setEnabled(True)

        elif operation in ["Delay", "Advance"]:

            self.parameter_label.setText(
                "Number of steps (k):"
            )

            self.parameter_spin.setValue(1)

            self.parameter_spin.setEnabled(True)

        else:

            self.parameter_label.setText(
                "No parameter required"
            )

            self.parameter_spin.setEnabled(False)

    # =========================================================
    # APPLY OPERATION
    # =========================================================

    def apply_operation(self):

        if not self.input_signals:

            QMessageBox.warning(
                self,
                "No Signal",
                "Please add at least one signal "
                "(a file or a generated signal)."
            )

            return

        operation = (
            self.operation_combo.currentText()
        )

        try:

            # Selected signals if any are selected, otherwise all of them
            rows = sorted(
                {index.row() for index in self.file_list.selectedIndexes()}
            )

            if not rows:
                rows = range(len(self.input_signals))

            signals = [self.input_signals[row][1] for row in rows]

            # -----------------------------
            # ADD
            # -----------------------------

            if operation == "Add":

                if len(signals) < 2:

                    raise ValueError(
                        "Add requires at least two signals."
                    )

                result = add_signals(
                    *signals
                )

                title = "Added Signal"

            # -----------------------------
            # SUBTRACT
            # -----------------------------

            elif operation == "Subtract":

                if len(signals) != 2:

                    raise ValueError(
                        "Subtract requires exactly two signals."
                    )

                result = subtract_signals(
                    signals[0],
                    signals[1]
                )

                title = "Subtracted Signal"

            # -----------------------------
            # MULTIPLY
            # -----------------------------

            elif operation == "Multiply":

                if len(signals) != 1:

                    raise ValueError(
                        "Multiply requires exactly one signal."
                    )

                constant = (
                    self.parameter_spin.value()
                )

                result = multiply_signal(
                    signals[0],
                    constant
                )

                title = (
                    f"Signal × {constant}"
                )

            # -----------------------------
            # DELAY
            # -----------------------------

            elif operation == "Delay":

                if len(signals) != 1:

                    raise ValueError(
                        "Delay requires exactly one signal."
                    )

                k = int(
                    self.parameter_spin.value()
                )

                result = delay(
                    signals[0],
                    k
                )

                title = (
                    f"Delayed Signal by {k}"
                )

            # -----------------------------
            # ADVANCE
            # -----------------------------

            elif operation == "Advance":

                if len(signals) != 1:

                    raise ValueError(
                        "Advance requires exactly one signal."
                    )

                k = int(
                    self.parameter_spin.value()
                )

                result = advance(
                    signals[0],
                    k
                )

                title = (
                    f"Advanced Signal by {k}"
                )

            # -----------------------------
            # FOLD
            # -----------------------------

            elif operation == "Fold":

                if len(signals) != 1:

                    raise ValueError(
                        "Fold requires exactly one signal."
                    )

                result = fold_signal(
                    signals[0]
                )

                title = "Folded Signal"

            else:

                raise ValueError(
                    "Unknown operation."
                )

            # Display result

            self.canvas.plot_signal(
                result,
                title
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )

    # =========================================================
    # CLEAR
    # =========================================================

    def clear_plot(self):
        self.canvas.plot_empty()

    def clear_all(self):

        self.input_signals.clear()

        self.file_list.clear()

        self.clear_plot()


# =============================================================
# APPLICATION ENTRY POINT
# =============================================================

def main():

    app = QApplication(sys.argv)

    window = MainWindow()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()