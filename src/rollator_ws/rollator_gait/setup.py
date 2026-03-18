from setuptools import setup

package_name = 'rollator_gait'

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
    keywords=['ROS2', 'Gait', 'Recognition', 'Biomedical'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development',
    ],
    description='Gait recognition and analysis for Smart Rollator',
    long_description='ROS 2 gait recognition module focusing on legs and thighs',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gait_analyzer_node = rollator_gait.gait_analyzer_node:main',
        ],
    },
)
