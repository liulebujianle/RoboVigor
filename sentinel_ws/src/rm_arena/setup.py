"""安装 rm_arena 包及其完整场地资源树。"""

from glob import glob
import os

from setuptools import setup

PACKAGE = 'rm_arena'
SHARE = os.path.join('share', PACKAGE)

setup(
    name=PACKAGE,
    version='0.0.1',
    packages=[PACKAGE],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + PACKAGE]),
        (SHARE, ['package.xml', 'README.md']),
        (os.path.join(SHARE, 'launch'), glob('launch/*.launch.py')),
        (os.path.join(SHARE, 'rviz'), glob('rviz/*.rviz')),
    ] + [
        # models / worlds / docs 整棵树原样安装，保留子目录结构
        (os.path.join(SHARE, directory),
         [os.path.join(directory, name) for name in sorted(names)])
        for root in ('models', 'worlds', 'docs')
        for directory, _, names in os.walk(root)
        if names
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ethan',
    maintainer_email='ethan@example.com',
    description='RMUL 2027 simulation package',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={'console_scripts': ['arena_marker = rm_arena.arena_marker:main']},
)
