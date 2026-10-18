from Functionality import read_signal, advance


def test_advance():

    signal = read_signal("data/Signal1.txt")
    expected = read_signal("data/advance3.txt")

    result = advance(signal, 3)

    assert result == expected