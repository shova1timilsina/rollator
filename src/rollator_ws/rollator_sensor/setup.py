from setuptools import setup
from glob import glob
import os

package_name = 'rollator_sensor'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    author='Smart Rollator Team',
    author_email='developer@rollator.local',
    maintainer='Smart Rollator Team',
    maintainer_email='developer@rollator.local',
    url='https://github.com/rollator/rollator',
    download_url='https://github.com/rollator/rollator/releases',
    keywords=['ROS2', 'Arducam', 'Depth Sensor', 'ToF'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development',
    ],
    description='Arducam depth sensor driver for Smart Rollator',
    long_description='ROS 2 driver for Arducam ToF/Depth camera on Jetson Nano',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'arducam_node = rollator_sensor.arducam_node:main',
        ],
    },
)
