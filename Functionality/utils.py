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


def plot_signal(
    signal,
    title="Discrete-Time Signal",
    axes=None,
    clear=True,
    label=None,
):
    """
    Plot a discrete-time signal, optionally on an existing Matplotlib axis.
    """

    owns_figure = axes is None
    if owns_figure:
        _, axes = plt.subplots(figsize=(10, 5))

    if clear:
        axes.clear()

    axes.stem(
        signal.indices,
        signal.values,
        label=label,
    )

    axes.set_title(title)
    axes.set_xlabel("n")
    axes.set_ylabel("x[n]")
    axes.grid(True)

    axes.axhline(0, linewidth=1)
    axes.axvline(0, linewidth=1)

    if label is not None:
        axes.legend()

    if owns_figure:
        axes.figure.tight_layout()
        plt.show()