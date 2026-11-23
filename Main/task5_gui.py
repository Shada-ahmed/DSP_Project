from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from Functionality import (
    convolution,
    moving_average,
    plot_signal,
    read_signal,
    sharpening,
)


class SignalPlotCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.figure = Figure(figsize=(4.5, 3.2), dpi=100)
        self.axes = self.figure.add_subplot(111)
        super().__init__(self.figure)
        self.setParent(parent)
        self.setMinimumHeight(260)

    def plot_signals(self, signals, title):
        self.axes.clear()
        self.axes.set_title(title)
        self.axes.set_xlabel("n")
        self.axes.set_ylabel("x[n]")
        self.axes.grid(True, alpha=0.3)
        self.axes.axhline(0, linewidth=1)
        self.axes.axvline(0, linewidth=1)

        for label, signal in signals:
            plot_signal(
                signal,
                title,
                axes=self.axes,
                clear=False,
                label=label,
            )

        if not signals:
            self.axes.set_title(title)

        self.figure.tight_layout()
        self.draw()


class Task5Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DSP Project - Task 5")
        self.resize(1250, 850)

        self.first_signal = None
        self.second_signal = None
        self.first_signal_name = "Input 1"
        self.second_signal_name = "Input 2"

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        input_group = QGroupBox("Input Signals")
        input_layout = QFormLayout(input_group)

        first_row = QHBoxLayout()
        self.first_name_label = QLabel("No signal selected")
        first_button = QPushButton("Load Input 1")
        first_button.clicked.connect(
            lambda: self._load_signal(1)
        )
        first_row.addWidget(self.first_name_label, 1)
        first_row.addWidget(first_button)
        input_layout.addRow("Signal 1:", first_row)

        second_row = QHBoxLayout()
        self.second_name_label = QLabel("No signal selected")
        second_button = QPushButton("Load Input 2")
        second_button.clicked.connect(
            lambda: self._load_signal(2)
        )
        second_row.addWidget(self.second_name_label, 1)
        second_row.addWidget(second_button)
        input_layout.addRow("Signal 2:", second_row)
        layout.addWidget(input_group)

        operation_group = QGroupBox("Task 5 Operation")
        operation_layout = QHBoxLayout(operation_group)
        self.operation_combo = QComboBox()
        self.operation_combo.addItems([
            "Moving Average",
            "First and Second Derivatives",
            "Convolution",
        ])
        self.operation_combo.currentTextChanged.connect(
            self._operation_changed
        )
        operation_layout.addWidget(QLabel("Operation:"))
        operation_layout.addWidget(self.operation_combo)

        self.window_size_label = QLabel("Window size:")
        operation_layout.addWidget(self.window_size_label)
        self.window_size_spin = QSpinBox()
        self.window_size_spin.setRange(1, 1_000_000)
        self.window_size_spin.setValue(3)
        operation_layout.addWidget(self.window_size_spin)

        self.run_button = QPushButton("Run Operation")
        self.run_button.clicked.connect(self._run_operation)
        operation_layout.addWidget(self.run_button)
        layout.addWidget(operation_group)

        plots_layout = QHBoxLayout()
        self.first_canvas = SignalPlotCanvas()
        self.second_canvas = SignalPlotCanvas()
        self.output_canvas = SignalPlotCanvas()
        self.first_canvas.plot_signals([], "Input 1")
        self.second_canvas.plot_signals([], "Input 2")
        self.output_canvas.plot_signals([], "Output")
        plots_layout.addWidget(self.first_canvas)
        plots_layout.addWidget(self.second_canvas)
        plots_layout.addWidget(self.output_canvas)
        layout.addLayout(plots_layout, 2)

        result_group = QGroupBox("Output Samples")
        result_layout = QVBoxLayout(result_group)
        self.result_summary = QLabel(
            "Load the required signal(s), then run an operation."
        )
        result_layout.addWidget(self.result_summary)
        self.result_table = QTableWidget(0, 3)
        self.result_table.setHorizontalHeaderLabels([
            "Sample Index",
            "Output",
            "Value",
        ])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        result_layout.addWidget(self.result_table)
        layout.addWidget(result_group, 1)

        self._operation_changed(self.operation_combo.currentText())

    def _load_signal(self, signal_number):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Load Input {signal_number}",
            str(Path.cwd() / "data"),
            "Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return

        try:
            signal = read_signal(file_path)
        except (OSError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Could Not Load Signal",
                str(error),
            )
            return

        name = Path(file_path).name
        if signal_number == 1:
            self.first_signal = signal
            self.first_signal_name = name
            self.first_name_label.setText(name)
            self.first_canvas.plot_signals(
                [("Input 1", signal)],
                f"Input 1: {name}",
            )
        else:
            self.second_signal = signal
            self.second_signal_name = name
            self.second_name_label.setText(name)
            self.second_canvas.plot_signals(
                [("Input 2", signal)],
                f"Input 2: {name}",
            )

        self._clear_results()

    def _operation_changed(self, operation):
        is_moving_average = operation == "Moving Average"
        self.window_size_label.setVisible(is_moving_average)
        self.window_size_spin.setVisible(is_moving_average)

    def _run_operation(self):
        if self.first_signal is None:
            QMessageBox.warning(
                self,
                "Input Required",
                "Load Input 1 before running an operation.",
            )
            return

        operation = self.operation_combo.currentText()
        try:
            if operation == "Moving Average":
                window_size = self.window_size_spin.value()
                if window_size > len(self.first_signal):
                    QMessageBox.warning(
                        self,
                        "Invalid Window Size",
                        "Window size must not exceed the number of input samples.",
                    )
                    return
                output = moving_average(self.first_signal, window_size)
                result_signals = [("Moving average", output)]

            elif operation == "First and Second Derivatives":
                if len(self.first_signal) < 3:
                    QMessageBox.warning(
                        self,
                        "Insufficient Samples",
                        "Load at least three samples to calculate both derivatives.",
                    )
                    return
                first, second = sharpening(self.first_signal)
                result_signals = [
                    ("First derivative", first),
                    ("Second derivative", second),
                ]

            else:
                if self.second_signal is None:
                    QMessageBox.warning(
                        self,
                        "Input Required",
                        "Load Input 2 before calculating convolution.",
                    )
                    return
                output = convolution(self.first_signal, self.second_signal)
                result_signals = [("Convolution", output)]
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Operation Failed",
                str(error),
            )
            return

        self._display_results(result_signals)

    def _display_results(self, result_signals):
        rows = [
            (label, index, value)
            for label, signal in result_signals
            for index, value in zip(signal.indices, signal.values)
        ]
        self.result_table.setRowCount(len(rows))

        for row, (label, index, value) in enumerate(rows):
            self.result_table.setItem(
                row, 0, QTableWidgetItem(str(index))
            )
            self.result_table.setItem(
                row, 1, QTableWidgetItem(label)
            )
            self.result_table.setItem(
                row, 2, QTableWidgetItem(f"{value:.10g}")
            )

        self.result_summary.setText(
            f"{len(rows)} output samples across "
            f"{len(result_signals)} result signal(s)."
        )
        self.output_canvas.plot_signals(
            result_signals,
            self.operation_combo.currentText(),
        )

    def _clear_results(self):
        self.result_table.setRowCount(0)
        self.result_summary.setText(
            "Load the required signal(s), then run an operation."
        )
        self.output_canvas.plot_signals([], "Output")
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = Task5Window()
    window.show()
    sys.exit(app.exec())