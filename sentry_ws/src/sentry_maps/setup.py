"""Install sentry_maps and its resource directories."""
import os
from pathlib import Path
from setuptools import find_packages, setup

PACKAGE = 'sentry_maps'
data_files = [
    ('share/ament_index/resource_index/packages', ['resource/' + PACKAGE]),
    ('share/' + PACKAGE, ['package.xml']),
]
for directory in ('maps',):
    for parent, directories, names in os.walk(directory):
        directories[:] = sorted(
            name for name in directories if name not in ('__pycache__', '.pytest_cache'))
        files = [str(Path(parent) / name) for name in sorted(names)
                 if not name.endswith(('.pyc', '.pyo', '.bak'))]
        if files:
            data_files.append((str(Path('share') / PACKAGE / parent), files))

setup(
    name=PACKAGE,
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    data_files=data_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ethan',
    maintainer_email='ethan@example.com',
    description='Saved mapping assets',
    license='Apache-2.0',
    entry_points={'console_scripts': []},
)
