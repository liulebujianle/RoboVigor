"""安装场地工具和模型资源。"""

import os

from setuptools import find_packages, setup

PACKAGE = 'sentry_map'
SHARE = os.path.join('share', PACKAGE)


def resource_files():
    """按原目录安装资源，跳过缓存和备份文件。"""
    for root in ('launch', 'rviz', 'models', 'scenes', 'docs'):
        for directory, dirs, names in os.walk(root):
            dirs[:] = sorted(d for d in dirs if d not in ('__pycache__', '.pytest_cache'))
            files = [os.path.join(directory, name) for name in sorted(names)
                     if not name.endswith(('.pyc', '.pyo', '.bak'))]
            if files:
                yield os.path.join(SHARE, directory), files


setup(
    name=PACKAGE,
    version='0.0.1',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + PACKAGE]),
        (SHARE, ['package.xml', 'README.md']),
    ] + list(resource_files()),
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ethan',
    maintainer_email='hhhrrrppp123654@gmail.com',
    description='Fixed RMUL field resources, preview and explicit conversion tools',
    license='Apache-2.0',
    entry_points={'console_scripts': [
        'sentry_arena_marker = sentry_map.sentry_arena_marker:main',
        'sentry_stl_to_field = sentry_map.sentry_stl_to_field:main',
        'sentry_step_to_field = sentry_map.sentry_step_to_field:main',
        'sentry_restore_github_field = sentry_map.sentry_restore_github_field:main',
    ]},
)
