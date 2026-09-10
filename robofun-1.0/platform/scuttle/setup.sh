#!/bin/bash
ROS_DISTRO=humble
WORKDIR=`pwd`

echo -e "Scuttle platform installation started."

echo -e "Compiling workspace."
cd $WORKDIR/ROS2
source /opt/ros/$ROS_DISTRO/setup.bash
colcon build --symlink-install


echo -e "Scuttle platform installation completed."
