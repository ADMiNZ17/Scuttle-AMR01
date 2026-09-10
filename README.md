Project: Robofun Training - Autonomous Mobile Robot (AMR) Workspace

This repository contains the software stack, configuration files, and ROS2 packages for the Robofun University Training program. The workspace is structured to support a 4-day curriculum covering AMR setup, SLAM mapping, object detection, and data visualization. 

To ensure all file paths, scripts, and configurations work exactly as detailed in the training guides, you must follow the strict naming scheme and directory structure outlined below.

-------------------------------------
1. Workspace Setup & Cloning
-------------------------------------
The training environment relies on hardcoded paths pointing to your user's workspace. You must create the workspace directory directly in your home folder and extract/clone the project files there.

1. Open your terminal and create the mandatory workspace directory:
   mkdir ~/workspace

2. Navigate to the newly created directory:
   cd ~/workspace

3. Clone this repository (or unzip the provided package) directly into this folder so that the resulting working path is exactly `~/workspace/robofun-1.0/`:
   unzip robofun-1.0.zip
   ```bash
   # Create a working directory (/workspace/) and clone it as (/workspace/robofun-1.0)
   git clone https://github.com/ADMiNZ17/Scuttle-AMR01.git robofun-1.0

-------------------------------------
2. Environment Variables & Naming Scheme
-------------------------------------
Every robot in the fleet requires a unique identifier to prevent ROS2 network collisions on the shared environment. You must configure your specific robot number across the system before launching the containers.

* ROS_DOMAIN_ID: A unique integer assigned to your robot.
* ROBOT_NAMESPACE: Your robot's name string (e.g., amr017, amr33).

Applying the Naming Scheme:
1. Navigate to the standalone Docker configuration directory:
   cd ~/workspace/robofun-1.0/platform/scuttle/standalone/

2. Open the Docker compose file for editing:
   gedit docker-compose.yml

3. Update the following environment variables in both the `amr.platform.scuttle` and `amr.platform.scuttle.teleop` container configurations:
   ROS_DOMAIN_ID=<your_robot_number>
   ROBOT_NAMESPACE=<your_robot_name>

Note: Whenever you open a new terminal for ROS2 tasks throughout this guide, you must export your domain ID to the environment:
   export ROS_DOMAIN_ID=<ROBOT_DOMAIN_ID>

-------------------------------------
3. Curriculum Execution Flow
-------------------------------------
Once your workspace and naming scheme are configured, you can proceed through the 4-day modules:

Day 1: Platform Preparation & Hardware Setup
* Install Ubuntu 22.04 LTS and the dedicated Intel IoTG kernel (linux-image-5.15.0-1049-intel-iotg).
* Install the Intel Robotics SDK 2.1.
* Run the hardware prerequisites script (hardware-preq.sh) and flash the Scuttle driver via the i2c bus.
* Build and launch the base AMR Docker containers via docker-compose.

Day 2: SLAM Mapping & Navigation
* Launch Cartographer for Simultaneous Localization and Mapping.
* Save your generated occupancy grid map to /home/$USER/workspace/robofun-1.0/my_map.
* Configure Nav2 for localization (AMCL) and autonomous navigation. Ensure the nav2_eiforamr_params.yml file uses your specific <ROBOT_NAMESPACE> for observation source topics like /scan.

Day 3: 3D Mapping & Object Detection
* Generate 3D maps using RTAB-Map and FastMapping via Intel OneAPI optimization.
* Set up a secondary workspace for object detection: mkdir -p ~/workspace/robofun-1.0/object-detection-ws/src.
* Compile and run the OpenVINO YOLOv8 object detection node utilizing your custom Object.msg and Objects.msg ROS2 interfaces.

Day 4: Node-RED & ROSBoard Visualization
* Install Node.js, Node-RED, and the Mosquitto MQTT broker.
* Build the scuttle_mqtt middleware package to bridge ROS2 topics to Node-RED.
* Configure the Node-RED dashboard to view detected objects and save cropped images to the global JSON object.
* Launch ROSBoard for web-based topic visualization accessible at http://localhost:8888.
