from setuptools import setup

package_name = 'rollator_motor'

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
    keywords=['ROS2', 'Motor', 'Motor Controller', 'Jetson'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development',
    ],
    description='Motor controller for Smart Rollator',
    long_description='ROS 2 motor control interface for Jetson Nano',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'motor_controller_node = rollator_motor.motor_controller_node:main',
        ],
    },
)
