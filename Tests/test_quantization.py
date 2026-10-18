
import pytest

from Functionality.signals import Signal
from Functionality.quantization import quantize_signal


def test_quantize_using_bits():
    signal = Signal(
        indices=[0, 1, 2, 3],
        values=[-1.0, -0.2, 0.3, 1.0],
    )

    result = quantize_signal(signal, bits=2)

    assert result.levels == 4
    assert result.bits_per_sample == 2

    assert result.interval_indices == [1, 2, 3, 4]
    assert result.encoded_signal == ["00", "01", "10", "11"]

    assert result.quantized_signal.values == pytest.approx(
        [-0.75, -0.25, 0.25, 0.75]
    )

    assert result.error_signal.values == pytest.approx(
        [0.25, -0.05, -0.05, -0.25]
    )


def test_quantize_using_levels():
    signal = Signal(
        indices=[0, 1],
        values=[0.0, 1.0],
    )

    result = quantize_signal(signal, levels=4)

    assert result.levels == 4
    assert result.bits_per_sample == 2
    assert result.encoded_signal == ["00", "11"]


def test_preserve_sample_indices():
    signal = Signal(
        indices=[-2, 0, 3],
        values=[1.0, 2.0, 3.0],
    )

    result = quantize_signal(signal, levels=4)

    assert result.quantized_signal.indices == [-2, 0, 3]
    assert result.error_signal.indices == [-2, 0, 3]


def test_invalid_options():
    signal = Signal(indices=[0], values=[1.0])

    with pytest.raises(ValueError):
        quantize_signal(signal)

    with pytest.raises(ValueError):
        quantize_signal(signal, levels=4, bits=2)

    with pytest.raises(ValueError):
        quantize_signal(signal, bits=0)

    with pytest.raises(ValueError):
        quantize_signal(signal, levels=1)


def test_empty_signal():
    signal = Signal(indices=[], values=[])

    with pytest.raises(ValueError):
        quantize_signal(signal, bits=2)


def test_constant_signal():
    signal = Signal(
        indices=[0, 1, 2],
        values=[5.0, 5.0, 5.0],
    )

    result = quantize_signal(signal, bits=2)

    assert result.quantized_signal.values == [5.0, 5.0, 5.0]
    assert result.error_signal.values == [0.0, 0.0, 0.0]
    assert result.encoded_signal == ["00", "00", "00"]
