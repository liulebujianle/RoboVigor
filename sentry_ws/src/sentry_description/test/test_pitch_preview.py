"""核对 RViz 独立角度表的标尺、角度读数和参数范围。"""
import math

import pytest

pytest.importorskip('rclpy')
from rclpy.parameter import Parameter
from sentry_description.sentry_pitch_preview import make_gauge, PitchPreview


@pytest.mark.parametrize('angle', [-90.0, -10.0, 0.0, 15.0, 90.0])
def test_needle_and_readout_agree(angle):
    scale, needle, label = make_gauge(angle).markers
    assert scale.points[0].z == scale.points[1].z == 0.0
    tip = needle.points[-1]
    assert math.degrees(math.atan2(tip.z, tip.x)) == pytest.approx(angle)
    assert label.text == f'Pitch {angle:+.1f} deg'
    assert len({m.id for m in (scale, needle, label)}) == 3
    assert all(m.header.frame_id == 'base_link' for m in (scale, needle, label))
    assert PitchPreview.validate([Parameter('angle_deg', value=angle)]).successful


@pytest.mark.parametrize('value', [-91.0, 91.0, float('nan'), float('inf'), 'invalid'])
def test_invalid_angle_is_rejected(value):
    assert not PitchPreview.validate([Parameter('angle_deg', value=value)]).successful
