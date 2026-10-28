"""Install the ROS package and its complete field resource tree."""

from glob import glob
import os

from setuptools import setup

package_name = 'rm_arena'

setup(

    name=package_name,

    version='0.0.1',

    packages=[package_name],

    data_files=[

        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),

        (
            'share/' + package_name,
            ['package.xml']
        ),

        (
            os.path.join(
                'share',
                package_name,
                'launch'
            ),
            glob('launch/*.launch.py')
        ),

        (
            os.path.join(
                'share',
                package_name,
                'rviz'
            ),
            glob('rviz/*.rviz')
        ),

    ] + [
        (os.path.join('share', package_name, directory),
         [os.path.join(directory, filename) for filename in sorted(filenames)])
        for root in ('models', 'worlds', 'docs')
        for directory, _, filenames in os.walk(root)
        if filenames
    ] + [('share/' + package_name, ['README.md'])],

    install_requires=['setuptools'],

    zip_safe=True,

    maintainer='ethan',

    maintainer_email='ethan@example.com',

    description='RMUL 2027 simulation package',

    license='Apache-2.0',

    tests_require=['pytest'],

    entry_points={

        'console_scripts': [

            'arena_marker = rm_arena.arena_marker:main',

        ],

    },

)
