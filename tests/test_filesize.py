import pytest
from plugins.filters import filesize


back_and_forth = [
    (1, "M", 1024 ** 2),
    (1.0, "M", 1024 ** 2),
    (1, "", 1),
    (1, "", 1.0),
    (1.0, "", 1.0),
    (20.0, "K", 20 * 1024),
    (31.0, "G", 31 * 1024 ** 3),
    (31, "G", 31.0 * 1024 ** 3),
    (31, "G", 31 * 1024 ** 3),
    (31.0, "G", 31.0 * 1024 ** 3),
    (0.5, "K", 512),
    (0.5, "K", 512.0)
]


@pytest.mark.parametrize("num, unit, expected", back_and_forth)
def test_to_bytest(num, unit, expected):
    assert filesize.to_bytes(num, unit) == expected


@pytest.mark.parametrize("expected, unit, num", back_and_forth)
def test_to_bytest(num, unit, expected):
    assert filesize.from_bytes(num, unit) == expected
