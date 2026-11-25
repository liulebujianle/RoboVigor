"""安装模型发布节点和机器人资源。"""

import os

from setuptools import find_packages, setup

PACKAGE = 'sentry_description'
SHARE = os.path.join('share', PACKAGE)


def resource_files():
    """按原目录安装资源，跳过缓存和备份文件。"""
    for root in ('launch', 'rviz', 'urdf', 'meshes', 'config'):
        for directory, dirs, names in os.walk(root):
            dirs[:] = sorted(d for d in dirs if d not in ('__pycache__', '.pytest_cache'))
            files = [os.path.join(directory, name) for name in sorted(names)
                     if not name.endswith(('.pyc', '.pyo', '.bak'))]
            if files:
                yield os.path.join(SHARE, directory), files


setup(
    name=PACKAGE,
    version='0.1.0',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + PACKAGE]),
        (SHARE, ['package.xml', 'README.md', 'LICENSE']),
    ] + list(resource_files()),
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ethan',
    maintainer_email='ethan@example.com',
    description='Robot model resources and retained physics description publisher',
    license='Apache-2.0',
    entry_points={'console_scripts': [
        'sentry_description_publisher = '
        'sentry_description.sentry_description_publisher:main',
        'sentry_pitch_preview = sentry_description.sentry_pitch_preview:main',
    ]},
)
