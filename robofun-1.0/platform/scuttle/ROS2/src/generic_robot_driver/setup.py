import os
from setuptools import setup
from glob import glob

package_name = 'generic_robot_driver'
sub_package = "constants"
sub_modules = "generic_robot_driver/modules"
motor_module = "generic_robot_driver/modules/motor"
encoder_module = "generic_robot_driver/modules/encoder"

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name, sub_modules, motor_module, encoder_module],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch') , glob(os.path.join('launch', '*.launch.py'))),
        (os.path.join('share', package_name, 'config') , glob(os.path.join('config', '*.yaml'))),
        (os.path.join('share', package_name, 'meshes') , glob(os.path.join('meshes', '*.stl'))),
        (os.path.join('share', package_name, 'urdf') , glob(os.path.join('urdf', '*.*'))),
        (os.path.join('share', package_name, 'urdf/realsense') , glob(os.path.join('urdf/realsense', '*.*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'generic_robot_driver = generic_robot_driver.robot_base_driver:main'
        ],
    },
)
