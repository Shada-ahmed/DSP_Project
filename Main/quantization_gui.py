
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QHeaderView,
    QSplitter,
    QScrollArea,
    QFrame,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from Functionality.signals import Signal
from Functionality.quantization import quantize_signal


class SignalCanvas(FigureCanvasQTAgg):
    """Matplotlib canvas embedded in the PySide6 application."""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(4.4, 3.0), dpi=100)
        self.axes = self.figure.add_subplot(111)

        super().__init__(self.figure)
        self.setParent(parent)
        self.setMinimumHeight(285)
        self.setMinimumWidth(350)

        # Leave space above the axes so titles are never clipped.
        self.figure.subplots_adjust(
            left=0.22, right=0.98, bottom=0.24, top=0.80
        )
        self.axes.tick_params(axis="both", labelsize=8)

    def clear_plot(self, title, y_label):
        self.axes.clear()
        self.axes.set_title(title, fontsize=10, fontweight="bold", pad=10)
        self.axes.set_xlabel("Sample index n", fontsize=8, labelpad=4)
        self.axes.set_ylabel(y_label, fontsize=8, labelpad=5)
        self.axes.tick_params(axis="both", labelsize=8)
        self.axes.grid(True, alpha=0.28, linestyle="--")

    def plot_signal(self, signal, title, y_label="Amplitude"):
        self.clear_plot(title, y_label)

        if len(signal) > 0:
            self.axes.stem(
                signal.indices,
                signal.values,
                linefmt="C0-",
                markerfmt="C0o",
                basefmt="k-",
            )

        self.figure.subplots_adjust(
            left=0.22, right=0.98, bottom=0.24, top=0.80
        )
        self.draw()

    def plot_comparison(self, original, quantized):
        self.clear_plot("Original vs Quantized Signal", "Amplitude")

        self.axes.plot(
            original.indices,
            original.values,
            "o-",
            label="Original",
        )

        self.axes.step(
            quantized.indices,
            quantized.values,
            where="mid",
            label="Quantized",
        )

        self.axes.legend()
        self.figure.subplots_adjust(
            left=0.22, right=0.98, bottom=0.24, top=0.80
        )
        self.draw()

    def plot_discrete_quantization(self, original, quantized):
        """Show original samples and their quantized values together."""
        self.clear_plot(
            "Discrete Input + Quantized Signal",
            "Amplitude",
        )

        if len(original) > 0:
            # Original input: blue stems and circular sample markers.
            self.axes.stem(
                original.indices,
                original.values,
                linefmt="C0-",
                markerfmt="C0o",
                basefmt="k-",
                label="Original input",
            )

            # Quantized output: orange square markers and a staircase.
            self.axes.step(
                quantized.indices,
                quantized.values,
                where="mid",
                color="C1",
                linestyle="--",
                linewidth=1.5,
                label="Quantized",
            )
            self.axes.plot(
                quantized.indices,
                quantized.values,
                linestyle="None",
                marker="s",
                markersize=5,
                color="C1",
                label="_nolegend_",
            )

        self.axes.legend(fontsize=8, loc="best")
        self.figure.subplots_adjust(
            left=0.22, right=0.98, bottom=0.24, top=0.80
        )
        self.draw()


class QuantizationWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DSP Project - Signal Quantization")
        self.resize(1320, 740)
        self.setMinimumSize(1050, 620)
        self.setStyleSheet("""
            QWidget {
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 10pt;
            }
            QMainWindow {
                background-color: #f5f7fb;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                margin-top: 12px;
                padding: 10px 8px 8px 8px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #243b53;
            }
            QLabel {
                color: #243b53;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
            QComboBox, QSpinBox {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 5px;
                min-height: 24px;
            }
            QScrollArea {
                background-color: #f5f7fb;
            }
            QScrollBar:vertical {
                background: #eef2f7;
                width: 13px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #aab8ca;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #8295ad;
            }
            QTableWidget {
                background-color: white;
                alternate-background-color: #f1f5f9;
                gridline-color: #d7dee8;
                border: 1px solid #cbd5e1;
                font-size: 9pt;
            }
            QHeaderView::section {
                background-color: #e8eef7;
                color: #243b53;
                padding: 7px;
                border: none;
                border-bottom: 1px solid #cbd5e1;
                font-weight: bold;
            }
        """)

        # Signal name -> Signal object
        self.signals = {}

        self.current_result = None
        self.current_signal = None

        self.build_ui()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        outer_layout.addWidget(scroll_area)

        content = QWidget()
        scroll_area.setWidget(content)

        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(12, 10, 12, 12)
        main_layout.setSpacing(9)

        title = QLabel("DSP Signal Quantization")
        title.setStyleSheet(
            "font-size: 24px; font-weight: 700; color: #102a43; padding: 8px;"
        )
        main_layout.addWidget(title)

        # --------------------------------------------------
        # 1. Input signal section
        # --------------------------------------------------

        input_group = QGroupBox("Input Signal")
        input_layout = QHBoxLayout(input_group)

        self.signal_combo = QComboBox()
        self.signal_combo.setMinimumWidth(300)
        self.signal_combo.currentTextChanged.connect(
            self.on_signal_selected
        )

        self.load_button = QPushButton("Load Signal File")
        self.load_button.clicked.connect(self.load_signal_file)

        input_layout.addWidget(QLabel("Select signal:"))
        input_layout.addWidget(self.signal_combo, 1)
        input_layout.addWidget(self.load_button)

        main_layout.addWidget(input_group)

        # --------------------------------------------------
        # 2. Quantization configuration
        # --------------------------------------------------

        config_group = QGroupBox("Quantization Settings")
        config_layout = QGridLayout(config_group)

        config_layout.addWidget(
            QLabel("Input method:"), 0, 0
        )

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(
            ["Number of bits", "Number of levels"]
        )
        self.mode_combo.currentTextChanged.connect(
            self.update_level_preview
        )

        config_layout.addWidget(self.mode_combo, 0, 1)

        config_layout.addWidget(
            QLabel("Value:"), 0, 2
        )

        self.value_spin = QSpinBox()
        self.value_spin.setRange(1, 16)
        self.value_spin.setValue(3)
        self.value_spin.valueChanged.connect(
            self.update_level_preview
        )

        config_layout.addWidget(self.value_spin, 0, 3)

        self.levels_label = QLabel()
        self.levels_label.setStyleSheet(
            "font-weight: bold; padding: 5px;"
        )

        config_layout.addWidget(
            self.levels_label, 0, 4
        )

        self.quantize_button = QPushButton("Quantize Signal")
        self.quantize_button.setMinimumHeight(36)
        self.quantize_button.clicked.connect(
            self.run_quantization
        )

        config_layout.addWidget(
            self.quantize_button, 0, 5
        )

        main_layout.addWidget(config_group)

        # --------------------------------------------------
        # 3. Plots
        # --------------------------------------------------

        # Three charts in one row. The scroll area keeps the charts and
        # result tables accessible on laptop screens without clipping.
        plots_widget = QWidget()
        plots_layout = QHBoxLayout(plots_widget)
        plots_layout.setContentsMargins(0, 0, 0, 0)
        plots_layout.setSpacing(8)
        plots_widget.setMinimumHeight(300)

        self.discrete_canvas = SignalCanvas()
        self.discrete_canvas.clear_plot(
            "Discrete Input Signal",
            "Amplitude",
        )

        self.comparison_canvas = SignalCanvas()
        self.comparison_canvas.clear_plot(
            "Original vs Quantized",
            "Amplitude",
        )

        self.error_canvas = SignalCanvas()
        self.error_canvas.clear_plot(
            "Quantization Error",
            "Quantized - Original",
        )

        plots_layout.addWidget(self.discrete_canvas, 1)
        plots_layout.addWidget(self.comparison_canvas, 1)
        plots_layout.addWidget(self.error_canvas, 1)

        main_layout.addWidget(plots_widget, 3)

        # --------------------------------------------------
        # 4. Results table
        # --------------------------------------------------

        result_group = QGroupBox("Quantization Results")
        result_layout = QVBoxLayout(result_group)

        self.summary_label = QLabel(
            "Load a signal and click Quantize Signal."
        )
        result_layout.addWidget(self.summary_label)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.verticalHeader().setDefaultSectionSize(30)
        self.results_table.setHorizontalHeaderLabels(
            [
                "Sample Index",
                "Original Value",
                "Interval Index",
                "Quantized Value",
                "Quantization Error",
            ]
        )

        self.results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.results_table.setMinimumHeight(145)
        self.results_table.setMaximumHeight(220)
        result_layout.addWidget(self.results_table)

        # Encoded values are displayed separately so the binary
        # strings retain leading zeros.
        self.encoded_table = QTableWidget()
        self.encoded_table.setColumnCount(2)
        self.encoded_table.setAlternatingRowColors(True)
        self.encoded_table.verticalHeader().setDefaultSectionSize(30)
        self.encoded_table.setHorizontalHeaderLabels(
            ["Sample Index", "Encoded Binary Value"]
        )

        self.encoded_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        result_layout.addWidget(QLabel("Encoded Signal"))
        self.encoded_table.setMinimumHeight(115)
        self.encoded_table.setMaximumHeight(190)
        result_layout.addWidget(self.encoded_table)

        main_layout.addWidget(result_group, 3)

        self.update_level_preview()

    # ------------------------------------------------------
    # Load signal files
    # ------------------------------------------------------

    def load_signal_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Signal File",
            "",
            "Text Files (*.txt);;All Files (*)",
        )

        if not file_path:
            return

        try:
            signal = self.read_signal_file(file_path)

            name = Path(file_path).name
            display_name = name

            # Avoid replacing another signal with the same filename.
            counter = 2
            while display_name in self.signals:
                display_name = f"{name} ({counter})"
                counter += 1

            self.signals[display_name] = signal
            self.signal_combo.addItem(display_name)
            self.signal_combo.setCurrentText(display_name)

            QMessageBox.information(
                self,
                "Signal Loaded",
                f"Loaded {len(signal)} samples from:\n{name}",
            )

        except (OSError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Could Not Load Signal",
                str(error),
            )

    @staticmethod
    def read_signal_file(file_path):
        """
        Read lines containing:
            sample_index sample_value

        Single-value header lines are ignored. This supports
        the assignment's N/index/value format and the supplied
        doctor input files with three single-value header lines.
        """

        indices = []
        values = []

        with open(file_path, "r", encoding="utf-8-sig") as file:
            for line_number, line in enumerate(file, start=1):
                parts = line.split()

                if not parts:
                    continue

                # Only rows with exactly two fields are sample rows.
                if len(parts) != 2:
                    continue

                try:
                    index = int(parts[0])
                    value = float(parts[1])
                except ValueError:
                    # Ignore non-numeric header rows.
                    continue

                indices.append(index)
                values.append(value)

        if not values:
            raise ValueError(
                "No sample rows were found. Expected rows such as "
                "'0 0.387' (index followed by sample value)."
            )

        return Signal(indices, values)

    # ------------------------------------------------------
    # Signal selection
    # ------------------------------------------------------

    def on_signal_selected(self, name):
        if not name or name not in self.signals:
            self.current_signal = None
            return

        self.current_signal = self.signals[name]

        # Show the discrete-time input as soon as a signal is selected.
        self.discrete_canvas.plot_signal(
            self.current_signal,
            "Discrete Input Signal",
            "Amplitude",
        )

        # Reset the comparison and error plots until quantization runs.
        self.comparison_canvas.clear_plot(
            "Original vs Quantized Signal",
            "Amplitude",
        )
        self.comparison_canvas.draw()

        self.error_canvas.clear_plot(
            "Quantization Error",
            "Error",
        )
        self.error_canvas.draw()

        self.current_result = None
        self.results_table.setRowCount(0)
        self.encoded_table.setRowCount(0)

        self.summary_label.setText(
            f"Loaded {len(self.current_signal)} samples. "
            "Click Quantize Signal to calculate the results."
        )

    # ------------------------------------------------------
    # Quantization settings
    # ------------------------------------------------------

    def update_level_preview(self, *_):
        value = self.value_spin.value()

        if self.mode_combo.currentText() == "Number of bits":
            levels = 2 ** value
            self.levels_label.setText(
                f"Number of levels: {levels}"
            )
        else:
            levels = value
            self.levels_label.setText(
                f"Number of levels: {levels}"
            )

    # ------------------------------------------------------
    # Run quantization
    # ------------------------------------------------------

    def run_quantization(self):
        if self.current_signal is None:
            QMessageBox.warning(
                self,
                "No Signal Selected",
                "Please load and select a signal first.",
            )
            return

        value = self.value_spin.value()

        try:
            if self.mode_combo.currentText() == "Number of bits":
                result = quantize_signal(
                    self.current_signal,
                    bits=value,
                )
            else:
                if value < 2:
                    QMessageBox.warning(
                        self,
                        "Invalid Levels",
                        "Please select at least 2 levels.",
                    )
                    return

                result = quantize_signal(
                    self.current_signal,
                    levels=value,
                )

        except (ValueError, TypeError) as error:
            QMessageBox.critical(
                self,
                "Quantization Failed",
                str(error),
            )
            return

        self.current_result = result

        self.display_results()

    # ------------------------------------------------------
    # Display plots and tables
    # ------------------------------------------------------

    def display_results(self):
        signal = self.current_signal
        result = self.current_result

        if signal is None or result is None:
            return

        # Update the discrete plot to show both the original samples
        # and the quantized values after quantization has completed.
        self.discrete_canvas.plot_discrete_quantization(
            signal,
            result.quantized_signal,
        )

        self.comparison_canvas.plot_comparison(
            signal,
            result.quantized_signal,
        )

        self.error_canvas.plot_signal(
            result.error_signal,
            "Quantization Error",
            "Quantized - Original",
        )

        # Results table
        self.results_table.setRowCount(len(signal))

        for row in range(len(signal)):
            values = [
                str(signal.indices[row]),
                f"{signal.values[row]:.6f}",
                str(result.interval_indices[row]),
                f"{result.quantized_signal.values[row]:.6f}",
                f"{result.error_signal.values[row]:.6f}",
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )
                self.results_table.setItem(row, column, item)

        # Binary encoding table
        self.encoded_table.setRowCount(len(signal))

        for row in range(len(signal)):
            index_item = QTableWidgetItem(
                str(signal.indices[row])
            )

            code_item = QTableWidgetItem(
                result.encoded_signal[row]
            )

            index_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            code_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.encoded_table.setItem(row, 0, index_item)
            self.encoded_table.setItem(row, 1, code_item)

        self.summary_label.setText(
            f"Samples: {len(signal)} | "
            f"Levels: {result.levels} | "
            f"Bits per code: {result.bits_per_sample}"
        )


def main():
    app = QApplication(sys.argv)

    window = QuantizationWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
