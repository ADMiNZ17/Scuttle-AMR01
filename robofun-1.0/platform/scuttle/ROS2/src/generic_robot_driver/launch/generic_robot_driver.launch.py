#/home/p2bot/workspace/robofun-1.0/platform/scuttle/ROS2/src/generic_robot_driver/launch
import os
from ament_index_python.packages import get_package_share_path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    config_dir = os.path.join(get_package_share_path('generic_robot_driver'), 'config')
    robot_driver_path = config_dir + '/robot_driver.yaml' 

    robot_driver_node = Node(
        package='generic_robot_driver',
        executable='generic_robot_driver',
        output='screen',
        parameters=[{
            'i2c_bus_id': 13,
            'enable_tf_pub': True,
            'enable_jointstate_pub': True,
            'motor_type': 'hw213'
        }]
    )

    return LaunchDescription([
        robot_driver_node
    ])
