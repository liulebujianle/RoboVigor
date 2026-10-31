"""Geometry and rolling direction checks independent of the renderer."""

import math
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sentry_wheels import rolling_rate


def test_radial_omni_axle_handedness():
    """Forward, lateral and spin must produce distinct physical wheel rates."""
    s, a, radius = math.sqrt(0.5), 0.167317, 0.0763
    axes = [(s, -s, 0), (-s, -s, 0), (-s, s, 0), (s, s, 0)]
    centers = [(-a, a, 0), (a, a, 0), (a, -a, 0), (-a, -a, 0)]
    forward = [rolling_rate(v, p, radius, (1, 0, 0)) for v, p in zip(axes, centers)]
    lateral = [rolling_rate(v, p, radius, (0, 1, 0)) for v, p in zip(axes, centers)]
    spin = [rolling_rate(v, p, radius, (0, 0, 1)) for v, p in zip(axes, centers)]
    assert np.allclose(forward, np.array([-s, -s, s, s]) / radius)
    assert np.allclose(lateral, np.array([-s, s, s, -s]) / radius)
    assert np.allclose(spin, np.full(4, math.sqrt(2) * a / radius))
