from Functionality import read_signal, add_signals


def test_add():

    signal1 = read_signal("data/Signal1.txt")
    signal2 = read_signal("data/Signal2.txt")

    expected = read_signal("data/add.txt")

    result = add_signals(signal1, signal2)

    assert result == expected