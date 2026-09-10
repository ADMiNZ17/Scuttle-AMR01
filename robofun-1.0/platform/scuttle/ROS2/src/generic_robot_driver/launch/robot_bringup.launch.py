import os
import sys
from ament_index_python.packages import get_package_share_path
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

ROBOT_NAMESPACE = None
CAMERA_NAMESPACE = None
LIDAR_NAMESAPCE = None
SCUTTLE_URDF_PATH = None
SCUTTLE_BASE_TYPE = os.getenv("ROBOT_BASE_TYPE", "scuttle")
SCUTTLE_CONFIG_DIR = os.path.join(get_package_share_path('generic_robot_driver'), 'config')
SCUTTLE_URDF_DIR = get_package_share_path('generic_robot_driver')

if SCUTTLE_BASE_TYPE == "devkit":
    SCUTTLE_URDF_PATH = SCUTTLE_URDF_DIR / 'urdf/scuttle_ydlidar.xacro'
    MOTOR_TYPE = 'hw231'
    YDLIDAR_CONFIG_PATH = SCUTTLE_CONFIG_DIR + '/ydlidar.yaml' # configure YDLidar to use TYPE_TRIANGLE version
else:
    print(
        f"Base type: {SCUTTLE_BASE_TYPE} is currently not supported. Currently supported type: [devkit]")
    sys.exit(1)
    
print(
    f"[SCUTTLE_BRINGUP] - Running scuttle base type: {SCUTTLE_BASE_TYPE}, motor type:{MOTOR_TYPE}, YDLIDAR config:{YDLIDAR_CONFIG_PATH}")

env_namespace = os.getenv('ROBOT_NAMESPACE')
scan_topic = 'scan'
if env_namespace == "":
    print(f"[SCUTTLE_BRINGUP] - Namespace settings not available. Running node without namespace")
    ROBOT_NAMESPACE = "/"
    CAMERA_NAMESPACE = f'camera'
    CAMERA_TF_NAMESPACE = '/tf'
    CAMERA_TF_STATIC_NAMESPACE = '/tf_static'
    LIDAR_NAMESAPCE = scan_topic
else:
    print(
        f"[SCUTTLE_BRINGUP] - Namespace settings found. Running node with namespace: {env_namespace}")
    ROBOT_NAMESPACE = env_namespace
    CAMERA_NAMESPACE = f'/{ROBOT_NAMESPACE}/camera'
    CAMERA_TF_NAMESPACE = f'/{ROBOT_NAMESPACE}/tf'
    CAMERA_TF_STATIC_NAMESPACE = f'/{ROBOT_NAMESPACE}/tf_static'
    LIDAR_NAMESAPCE = f'/{ROBOT_NAMESPACE}/{scan_topic}'


def generate_launch_description():
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=ROBOT_NAMESPACE,
        parameters=[{'robot_description': ParameterValue(
            Command(['xacro ', str(SCUTTLE_URDF_PATH)]), value_type=str)}],
        remappings=[
            ('/tf', 'tf'),
            ('/tf_static', 'tf_static')
        ]
    )

    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        namespace=ROBOT_NAMESPACE
    )

    robot_driver_node = Node(
        package='generic_robot_driver',
        executable='generic_robot_driver',
        namespace=ROBOT_NAMESPACE,
        output='screen',
        parameters=[{
            'enable_tf_pub': True,
            'enable_jointstate_pub': True,
            'motor_type': MOTOR_TYPE
        }],
        remappings=[
            ('odom', 'odom/amr'),
            ('/tf', 'tf'),
            ('/tf_static', 'tf_static')
        ]
    )

    ydlidar_node = Node(
        package='ydlidar_ros2_driver',
        executable='ydlidar_ros2_driver_node',
        name='ydlidar_ros2_driver_node',
        output='screen',
        emulate_tty=True,
        parameters=[YDLIDAR_CONFIG_PATH],
        remappings=[
            ('scan', LIDAR_NAMESAPCE),
            ('/point_cloud', 'point_cloud')
        ]
    )

    realsense2_camera_node = Node(
        package='realsense2_camera',
        executable='realsense2_camera_node',
        namespace=CAMERA_NAMESPACE,
        name='scuttle_camera_node',
        parameters=[{
                'camera_name': 'camera',
                'serial_no': '',
                'usb_port_id': '',
                'device_type': '',
                'config_file': '',
                'unite_imu_method': 0,
                'json_file_path': '',
                'log_level': 'info',
                'output': 'screen',
                'enable_depth': True,
                'enable_color': True,
                'enable_infra1': False,
                'enable_infra2': False,
                'clip_distance': 4,
                'linear_accel_cov': 0.01,
                'initial_reset': True,
                'allow_no_texture_points': False,
                'ordered_pc': False,
                'tf_publish_rate': 0.0,
                'diagnostics_period': 0.0,
                'decimation_filter.enable': False,
                'reconnect_timeout': 6.,
                'align_depth.enable': True,
                'rgb_camera.profile': '1280,720,30',
                'depth_module.profile': '1280,720,30',
        }],
        remappings=[
            ('/tf', CAMERA_TF_NAMESPACE),
            ('/tf_static', CAMERA_TF_STATIC_NAMESPACE)
        ]
    )

    return LaunchDescription([
        joint_state_publisher_node,
        robot_state_publisher_node,
        robot_driver_node,
        ydlidar_node,
        realsense2_camera_node
    ])
