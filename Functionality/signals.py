from dataclasses import dataclass


@dataclass
class Signal:
    """
    indices: sample indices n
    values: corresponding sample values x[n]
    """

    indices: list[int]
    values: list[float]

    def __post_init__(self):
        if len(self.indices) != len(self.values):
            raise ValueError("Indices and values must have the same length.")

        if len(set(self.indices)) != len(self.indices):
            raise ValueError("Signal indices must be unique.")

    def __len__(self):
        return len(self.indices)

    def __eq__(self, other):
        if not isinstance(other, Signal):
            return False

        return (
            self.indices == other.indices
            and self.values == other.values
        )