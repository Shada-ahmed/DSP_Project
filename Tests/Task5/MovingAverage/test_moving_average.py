from pathlib import Path

import pytest

from Functionality.signals import Signal
from Functionality.task5 import moving_average


FIXTURE_DIR = Path(__file__).parent


def test_moving_average_window_3(
    read_task5_signal,
    compare_task5_signals,
):
    source = read_task5_signal(FIXTURE_DIR / "MovingAvg_input.txt")
    expected = read_task5_signal(FIXTURE_DIR / "MovingAvg_out1.txt")

    compare_task5_signals(moving_average(source, 3), expected)


def test_moving_average_window_5(
    read_task5_signal,
    compare_task5_signals,
):
    source = read_task5_signal(FIXTURE_DIR / "MovingAvg_input.txt")
    expected = read_task5_signal(FIXTURE_DIR / "MovingAvg_out2.txt")

    compare_task5_signals(moving_average(source, 5), expected)


@pytest.mark.parametrize("window_size", [0, 4])
def test_moving_average_rejects_invalid_window(window_size):
    with pytest.raises(ValueError):
        moving_average([1, 2, 3], window_size)


def test_moving_average_preserves_nonzero_start_index():
    source = Signal(
        indices=[7, 8, 9, 10],
        values=[1, 2, 3, 4],
    )

    result = moving_average(source, 2)

    assert result.indices == [7, 8, 9]
    assert result.values == pytest.approx(moving_average(source.values, 2))
