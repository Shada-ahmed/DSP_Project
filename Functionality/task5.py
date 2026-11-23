from .signals import Signal


def _signal_samples(signal):
    if isinstance(signal, Signal):
        samples = sorted(zip(signal.indices, signal.values))
        return (
            [index for index, _ in samples],
            [value for _, value in samples],
        )

    return None, list(signal)


def moving_average(x, window_size):
    """Calculate a moving average, preserving Signal sample indices."""
    indices, values = _signal_samples(x)

    if window_size <= 0 or window_size > len(values):
        raise ValueError("Invalid window size!")

    averages = [
        sum(values[start:start + window_size]) / window_size
        for start in range(len(values) - window_size + 1)
    ]

    if indices is not None:
        output_indices = indices[:len(averages)]
        return Signal(output_indices, averages)

    return averages


def sharpening(x):
    """Calculate first and second differences of a signal."""
    indices, values = _signal_samples(x)

    first_derivative = [
        values[index] - values[index - 1]
        for index in range(1, len(values))
    ]
    second_derivative = [
        values[index + 1] - 2 * values[index] + values[index - 1]
        for index in range(1, len(values) - 1)
    ]

    if indices is not None:
        first = Signal(indices[:-1], first_derivative)
        second = Signal(indices[:-2], second_derivative)
        return first, second

    return first_derivative, second_derivative


def convolution(x, h):
    """Calculate linear convolution, preserving summed Signal indices."""
    x_indices, x_values = _signal_samples(x)
    h_indices, h_values = _signal_samples(h)

    if not x_values or not h_values:
        return Signal([], []) if x_indices is not None or h_indices is not None else []

    if x_indices is None and h_indices is None:
        result = [0] * (len(x_values) + len(h_values) - 1)
        for x_index, x_value in enumerate(x_values):
            for h_index, h_value in enumerate(h_values):
                result[x_index + h_index] += x_value * h_value
        return result

    if x_indices is None:
        x_indices = list(range(len(x_values)))
    if h_indices is None:
        h_indices = list(range(len(h_values)))

    result_by_index = {}
    for x_index, x_value in zip(x_indices, x_values):
        for h_index, h_value in zip(h_indices, h_values):
            output_index = x_index + h_index
            result_by_index[output_index] = (
                result_by_index.get(output_index, 0) + x_value * h_value
            )

    first_index = min(result_by_index)
    last_index = max(result_by_index)
    output_indices = list(range(first_index, last_index + 1))
    output_values = [
        result_by_index.get(index, 0)
        for index in output_indices
    ]
    return Signal(output_indices, output_values)
