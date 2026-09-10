# /home/p2bot/workspace/robofun-1.0/object-detection-ws/src/object_detection
from setuptools import find_packages, setup

package_name = 'object_detection'

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
    maintainer='amr01',
    maintainer_email='amr01@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'object_detection_node = object_detection.object_detection_node:main',
            'patrol_node = object_detection.patrol_node:main', # <--- new node for patroling
            'plate_recognition_node = object_detection.plate_recognition_node:main', # <---
            'person_detection_node = object_detection.person_detection_node:main',
        ],
    },
)
