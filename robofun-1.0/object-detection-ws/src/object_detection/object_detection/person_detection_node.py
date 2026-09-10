#!/usr/bin/env python3
import sys
import site

# Force Python to load the upgraded OpenVINO packages from user site-packages first
user_site = site.getusersitepackages()
if user_site in sys.path:
    sys.path.remove(user_site)
sys.path.insert(0, user_site)

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import time
import openvino as ov

# Node to Nav2
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from action_msgs.srv import CancelGoal

class PersonDetectionNode(Node):
    def __init__(self):
        super().__init__('person_detection_node')
        self.get_logger().info("Starting Person Detection Node with Generic Webcam...")

        # --- Configuration ---
        self.model_path = "/home/p2bot/workspace/robofun-1.0/object-detection-ws/model/person-detection-0202.xml"
        self.conf_threshold = 0.25
        self.input_height = 512
        self.input_width = 512
        self.coverage_threshold = 0.40

        # --- OpenVINO Setup ---
        self.core = ov.Core()
        try:
            self.model = self.core.read_model(self.model_path)
            # Using "GPU" targets Intel iGPU hardware acceleration directly
            self.compiled_model = self.core.compile_model(self.model, "GPU")
            self.input_layer = self.compiled_model.input(0)
            self.output_layer = self.compiled_model.output(0)
            self.get_logger().info("✅ OpenVINO person-detection-0202 loaded successfully on iGPU!")
        except Exception as e:
            self.get_logger().error(f"Failed to load model on GPU, falling back to AUTO: {e}")
            self.compiled_model = self.core.compile_model(self.model, "AUTO")
            self.input_layer = self.compiled_model.input(0)
            self.output_layer = self.compiled_model.output(0)

        # --- ROS 2 Interfaces & Camera Setup ---
        self.bridge = CvBridge()
        
        self.cap = None
        possible_indices = [6] 
        
        for idx in possible_indices:
            self.get_logger().info(f"Trying camera index {idx}...")
            cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
            
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    self.cap = cap
                    self.get_logger().info(f"✅ Successfully opened and grabbed frame from index {idx}!")
                    break
                else:
                    self.get_logger().info(f"Index {idx} opened but returned no frames. Skipping.")
                    cap.release()
            else:
                self.get_logger().info(f"Could not open index {idx}.")

        if self.cap is None:
            self.get_logger().error("❌ Could not find a working camera stream on any index!")
            raise RuntimeError("Camera auto-discovery failed.")

        # Apply camera settings
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.get_logger().info("✅ Webcam configured successfully!")

        # Publisher for RViz
        self.image_pub = self.create_publisher(Image, '/person_detection/annotated_image', 10)
        
        # Timer for frame grabbing (~30 FPS)
        self.timer = self.create_timer(0.033, self.timer_callback)
        self.last_time = time.time()

        # --- Nav2 Pause/Resume Logic Variables ---
        self.pause_duration = 10.0
        self.is_paused = False
        self.last_person_time = 0.0
        self.saved_goal = None

        self.goal_sub = self.create_subscription(PoseStamped, 'goal_pose', self.goal_callback, 10)
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.cancel_client = self.create_client(CancelGoal, 'navigate_to_pose/_action/cancel_goal')

        self.create_timer(1.0, self.resume_check_callback)

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warning("Dropped frame from webcam")
            return

        frame_height, frame_width = frame.shape[:2]
        frame_area = frame_width * frame_height

        # --- Inference ---
        resized = cv2.resize(frame, (self.input_width, self.input_height))
        blob = cv2.dnn.blobFromImage(resized, size=(self.input_width, self.input_height),
                                     ddepth=cv2.CV_8U, swapRB=False)

        results = self.compiled_model([blob])[self.output_layer]
        detections = results[0][0]

        person_too_close = False

        # --- Draw Bounding Boxes ---
        for detection in detections:
            confidence = float(detection[2])
            if confidence > self.conf_threshold:
                xmin = int(detection[3] * frame_width)
                ymin = int(detection[4] * frame_height)
                xmax = int(detection[5] * frame_width)
                ymax = int(detection[6] * frame_height)

                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 3)
                cv2.putText(frame, f"Person {confidence:.2f}", (xmin, ymin - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # --- COVERAGE LOGIC ---
                box_area = (xmax - xmin) * (ymax - ymin)
                coverage_ratio = box_area / frame_area

                if coverage_ratio >= self.coverage_threshold:
                    self.last_person_time = time.time()
                    person_too_close = True
                    cv2.putText(frame, "WARNING: PERSON NEARBY", (50, 100), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)

                    if not self.is_paused:
                        self.get_logger().warn("🛑 PERSON DETECTED! Pausing Nav2 for 10 seconds...")
                        self.is_paused = True
                        
                        cancel_msg = CancelGoal.Request()
                        self.cancel_client.call_async(cancel_msg)

        if person_too_close:
            self.get_logger().warn("Person Nearby!")

        # --- FPS Calculation ---
        now = time.time()
        fps = 1.0 / max(1e-6, now - self.last_time)
        self.last_time = now

        cv2.putText(frame, f"FPS: {fps:.1f} (Webcam 6)", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

        try:
            annotated_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            self.image_pub.publish(annotated_msg)
        except Exception as e:
            self.get_logger().error(f"Failed to publish image: {e}")

    def destroy_node(self):
        if self.cap:
            self.cap.release()
        super().destroy_node()

    def goal_callback(self, msg):
        self.saved_goal = msg
        self.is_paused = False 
        self.get_logger().info("🗺️ New navigation goal saved!")

    def resume_check_callback(self):
        if self.is_paused:
            elapsed = time.time() - self.last_person_time
            
            if elapsed >= self.pause_duration:
                self.get_logger().info("🟢 Path clear for 10s! Resuming...")
                self.is_paused = False
                
                if self.saved_goal is not None:
                    if not self.nav_client.server_is_ready():
                        self.get_logger().warn("Nav2 server is down! Cannot resume goal.")
                        return

                    goal_msg = NavigateToPose.Goal()
                    goal_msg.pose = self.saved_goal
                    self.nav_client.send_goal_async(goal_msg)
                else:
                    self.get_logger().info("No RViz goal saved. Awaiting next command.")

def main(args=None):
    rclpy.init(args=args)
    node = PersonDetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down Person Detection Node.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()