from Functionality import read_signal, delay


def test_delay():

    signal = read_signal("data/Signal1.txt")
    expected = read_signal("data/delay3.txt")

    result = delay(signal, 3)

    assert result == expected