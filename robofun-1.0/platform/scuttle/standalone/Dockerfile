FROM ros:humble-ros-core

# Install Dependencies && Configure Locales
RUN apt update -q && \
    apt upgrade -yq && \
    DEBIAN_FRONTEND=noninteractive apt install -yq --no-install-recommends keyboard-configuration language-pack-en && \
    DEBIAN_FRONTEND=noninteractive apt install -yq --no-install-recommends wget curl git build-essential ca-certificates \
        tzdata tmux gnupg2 vim sudo lsb-release locales bash-completion zsh iproute2 iputils-ping net-tools dnsutils software-properties-common && \
    rm -rf /var/lib/apt/lists/*
RUN locale-gen en_US.UTF-8

# Setup Environment Variables
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8
ENV HOME /root
ENV ROS_DISTRO=humble

RUN apt update && \
    apt install -y --no-install-recommends \
        python3-argcomplete \
        python3-colcon-common-extensions \
        python3-rosdep \
        python3-colcon-mixin \
        python3-vcstool

RUN apt update && \
    apt install -y --no-install-recommends \
        ros-$ROS_DISTRO-cv-bridge \
        ros-$ROS_DISTRO-joy \
        ros-$ROS_DISTRO-robot-localization \
        ros-$ROS_DISTRO-diagnostic-updater \
        ros-$ROS_DISTRO-image-transport \
        ros-$ROS_DISTRO-xacro \
        ros-$ROS_DISTRO-tf-transformations \
        ros-$ROS_DISTRO-angles \
        ros-$ROS_DISTRO-image-transport-plugins \
        ros-$ROS_DISTRO-rmw-cyclonedds-cpp \
        ros-$ROS_DISTRO-robot-state-publisher \
        ros-$ROS_DISTRO-joint-state-publisher \
        ros-$ROS_DISTRO-teleop-twist-joy

RUN apt update && \
    apt install -y --no-install-recommends \
        python3-pip && \
    pip3 install \
        transforms3d smbus2

RUN apt update \
    && apt install -qq -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    libssl-dev \
    libusb-1.0-0-dev \
    pkg-config \
    libgtk-3-dev \
    libglfw3-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \    
    curl \
    python3 \
    python3-dev \
    ca-certificates \
    dkms

RUN apt install -qq -y --no-install-recommends \
    i2c-tools \
    && rm -rf /var/lib/apt/lists/*

ARG LIBREALSENSE_VERSION="v2.51.1"
ARG LIBREALSENSE_COMMIT="af7510c8d58f70381056a758cd3f4553aa37fc69"

WORKDIR /tmp
RUN git clone https://github.com/IntelRealSense/librealsense.git && cd librealsense && git checkout $LIBREALSENSE_COMMIT
RUN rm -rf librealsense/build && \
    mkdir -p librealsense/build && \
    cd librealsense/build && \
    cmake .. && \
    make -j${nproc-1} && \
    make install

RUN git clone https://github.com/YDLIDAR/YDLidar-SDK.git && cd YDLidar-SDK && git checkout 4cd3629
RUN mkdir -p YDLidar-SDK/build && \
   cd YDLidar-SDK/build && \
   cmake .. && \
   make -j${nproc-1} && \
   make install

WORKDIR /ros2_ws
COPY ./ROS2 ROS2

WORKDIR /ros2_ws/ROS2/src
RUN git clone -b humble https://github.com/YDLIDAR/ydlidar_ros2_driver.git
RUN git clone https://github.com/IntelRealSense/realsense-ros.git && cd realsense-ros && git checkout tags/4.51.1
RUN rm -rf scuttle_description && \
    git clone https://github.com/scuttlerobot/scuttle_description.git && \
    cp -rf scuttle_description/meshes generic_robot_driver/ && \
    cp -rf scuttle_description/urdf/*.xacro generic_robot_driver/urdf/ && \
    rm -rf scuttle_description

WORKDIR /ros2_ws
COPY ./setup.sh setup_scuttle.sh
RUN chmod +x setup_scuttle.sh && ./setup_scuttle.sh

COPY ./entrypoint.sh /ros_entrypoint.sh
RUN chmod +x /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]

WORKDIR /ros2_ws/ROS2
