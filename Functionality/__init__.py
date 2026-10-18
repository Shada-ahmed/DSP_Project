from .signals import (
    Signal,
    generate_signal,
    generate_discrete_signal,
)

from .operations import (
    add_signals,
    multiply_signal,
    subtract_signals,
    delay,
    advance,
    fold_signal
)

from .utils import (
    read_signal,
    plot_signal
)