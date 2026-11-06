import numpy as np
import pytest
from arena import Arena
from motion import interpolate, load_clip


@pytest.fixture
def arena():
    return Arena()


def test_shortest_path_interpolation(arena):
    a = arena.reset()
    b = a.copy()
    b[3:7] *= -1
    b[39:43] *= -1
    b[0] += 2
    b[7] += 0.6
    mid = interpolate(a, b, 0.5)
    np.testing.assert_allclose(mid[3:7], a[3:7])
    np.testing.assert_allclose(mid[39:43], a[39:43])
    assert mid[0] == pytest.approx(a[0] + 1)
    assert mid[7] == pytest.approx(a[7] + 0.3)


def test_csv_validation(tmp_path):
    p = tmp_path / "bad.csv"
    np.savetxt(p, np.ones((2, 35)), delimiter=",")
    with pytest.raises(ValueError, match="36-column"):
        load_clip(p)
    np.savetxt(p, np.zeros((2, 36)), delimiter=",")
    with pytest.raises(ValueError, match="quaternions"):
        load_clip(p)
