from glob import glob

from setuptools import find_packages, setup


package_name = 'sentry_motion'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ethan',
    maintainer_email='ethan@example.com',
    description='Simulation keyboard input and final velocity watchdog',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'sentry_keyboard_control = sentry_motion.teleop.sentry_keyboard_control:main',
        ],
    },
)
