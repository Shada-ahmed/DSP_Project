
from dataclasses import dataclass
import math

import numpy as np


MAX_SIGNAL_SAMPLES = 1_000_000


@dataclass
class Signal:
    """
    Represents a discrete-time signal.

    indices: sample indices n
    values: corresponding sample values x[n]
    """

    indices: list[int]
    values: list[float]

    def __post_init__(self):
        if len(self.indices) != len(self.values):
            raise ValueError(
                "Indices and values must have the same length."
            )

        if len(set(self.indices)) != len(self.indices):
            raise ValueError("Signal indices must be unique.")

        if any(
            isinstance(index, bool) or not isinstance(index, int)
            for index in self.indices
        ):
            raise ValueError("Signal indices must be integers.")

        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float, np.number))
            or not math.isfinite(float(value))
            for value in self.values
        ):
            raise ValueError(
                "Signal values must be finite numeric values."
            )

        # Normalize numeric values to Python floats.
        self.values = [float(value) for value in self.values]

    def __len__(self):
        return len(self.indices)

    def __eq__(self, other):
        if not isinstance(other, Signal):
            return False

        return (
            self.indices == other.indices
            and self.values == other.values
        )


def generate_signal(
    wave_type,
    amplitude,
    frequency,
    phase_degrees,
    sampling_frequency,
    duration,
    representation="discrete",
):
    """
    Generate a sine or cosine signal.

    Returns:
        times: sample times
        values: generated amplitudes

    representation:
        'discrete'   - samples at multiples of 1/fs
        'continuous' - densely sampled values for visualization
    """

    try:
        amplitude = float(amplitude)
        frequency = float(frequency)
        phase_degrees = float(phase_degrees)
        sampling_frequency = float(sampling_frequency)
        duration = float(duration)
    except (TypeError, ValueError) as error:
        raise ValueError(
            "All signal parameters must be numeric."
        ) from error

    parameters = (
        amplitude,
        frequency,
        phase_degrees,
        sampling_frequency,
        duration,
    )

    if not all(math.isfinite(value) for value in parameters):
        raise ValueError(
            "Signal parameters must be finite numbers."
        )

    if frequency <= 0:
        raise ValueError("Frequency must be positive.")

    if sampling_frequency <= 0:
        raise ValueError(
            "Sampling frequency must be positive."
        )

    if duration <= 0:
        raise ValueError("Duration must be positive.")

    if sampling_frequency <= 2 * frequency:
        raise ValueError(
            "Sampling frequency must be greater than twice "
            "the signal frequency (fs > 2*f)."
        )

    normalized_wave_type = str(wave_type).strip().lower()

    if normalized_wave_type not in ("sine", "cosine"):
        raise ValueError(
            "Wave type must be 'sine' or 'cosine'."
        )

    normalized_representation = (
        str(representation).strip().lower()
    )

    if normalized_representation == "discrete":
        requested_samples = duration * sampling_frequency

        if (
            not math.isfinite(requested_samples)
            or requested_samples > MAX_SIGNAL_SAMPLES
        ):
            raise ValueError(
                f"Signal would exceed the "
                f"{MAX_SIGNAL_SAMPLES:,}-sample limit."
            )

        sample_count = max(
            1,
            math.ceil(requested_samples),
        )

        sample_indices = np.arange(sample_count)
        times = sample_indices / sampling_frequency

    elif normalized_representation == "continuous":
        requested_points = duration * frequency * 100

        if (
            not math.isfinite(requested_points)
            or requested_points > MAX_SIGNAL_SAMPLES
        ):
            raise ValueError(
                f"Signal would exceed the "
                f"{MAX_SIGNAL_SAMPLES:,}-point limit."
            )

        point_count = max(
            1000,
            math.ceil(requested_points),
        )

        if point_count > MAX_SIGNAL_SAMPLES:
            raise ValueError(
                f"Signal would exceed the "
                f"{MAX_SIGNAL_SAMPLES:,}-point limit."
            )

        times = np.linspace(
            0,
            duration,
            point_count,
            endpoint=False,
        )

    else:
        raise ValueError(
            "Representation must be 'continuous' or 'discrete'."
        )

    phase_radians = np.deg2rad(phase_degrees)

    angle = (
        2 * np.pi * frequency * times
        + phase_radians
    )

    if normalized_wave_type == "sine":
        values = amplitude * np.sin(angle)
    else:
        values = amplitude * np.cos(angle)

    return times, values


def generate_discrete_signal(
    wave_type,
    amplitude,
    frequency,
    phase_degrees,
    sampling_frequency,
    duration,
):
    """
    Generate a discrete-time Signal object compatible with
    add, subtract, multiply, delay, advance, fold and quantization.
    """

    _, values = generate_signal(
        wave_type=wave_type,
        amplitude=amplitude,
        frequency=frequency,
        phase_degrees=phase_degrees,
        sampling_frequency=sampling_frequency,
        duration=duration,
        representation="discrete",
    )

    return Signal(
        indices=list(range(len(values))),
        values=values.tolist(),
    )
