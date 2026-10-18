def read_signal(file_path):
    """
    Read a signal from a TXT file.

    Format:
        First line: N
        Next N lines: index value

    Returns:
        Signal object
    """

    from .signals import Signal

    with open(file_path, "r") as file:
        lines = [line.strip() for line in file if line.strip()]

    if not lines:
        raise ValueError("The file is empty.")

    # First line = number of samples
    n = int(lines[0])

    if len(lines) - 1 != n:
        raise ValueError(
            f"Expected {n} samples, but found {len(lines) - 1}."
        )

    indices = []
    values = []

    for line in lines[1:]:
        parts = line.split()

        if len(parts) != 2:
            raise ValueError(
                f"Invalid sample format: '{line}'"
            )

        index = int(parts[0])
        value = float(parts[1])

        indices.append(index)
        values.append(value)

    return Signal(indices, values)

import matplotlib.pyplot as plt


def plot_signal(signal, title="Discrete-Time Signal"):
    """
    Display a discrete-time signal using a stem plot.
    """

    plt.figure(figsize=(10, 5))

    plt.stem(
        signal.indices,
        signal.values
    )

    plt.title(title)
    plt.xlabel("n")
    plt.ylabel("x[n]")
    plt.grid(True)

    plt.axhline(0, linewidth=1)
    plt.axvline(0, linewidth=1)

    plt.show()