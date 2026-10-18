from Functionality import read_signal, fold_signal


def test_fold():

    signal = read_signal("data/Signal1.txt")
    expected = read_signal("data/folding.txt")

    result = fold_signal(signal)

    assert result == expected