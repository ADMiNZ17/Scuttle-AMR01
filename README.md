# Project: Robofun Training - Autonomous Mobile Robot (AMR) Workspace

This repository contains the software stack, configuration files, and ROS 2 packages for the Robofun University Training program. The workspace is structured to support a 4-day curriculum covering AMR setup, SLAM mapping, object detection, and data visualization.

To ensure all file paths, scripts, and configurations work exactly as detailed in the training guides, you must follow the strict naming scheme and directory structure outlined below. The directory map has been updated to reflect the true structure of the repository.

---

## **1. Workspace Setup & Cloning**

The training environment relies on hardcoded paths pointing to your user's workspace. You must create the workspace directory directly in your home folder and extract or clone the project files there.

- Clone this repository (or unzip the provided package) directly into this folder so that the resulting working path is exactly `~/workspace/robofun-1.0/`:
   unzip robofun-1.0.zip
   ```bash
   # Clone this working directory (/home) OR Unzip it as (/workspace/robofun-1.0/.....)
   git clone https://github.com/ADMiNZ17/Scuttle-AMR01.git workspace

---

## **2. Environment Variables & Naming Scheme**

Every robot in the fleet requires a unique identifier to prevent ROS 2 network collisions on the shared environment. You must configure your specific robot number across the system before launching the containers.

* **`ROS_DOMAIN_ID`**: A unique integer assigned to your robot.


* **`ROBOT_NAMESPACE`**: Your robot's name string (e.g., amr017, amr33).



**Applying the Naming Scheme:**

1. Navigate to the standalone configuration directory:
```bash
cd ~/workspace/robofun-1.0/platform/scuttle/standalone/

```


2. Open the Docker compose file for editing (e.g., `gedit docker-compose.yml`).


3. Update the environment variables in both the `amr.platform.scuttle` and `amr.platform.scuttle.teleop` container configurations:


```yaml
ROS_DOMAIN_ID=<your_robot_number>
ROBOT_NAMESPACE=<your_robot_name>

```



> **Note:** Whenever you open a new terminal for ROS 2 tasks throughout this guide, you must export your domain ID to the environment: `export ROS_DOMAIN_ID=<ROBOT_DOMAIN_ID>`.
> 
> 

---

## **3. Software Stack & Directory Map**

The repository utilizes standard ROS 2 and Linux conventions. Below is the corrected map of your robot's software stack based on the physical file structure. Modify these files carefully to alter how the robot operates, communicates, and navigates.

### **Robot Hardware, Drivers & Firmware**

* **Hardware Setup Scripts**: `~/workspace/robofun-1.0/platform/scuttle/`
Contains `hardware-preq.sh`, `setup.sh`, and `install_dependencies.sh`.


* **Low-Level I2C Drivers**: `~/workspace/robofun-1.0/platform/scuttle/driver/I2C-Tiny-USB/`
Contains C-based firmware and kernel drivers for the USB to I2C bridge.


* **Generic Robot Driver Workspace**: `~/workspace/robofun-1.0/platform/scuttle/ROS2/src/generic_robot_driver/`
The master ROS package containing all hardware interfaces. Modifying files within this folder changes how ROS talks to the physical chassis.


* **Motor Driver (PCA9685)**: `.../generic_robot_driver/modules/motor/pca9685.py`
The I2C driver for the PWM motor shield. Modify this to change the PWM frequency (Hz) or correct I2C addresses.


* **Encoder Driver (AMS)**: `.../generic_robot_driver/modules/encoder/ams.py`
Reads hardware ticks from the wheels to calculate actual distance traveled.



### **Sensors, Navigation & Autonomy**

* **Bringup & Launch Scripts**: `.../generic_robot_driver/launch/`
Contains `robot_bringup.launch.py` and `generic_robot_driver.launch.py`. The master ignition switches to start nodes.


* **Robot Driver Config**: `.../generic_robot_driver/config/robot_driver.yaml`
Contains physical tuning parameters.


* **Nav2 Parameters**: `.../generic_robot_driver/config/nav2_eiforamr_params.yaml`
The navigation brain. Modify this to alter path planning, obstacle avoidance buffers, and acceleration limits (DWB local planner).


* **LiDAR Parameters**: `.../generic_robot_driver/config/ydlidar.yaml` (also located in `GT15/` and `T-mini/` subfolders)
Hardware-specific LiDAR rules. Modify this to change motor spin speed or minimum/maximum angle ranges.


* **Object Detection Node**: `~/workspace/robofun-1.0/object-detection-ws/src/object_detection/object_detection/`
Contains `object_detection_node.py`, `person_detection_node.py`, and `plate_recognition_node.py`. The AI vision loop modifying inference thresholds. Models are stored in `.../models/yolov8n_openvino_model/` and `.../model/Perodua_openvino_model/`.



### **Teleoperation**

* **Teleop Parameters**: `~/workspace/robofun-1.0/platform/scuttle/standalone/teleop_params.yaml`
Maps gamepad buttons to actions, assigning deadman switches or maximum speed multipliers.


* **Teleop Launch**: `.../generic_robot_driver/launch/robot_teleop.launch.py`
Initiates the manual control nodes.



---

## **4. Curriculum Execution Flow**

Once your workspace and naming scheme are configured, proceed through the 4-day modules:

### **Day 1: Platform Preparation & Hardware Setup**

* Install Ubuntu 22.04 LTS and the dedicated Intel IoTG kernel (`linux-image-5.15.0-1049-intel-iotg`).
* Install the Intel Robotics SDK 2.1.
* Run the hardware prerequisites script (`hardware-preq.sh`) and flash the Scuttle driver via the I2C bus.
* Build and launch the base AMR Docker containers via docker-compose.




### **Day 2: SLAM Mapping & Navigation**
* Launch Cartographer for Simultaneous Localization and Mapping.
* Save your generated occupancy grid map to `~/workspace/robofun-1.0/my_map`.
* Configure Nav2 for localization (AMCL) and autonomous navigation. Ensure the `nav2_eiforamr_params.yaml` file uses your specific `<ROBOT_NAMESPACE>` for observation source topics like `/scan`.




### **Day 3: 3D Mapping & Object Detection**
* Generate 3D maps using RTAB-Map and FastMapping via Intel OneAPI optimization.
* Set up the secondary workspace for object detection at `~/workspace/robofun-1.0/object-detection-ws/src`.
* Compile and run the OpenVINO YOLOv8 object detection node utilizing your custom `Object.msg` and `Objects.msg` ROS 2 interfaces.




### **Day 4: Node-RED & ROSBoard Visualization**
* Install Node.js, Node-RED, and the Mosquitto MQTT broker.
* Build the `scuttle_mqtt` middleware package to bridge ROS 2 topics to Node-RED.
* Configure the Node-RED dashboard to view detected objects and save cropped images to the global JSON object.
* Launch ROSBoard for web-based topic visualization accessible at `http://localhost:8888`.
