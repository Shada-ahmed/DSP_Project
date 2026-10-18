
from pathlib import Path

from Functionality.signals import Signal
from Functionality.quantization import quantize_signal

from Tests.QuanTest1 import QuantizationTest1
from Tests.QuanTest2 import QuantizationTest2


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "quantization"


def load_quantization_input(file_path):
    """Read the doctor's input format: 3 header lines, then index/value."""

    indices = []
    values = []

    with open(file_path, "r") as file:
        for _ in range(3):
            next(file, None)

        for line in file:
            parts = line.split()

            if len(parts) < 2:
                continue

            indices.append(int(parts[0]))
            values.append(float(parts[1]))

    return Signal(indices, values)


def run_test_1():
    signal = load_quantization_input(DATA / "Quan1_input.txt")

    result = quantize_signal(signal, bits=3)

    print("\n--- Doctor Test 1 ---")

    QuantizationTest1(
        str(DATA / "Quan1_Out.txt"),
        result.encoded_signal,
        result.quantized_signal.values,
    )


def run_test_2():
    signal = load_quantization_input(DATA / "Quan2_input.txt")

    result = quantize_signal(signal, bits=2)

    print("\n--- Doctor Test 2 ---")

    QuantizationTest2(
        str(DATA / "Quan2_Out.txt"),
        result.interval_indices,
        result.encoded_signal,
        result.quantized_signal.values,
        result.error_signal.values,
    )


if __name__ == "__main__":
    run_test_1()
    run_test_2()
