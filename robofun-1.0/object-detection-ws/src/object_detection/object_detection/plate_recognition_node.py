#!/usr/bin/env python3
import os
import time
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge
from ultralytics import YOLO

class PlateRecognitionNode(Node):
    def __init__(self):
        super().__init__('plate_recognition_node')
        
        self.bridge = CvBridge()
        self.get_logger().info("Starting Custom OpenVINO Perodua Detection Node... Accelerated by Intel iGPU!")

        # 1. Load your custom OpenVINO model
        home_dir = os.path.expanduser('~')
        model_path = os.path.join(home_dir, 'workspace/robofun-1.0/object-detection-ws/model/Perodua_openvino_model')
        
        self.get_logger().info(f"Loading OpenVINO model from: {model_path}")
        self.model = YOLO(model_path)

        # Static class mapping
        self.class_names = {
            0: 'Alza', 1: 'Aruz', 2: 'Ativa', 3: 'Axia', 
            4: 'Bezza', 5: 'Frame', 6: 'Myvi', 7: 'QV-E', 8: 'Traz'
        }
        self.FRAME_CLASS_ID = 5

        # Standard Camera Intrinsics (Default approximation; updated dynamically if available)
        self.fx = 615.0  # Focal length X (pixels)
        self.fy = 615.0  # Focal length Y (pixels)
        self.cx = 320.0  # Principal point X (pixels)
        self.cy = 240.0  # Principal point Y (pixels)

        # ROS 2 Subscriptions & Publishers
        self.sub_color = self.create_subscription(Image, '/p2bot/camera/color/image_raw', self.color_callback, 10)
        self.sub_depth = self.create_subscription(Image, '/p2bot/camera/aligned_depth_to_color/image_raw', self.depth_callback, 10)

        self.pub_annotated_img = self.create_publisher(Image, '/p2bot/plate_detection/image', 10)
        self.pub_car_model = self.create_publisher(String, '/p2bot/detected_car_model', 10)
        
        # Nav2 / Cartographer ready Pose Publisher
        self.pub_car_pose = self.create_publisher(PoseStamped, '/p2bot/car_pose', 10)

        self.latest_depth_image = None
        self.frame_counter = 0
        self.process_every_n_frames = 2 

        self.prev_time = time.time()
        self.fps = 0.0

    def depth_callback(self, msg):
        self.latest_depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")

    def color_callback(self, msg):
        self.frame_counter += 1
        if self.frame_counter % self.process_every_n_frames != 0:
            return 

        curr_time = time.time()
        time_diff = curr_time - self.prev_time
        if time_diff > 0:
            self.fps = 1.0 / time_diff
        self.prev_time = curr_time

        frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        
        # 1. Run inference on Intel iGPU (device="GPU")
        results = self.model(frame, device="intel:gpu", conf=0.35, verbose=False)
        vis_frame = frame.copy()

        frame_boxes = []  # List of Frame bounding boxes: [(fx1, fy1, fx2, fy2, fcx, fcy)]
        car_boxes = []    # List of Car model bounding boxes: [(cx1, cy1, cx2, cy2, ccx, ccy, label)]

        # 2. Separate 'Frame' detections from 'Car Model' detections
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls_id = int(box.cls[0])
                label = self.class_names.get(cls_id, "Unknown")
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                if cls_id == self.FRAME_CLASS_ID:
                    frame_boxes.append((x1, y1, x2, y2, center_x, center_y))
                elif cls_id != self.FRAME_CLASS_ID:
                    car_boxes.append((x1, y1, x2, y2, center_x, center_y, label))

        # 3. Filter: Only process car models located INSIDE a detected Frame
        for (fx1, fy1, fx2, fy2, fcx, fcy) in frame_boxes:
            # Draw Frame Bounding Box (Blue)
            cv2.rectangle(vis_frame, (fx1, fy1), (fx2, fy2), (255, 0, 0), 2)
            cv2.putText(vis_frame, "Frame", (fx1, fy1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            # Measure distance from the FRAME'S center depth
            distance_m = 0.0
            if self.latest_depth_image is not None:
                h_depth, w_depth = self.latest_depth_image.shape[:2]
                if 0 <= fcx < w_depth and 0 <= fcy < h_depth:
                    distance_mm = self.latest_depth_image[fcy, fcx]
                    distance_m = distance_mm / 1000.0

            # Check for any car model inside this frame box
            for (cx1, cy1, cx2, cy2, ccx, ccy, car_label) in car_boxes:
                # Bounding box containment check
                if fx1 <= ccx <= fx2 and fy1 <= ccy <= fy2:
                    
                    # Log to terminal (Only triggers when valid car is inside frame)
                    log_msg = f"{car_label}: {distance_m:.2f} Meters"
                    self.get_logger().info(log_msg)

                    # Publish String Topic
                    str_msg = String()
                    str_msg.data = log_msg
                    self.pub_car_model.publish(str_msg)

                    # Draw Car Bounding Box (Green)
                    cv2.rectangle(vis_frame, (cx1, cy1), (cx2, cy2), (0, 255, 0), 2)
                    cv2.putText(vis_frame, log_msg, (cx1, cy1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    # 4. Publish 3D Pose for Cartographer / Nav2
                    if distance_m > 0:
                        pose_msg = PoseStamped()
                        pose_msg.header.stamp = self.get_clock().now().to_msg()
                        pose_msg.header.frame_id = "camera_color_optical_frame"

                        # 3D Position relative to camera frame (Pinhole Projection)
                        pose_msg.pose.position.x = float((fcx - self.cx) * distance_m / self.fx)
                        pose_msg.pose.position.y = float((fcy - self.cy) * distance_m / self.fy)
                        pose_msg.pose.position.z = float(distance_m)
                        
                        # Neutral Orientation (Quaternion)
                        pose_msg.pose.orientation.w = 1.0

                        self.pub_car_pose.publish(pose_msg)

        # 5. Draw FPS Overlay
        h_vis, w_vis = vis_frame.shape[:2]
        cv2.rectangle(vis_frame, (w_vis - 170, 10), (w_vis - 10, 50), (0, 0, 0), -1)
        cv2.putText(vis_frame, f"FPS: {self.fps:.1f}", (w_vis - 160, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Publish visual feed to RViz2
        img_msg = self.bridge.cv2_to_imgmsg(vis_frame, encoding="bgr8")
        self.pub_annotated_img.publish(img_msg)

def main(args=None):
    rclpy.init(args=args)
    node = PlateRecognitionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()