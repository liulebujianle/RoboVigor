"""Regression for the native assembly's non-contiguous directory records."""

from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'vendor'))
from sldprt.assembly import read_directory


def test_non_contiguous_component_numbers():
    """Do not silently lose every component after the first sequence gap."""
    def string(value):
        return b'\xff\xfe\xff' + bytes([len(value)]) + value.encode('utf-16-le')

    data = struct.pack('<III', 2, 96, 3)
    for number, name in [(2, 'a-1@root'), (4, 'b-1@root'), (6, 'c-1@root')]:
        data += struct.pack('<I', number) + string(name)
        data += struct.pack('<III', 0, 0, 0) + bytes(16)
        data += string('cache') + struct.pack('<I', number)
    assert [entry.name for entry in read_directory(data)] == [
        'a-1@root', 'b-1@root', 'c-1@root',
    ]
