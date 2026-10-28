"""Check that the installed field has no missing local resource references."""

from distutils.core import run_setup
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import pytest
import yaml


@pytest.fixture
def installed_share(tmp_path, monkeypatch):
    """Stage the actual setuptools data payload outside the source tree."""
    source = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(source)
    distribution = run_setup('setup.py', stop_after='config')
    for destination, files in distribution.data_files:
        target = tmp_path / destination
        target.mkdir(parents=True, exist_ok=True)
        for filename in files:
            shutil.copy2(filename, target / Path(filename).name)
    return tmp_path / 'share' / 'rm_arena'


def test_field_resources_are_self_contained(installed_share):
    """Catch omitted worlds, meshes or textures in the install payload."""
    world = installed_share / 'worlds' / 'arena.world'
    assert world.is_file(), 'Installed package is missing the field world'
    models = installed_share / 'models'
    documents = [world, *models.rglob('*.sdf')]
    for document in documents:
        for element in ET.parse(document).iter('uri'):
            uri = element.text
            assert uri.startswith('model://'), uri
            assert (models / uri.removeprefix('model://')).exists(), uri
    for mesh in models.rglob('*.dae'):
        namespace = {'c': 'http://www.collada.org/2005/11/COLLADASchema'}
        images = ET.parse(mesh).findall('.//c:image/c:init_from', namespace)
        for image in images:
            assert (mesh.parent / image.text).is_file(), image.text
    config = models / 'rmul_2027' / 'model.config'
    assert config.is_file()
    for sdf in ET.parse(config).iter('sdf'):
        assert (config.parent / sdf.text).is_file()


def test_package_versions_match(monkeypatch):
    """Keep ROS and Python package metadata consistent."""
    source = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(source)
    distribution = run_setup('setup.py', stop_after='config')
    assert distribution.get_version() == ET.parse('package.xml').findtext('version')


def test_rviz_grid_covers_field(installed_share):
    """Keep the complete field, including its perimeter, inside the grid."""
    config = yaml.safe_load((installed_share / 'rviz' / 'arena.rviz').read_text())
    displays = config['Visualization Manager']['Displays']
    grid = next(d for d in displays if d['Class'] == 'rviz_default_plugins/Grid')
    half_width = grid['Cell Size'] * grid['Plane Cell Count'] / 2
    for axis, minimum, maximum in [('X', -0.3, 12.3), ('Y', -0.3, 8.3)]:
        assert grid['Offset'][axis] - half_width <= minimum
        assert grid['Offset'][axis] + half_width >= maximum
