from pathlib import Path

import pytest

from Functionality.signals import Signal


@pytest.fixture
def read_task5_signal():
    def read_signal_file(file_path):
        lines = [
            line.split()
            for line in Path(file_path).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if len(lines) < 3 or any(len(header) != 1 for header in lines[:3]):
            raise ValueError(f"Invalid Task 5 signal file: {file_path}")

        sample_count = int(lines[2][0])
        samples = lines[3:]
        if len(samples) != sample_count:
            raise ValueError(
                f"Expected {sample_count} samples in {file_path}, "
                f"found {len(samples)}."
            )

        indices = []
        values = []
        for sample in samples:
            if len(sample) != 2:
                raise ValueError(
                    f"Invalid sample row in {file_path}: {' '.join(sample)}"
                )
            indices.append(int(sample[0]))
            values.append(float(sample[1]))

        return Signal(indices, values)

    return read_signal_file


@pytest.fixture
def compare_task5_signals():
    def compare(actual, expected):
        assert actual.indices == expected.indices
        assert actual.values == pytest.approx(expected.values, abs=0.01)

    return compare
