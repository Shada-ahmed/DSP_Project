from pathlib import Path

from Functionality.signals import Signal
from Functionality.task5 import sharpening


FIXTURE_DIR = Path(__file__).parent


def test_first_derivative_matches_official_output(
    read_task5_signal,
    compare_task5_signals,
):
    source = read_task5_signal(FIXTURE_DIR / "Derivative_input.txt")
    expected = read_task5_signal(FIXTURE_DIR / "1st_derivative_out.txt")

    first, _ = sharpening(source)
    compare_task5_signals(first, expected)


def test_second_derivative_matches_official_output(
    read_task5_signal,
    compare_task5_signals,
):
    source = read_task5_signal(FIXTURE_DIR / "Derivative_input.txt")
    expected = read_task5_signal(FIXTURE_DIR / "2nd_derivative_out.txt")

    _, second = sharpening(source)
    compare_task5_signals(second, expected)


def test_derivatives_preserve_nonzero_sample_indices():
    source = Signal(
        indices=[12, 13, 14, 15],
        values=[1, 3, 6, 10],
    )

    first, second = sharpening(source)

    assert first.indices == [12, 13, 14]
    assert first.values == sharpening(source.values)[0]
    assert second.indices == [12, 13]
    assert second.values == sharpening(source.values)[1]
