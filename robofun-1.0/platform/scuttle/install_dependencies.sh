#!/bin/bash

ROS_DISTRO=humble
LIBREALSENSE_VERSION="v2.51.1"
LIBREALSENSE_COMMIT="af7510c8d58f70381056a758cd3f4553aa37fc69"
REALSENSE_ROS_VER="7d376fa3eff1f7c41d5cd06ed9371da125aa782c"
WORKDIR=`pwd`

install_ros2(){
    if ! [ -d "/opt/ros/${ROS_DISTRO}" ] 
    then
        echo -e "Installing ROS2 ${ROS_DISTRO}"
        apt update
        apt install -y locales
        locale-gen en_US en_US.UTF-8
        update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
        export LANG=en_US.UTF-8

        apt install -y software-properties-common
        add-apt-repository -y universe

        apt install -y curl gnupg2 lsb-release
        curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(source /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

        apt update
        apt install -y ros-${ROS_DISTRO}-desktop python3-argcomplete
    else
        echo -e "ROS2 installed."
    fi
}

install_librealsense() {
    if ! [ -x "$(command -v realsense-viewer)" ]; 
    then
        echo -e "Installing librealsense"
        mkdir -p /tmp/realsense
        cd /tmp/realsense
        git clone https://github.com/IntelRealSense/librealsense.git
        cd librealsense && \
        git checkout af7510c8d58f70381056a758cd3f4553aa37fc69 && \
        mkdir build && \
        cd build && \
        cmake .. && \
        make -j${nproc-1} && \
        make install
    else
        echo -e "librealsense installed."
    fi
}

echo -e "Kobuki platform installation started."
echo -e "Installing software dependencies."
install_ros2
install_librealsense

apt update && apt install -y python3-colcon-common-extensions \
    python3-pip \
    cmake \
    pkg-config \
    i2c-tools \
    ros-$ROS_DISTRO-angles \
    ros-$ROS_DISTRO-teleop-twist-joy \
    ros-$ROS_DISTRO-tf-transformations \
    ros-$ROS_DISTRO-joint-state-publisher \
    ros-$ROS_DISTRO-image-transport \
    ros-$ROS_DISTRO-image-transport-plugins \
    ros-$ROS_DISTRO-diagnostic-updater \
    ros-$ROS_DISTRO-rmw-cyclonedds-cpp \
    ros-$ROS_DISTRO-tf-transformations \
    ros-$ROS_DISTRO-joint-state-publisher

python3 -m pip install transforms3d smbus2
