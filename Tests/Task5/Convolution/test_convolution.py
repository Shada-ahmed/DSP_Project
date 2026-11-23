from pathlib import Path

from Functionality.signals import Signal
from Functionality.task5 import convolution


FIXTURE_DIR = Path(__file__).parent


def test_convolution_matches_official_output(
    read_task5_signal,
    compare_task5_signals,
):
    first = read_task5_signal(FIXTURE_DIR / "Signal 1.txt")
    second = read_task5_signal(FIXTURE_DIR / "Signal 2.txt")
    expected = read_task5_signal(FIXTURE_DIR / "Conv_output.txt")

    compare_task5_signals(convolution(first, second), expected)


def test_convolution_preserves_summed_nonzero_start_indices():
    first = Signal(indices=[4, 5], values=[1, 2])
    second = Signal(indices=[-2, -1], values=[3, 4])

    result = convolution(first, second)

    assert result.indices == [2, 3, 4]
    assert result.values == convolution(first.values, second.values)
