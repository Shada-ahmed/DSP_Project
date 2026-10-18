from Functionality import read_signal, subtract_signals


def test_subtract():

    signal1 = read_signal("data/Signal1.txt")
    signal2 = read_signal("data/Signal2.txt")

    expected = read_signal("data/subtract.txt")

    result = subtract_signals(signal1, signal2)

    assert result == expected