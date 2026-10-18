from .signals import Signal


def add_signals(*signals):

    result = {}

    for signal in signals:
        for i in range(len(signal.indices)):
            index = signal.indices[i]
            value = signal.values[i]

            if index in result:
                result[index] += value
            else:
                result[index] = value

    result_indices = sorted(result.keys())

    result_values = []
    for index in result_indices:
        result_values.append(result[index])

    return Signal(result_indices, result_values)

def multiply_signal(signal, constant):
    """Multiply every sample of a signal by a constant"""

    new_values = [value * constant for value in signal.values]
                  

    return Signal( signal.indices.copy(), new_values )

def subtract_signals(signal1, signal2):
    """signal1 + (-1 * signal2) """

    negative_signal = multiply_signal(signal2, -1)

    return add_signals(signal1, negative_signal )

def delay(signal, k):

    result_indices = []

    for index in signal.indices:
        result_indices.append(index + k)

    result_values = []

    for value in signal.values:
        result_values.append(value)

    return Signal(result_indices, result_values)

def advance(signal, k):
   

    new_indices = [  index - k for index in signal.indices]

    return Signal(new_indices, signal.values.copy())

def fold_signal(signal):

    result_indices = []

    for index in signal.indices:
        result_indices.append(-index)

    result_values = []

    for value in signal.values:
        result_values.append(value)

    pairs = []

    for i in range(len(result_indices)):
        pairs.append((result_indices[i], result_values[i]))

    pairs.sort()

    sorted_indices = []
    sorted_values = []

    for pair in pairs:
        sorted_indices.append(pair[0])
        sorted_values.append(pair[1])

    return Signal(sorted_indices, sorted_values)
    