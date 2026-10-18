
from dataclasses import dataclass
from math import floor, ceil, log2

from .signals import Signal


@dataclass
class QuantizationResult:
    interval_indices: list[int]
    encoded_signal: list[str]
    quantized_signal: Signal
    error_signal: Signal
    levels: int
    bits_per_sample: int


def quantize_signal(
    signal: Signal,
    *,
    levels: int | None = None,
    bits: int | None = None,
) -> QuantizationResult:
    """
    Quantize a signal using either a number of levels or a number of bits.

    Interval indices: 1-based, matching the doctor's Test 2.
    Binary codes: 0-based interval indices, matching both tests.
    Quantization error: quantized value - original value.
    Quantized values: midpoint of each interval.
    """

    # Validate that exactly one option is supplied.
    if (levels is None) == (bits is None):
        raise ValueError("Provide either levels or bits, not both.")

    if bits is not None:
        if isinstance(bits, bool) or not isinstance(bits, int) or bits < 1:
            raise ValueError("Bits must be a positive integer.")

        number_of_levels = 2 ** bits
        bits_per_sample = bits

    else:
        if (
            isinstance(levels, bool)
            or not isinstance(levels, int)
            or levels < 2
        ):
            raise ValueError("Levels must be an integer >= 2.")

        number_of_levels = levels
        bits_per_sample = ceil(log2(number_of_levels))

    if len(signal) == 0:
        raise ValueError("Cannot quantize an empty signal.")

    minimum = min(signal.values)
    maximum = max(signal.values)

    # A constant signal needs special handling because its range is zero.
    if minimum == maximum:
        return QuantizationResult(
            interval_indices=[1] * len(signal),
            encoded_signal=[
                format(0, f"0{bits_per_sample}b")
                for _ in signal.values
            ],
            quantized_signal=Signal(
                signal.indices.copy(),
                signal.values.copy(),
            ),
            error_signal=Signal(
                signal.indices.copy(),
                [0.0] * len(signal),
            ),
            levels=number_of_levels,
            bits_per_sample=bits_per_sample,
        )

    step_size = (maximum - minimum) / number_of_levels

    interval_indices = []
    encoded_values = []
    quantized_values = []
    error_values = []

    for value in signal.values:
        # Zero-based interval index: 0 to number_of_levels - 1.
        interval = floor((value - minimum) / step_size)

        # The maximum value belongs to the final interval.
        interval = min(
            max(interval, 0),
            number_of_levels - 1,
        )

        quantized_value = (
            minimum + (interval + 0.5) * step_size
        )

        # Doctor's expected convention: quantized - original.
        error = quantized_value - value

        # The doctor's Test 2 expects interval numbers starting at 1.
        interval_indices.append(interval + 1)

        # Binary encoding starts at zero, so do not encode interval + 1.
        encoded_values.append(
            format(interval, f"0{bits_per_sample}b")
        )

        quantized_values.append(quantized_value)
        error_values.append(error)

    return QuantizationResult(
        interval_indices=interval_indices,
        encoded_signal=encoded_values,
        quantized_signal=Signal(
            signal.indices.copy(),
            quantized_values,
        ),
        error_signal=Signal(
            signal.indices.copy(),
            error_values,
        ),
        levels=number_of_levels,
        bits_per_sample=bits_per_sample,
    )
