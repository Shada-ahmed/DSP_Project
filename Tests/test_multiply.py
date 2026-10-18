from Functionality import read_signal, multiply_signal


def test_multiply():

    signal = read_signal("data/Signal1.txt")
    expected = read_signal("data/mul5.txt")

    result = multiply_signal(signal, 5)

    assert result == expected