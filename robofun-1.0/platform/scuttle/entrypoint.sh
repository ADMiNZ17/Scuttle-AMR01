#!/bin/bash
set -e

ros_env_setup="/ros2_ws/ROS2/install/setup.bash"
source "$ros_env_setup"
exec "$@"