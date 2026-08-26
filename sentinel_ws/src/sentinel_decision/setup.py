from setuptools import find_packages, setup

package_name = 'sentinel_decision'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ethan',
    maintainer_email='hhhrrrppp123654@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [

            'lesson01_decision = sentinel_decision.lesson01_decision:main',

            'lesson02_health_publisher = sentinel_decision.lesson02_health_publisher:main',

            'lesson03_decision_subscriber = sentinel_decision.lesson03_decision_subscriber:main',

            'lesson04_mission_decision = sentinel_decision.lesson04_mission_decision:main',

            'lesson05_target_manager = sentinel_decision.lesson05_target_manager:main',

            'lesson06_decision_with_target = sentinel_decision.lesson06_decision_with_target:main',
        ],
    },
)
