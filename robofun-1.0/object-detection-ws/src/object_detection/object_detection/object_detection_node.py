#file location: /home/p2bot/workspace/robofun-1.0/object-detection-ws/src/object_detection/object_detection
# Import packages
import cv2
import sys
import random
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Tuple, Dict

# ROS2 libraries
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
from object_detection_msgs.msg import Object, Objects

import torch
from ultralytics import YOLO
from ultralytics.yolo.utils import ops
from ultralytics.yolo.utils.plotting import colors
from openvino.runtime import Core

class ObjectDetection(Node):
    def __init__(self):
        super().__init__('ObjectDetectionNode')

        self.declare_parameter('model_name', 'yolov8n')
        self.model_name = self.get_parameter('model_name').get_parameter_value().string_value
        self.get_logger().info(f"Params - model_name: {self.model_name}")

        self.declare_parameter('device', 'AUTO')
        self.device = self.get_parameter('device').get_parameter_value().string_value
        self.get_logger().info(f"Params - device: {self.device}")

        self.declare_parameter('model_detection_threshold', 0.01)
        self.model_detection_threshold = self.get_parameter('model_detection_threshold').get_parameter_value().double_value
        self.get_logger().info(f"Params - model_detection_threshold: {self.model_detection_threshold}")

        self.declare_parameter('publish_frame_size', (640, 480))
        self.publish_frame_size = self.get_parameter('publish_frame_size').get_parameter_value().integer_array_value
        self.get_logger().info(f"Params - publish_frame_size: {self.publish_frame_size}")

        self.model_dir = Path('./models')
        self.ov_model_path = self.model_dir / f"{self.model_name}_openvino_model/{self.model_name}.xml"

        if not self.ov_model_path.exists():
            self.get_logger().info(f"Model:{self.model_name} not available at {self.model_dir}, Downloading ...")
            self._download_default_model(self.model_dir, self.model_name)

        self.get_logger().info(f"Loading model from {self.ov_model_path} using device: {self.device}")
        self.model = self._load_model(self.ov_model_path, self.device)
        self.model_labels = self._load_model_labels(self.model_dir, self.model_name)

         # subscriber
        self.color_img_subscriber = self.create_subscription(Image, 'camera/color/image_raw', self.color_img_callback, 10)

        # result publisher
        self.det_image_publisher = self.create_publisher(Image, 'camera/image_tracked', 10)
        self.det_result_publisher = self.create_publisher(Objects, 'camera/detected_objects', 10)

        self.br = CvBridge()
        self.get_logger().info(f"Starting inferencing on object detection node.")

    def _download_default_model(self, model_dir, model_name):
        model_dir.mkdir(exist_ok=True)
        det_model = YOLO(model_dir / f'{model_name}.pt')
        det_model.export(format="openvino", dynamic=True, half=False)

    def _load_model(self, model_path, device):
        core = Core()
        det_ov_model = core.read_model(model_path)
        if device != "CPU":
            det_ov_model.reshape({0: [1, 3, 640, 640]})
        det_compiled_model = core.compile_model(det_ov_model, device)
        return det_compiled_model

    def _load_model_labels(self, model_dir, model_name):
        det_model = YOLO(model_dir / f'{model_name}.pt')
        return det_model.model.names

    def _preprocess_img(self, img):
        def _letterbox(img: np.ndarray, new_shape: Tuple[int, int] = (640, 640), color: Tuple[int, int, int] = (114, 114, 114), auto: bool = False, scale_fill: bool = False, scaleup: bool = False, stride: int = 32):
            """
            Resize image and padding for detection. Takes image as input,
            resizes image to fit into new shape with saving original aspect ratio and pads it to meet stride-multiple constraints

            Parameters:
            img (np.ndarray): image for preprocessing
            new_shape (Tuple(int, int)): image size after preprocessing in format [height, width]
            color (Tuple(int, int, int)): color for filling padded area
            auto (bool): use dynamic input size, only padding for stride constrins applied
            scale_fill (bool): scale image to fill new_shape
            scaleup (bool): allow scale image if it is lower then desired input size, can affect model accuracy
            stride (int): input padding stride
            Returns:
            img (np.ndarray): image after preprocessing
            ratio (Tuple(float, float)): hight and width scaling ratio
            padding_size (Tuple(int, int)): height and width padding size
            """
            # Resize and pad image while meeting stride-multiple constraints
            shape = img.shape[:2]  # current shape [height, width]
            if isinstance(new_shape, int):
                new_shape = (new_shape, new_shape)

            # Scale ratio (new / old)
            r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
            # only scale down, do not scale up (for better test mAP)
            if not scaleup:
                r = min(r, 1.0)

            # Compute padding
            ratio = r, r  # width, height ratios
            new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
            dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - \
                new_unpad[1]  # wh padding
            if auto:  # minimum rectangle
                dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding
            elif scale_fill:  # stretch
                dw, dh = 0.0, 0.0
                new_unpad = (new_shape[1], new_shape[0])
                ratio = new_shape[1] / shape[1], new_shape[0] / \
                    shape[0]  # width, height ratios

            dw /= 2  # divide padding into 2 sides
            dh /= 2

            if shape[::-1] != new_unpad:  # resize
                img = cv2.resize(
                    img, new_unpad, interpolation=cv2.INTER_LINEAR)
            top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
            left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
            img = cv2.copyMakeBorder(
                img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
            return img, ratio, (dw, dh)

        img = _letterbox(img)[0]

        # Convert HWC to CHW
        img = img.transpose(2, 0, 1)
        img = np.ascontiguousarray(img)
        return img

    def _image_to_tensor(self, image: np.ndarray):
        """
        Preprocess image according to YOLOv8 input requirements.
        Takes image in np.array format, resizes it to specific size using letterbox resize and changes data layout from HWC to CHW.

        Parameters:
        img (np.ndarray): image for preprocessing
        Returns:
        input_tensor (np.ndarray): input tensor in NCHW format with float32 values in [0, 1] range
        """
        input_tensor = image.astype(np.float32)  # uint8 to fp32
        input_tensor /= 255.0  # 0 - 255 to 0.0 - 1.0

        # add batch dimension
        if input_tensor.ndim == 3:
            input_tensor = np.expand_dims(input_tensor, 0)
        return input_tensor

    def _postprocess(
        self,
        pred_boxes: np.ndarray,
        input_hw: Tuple[int, int],
        orig_img: np.ndarray,
        min_conf_threshold: float = 0.25,
        nms_iou_threshold: float = 0.7,
        agnosting_nms: bool = False,
        max_detections: int = 300,
        pred_masks: np.ndarray = None,
        retina_mask: bool = False
    ):
        """
        YOLOv8 model postprocessing function. Applied non maximum supression algorithm to detections and rescale boxes to original image size
        Parameters:
            pred_boxes (np.ndarray): model output prediction boxes
            input_hw (np.ndarray): preprocessed image
            orig_image (np.ndarray): image before preprocessing
            min_conf_threshold (float, *optional*, 0.25): minimal accepted confidence for object filtering
            nms_iou_threshold (float, *optional*, 0.45): minimal overlap score for removing objects duplicates in NMS
            agnostic_nms (bool, *optiona*, False): apply class agnostinc NMS approach or not
            max_detections (int, *optional*, 300):  maximum detections after NMS
            pred_masks (np.ndarray, *optional*, None): model ooutput prediction masks, if not provided only boxes will be postprocessed
            retina_mask (bool, *optional*, False): retina mask postprocessing instead of native decoding
        Returns:
        pred (List[Dict[str, np.ndarray]]): list of dictionary with det - detected boxes in format [x1, y1, x2, y2, score, label] and segment - segmentation polygons for each element in batch
        """
        nms_kwargs = {"agnostic": agnosting_nms, "max_det": max_detections}
        # if pred_masks is not None:
        #     nms_kwargs["nm"] = 32
        preds = ops.non_max_suppression(
            torch.from_numpy(pred_boxes),
            min_conf_threshold,
            nms_iou_threshold,
            nc=80,
            **nms_kwargs
        )
        results = []
        proto = torch.from_numpy(
            pred_masks) if pred_masks is not None else None

        for i, pred in enumerate(preds):
            shape = orig_img[i].shape if isinstance(
                orig_img, list) else orig_img.shape
            if not len(pred):
                results.append({"det": [], "segment": []})
                continue
            if proto is None:
                pred[:, :4] = ops.scale_boxes(
                    input_hw, pred[:, :4], shape).round()
                results.append({"det": pred})
                continue
            if retina_mask:
                pred[:, :4] = ops.scale_boxes(
                    input_hw, pred[:, :4], shape).round()
                masks = ops.process_mask_native(
                    proto[i], pred[:, 6:], pred[:, :4], shape[:2])  # HWC
                segments = [ops.scale_segments(
                    input_hw, x, shape, normalize=False) for x in ops.masks2segments(masks)]
            else:
                masks = ops.process_mask(
                    proto[i], pred[:, 6:], pred[:, :4], input_hw, upsample=True)
                pred[:, :4] = ops.scale_boxes(
                    input_hw, pred[:, :4], shape).round()
                segments = [ops.scale_segments(
                    input_hw, x, shape, normalize=False) for x in ops.masks2segments(masks)]
            results.append({"det": pred[:, :6].numpy(), "segment": segments})
        return results

    def _publish_objects_msgs(self, results: Dict, label = None):
        label_map = label if label is not None else self.model_labels
        boxes = results["det"]

        objects_msg = Objects()
        objects_msg.header.stamp = self.get_clock().now().to_msg()
        objects_msg.header.frame_id = "camera_frame"
        masks = results.get("segment")

        for idx, (*xyxy, conf, lbl) in enumerate(boxes):
            if int(lbl) in label_map:
                object_msg = Object()
                object_msg.class_id = int(lbl)
                object_msg.id = idx
                object_msg.label = label_map[int(lbl)]
                object_msg.confidence = float(conf)  
                object_msg.x = float(xyxy[0])
                object_msg.y = float(xyxy[1])
                object_msg.width = float(xyxy[2]) - float(xyxy[0])
                object_msg.height = float(xyxy[3]) - float(xyxy[1])
                object_msg.vel_x = 0.0  # dummy value, needs velocity calculation logic
                object_msg.vel_y = 0.0  # dummy value, needs velocity calculation logic
                objects_msg.objects.append(object_msg)
        self.det_result_publisher.publish(objects_msg)

    def draw_results(self, results: Dict, source_image: np.ndarray, label=None):
        """
        Helper function for drawing bounding boxes on image
        Parameters:
            image_res (np.ndarray): detection predictions in format [x1, y1, x2, y2, score, label_id]
            source_image (np.ndarray): input image for drawing
            label_map; (Dict[int, str]): label_id to class name mapping
        Returns:

        """
        def plot_one_box(box: np.ndarray, img: np.ndarray, color: Tuple[int, int, int] = None, mask: np.ndarray = None, label: str = None, line_thickness: int = 5):
            """
            Helper function for drawing single bounding box on image
            Parameters:
                x (np.ndarray): bounding box coordinates in format [x1, y1, x2, y2]
                img (no.ndarray): input image
                color (Tuple[int, int, int], *optional*, None): color in BGR format for drawing box, if not specified will be selected randomly
                mask (np.ndarray, *optional*, None): instance segmentation mask polygon in format [N, 2], where N - number of points in contour, if not provided, only box will be drawn
                label (str, *optonal*, None): box label string, if not provided will not be provided as drowing result
                line_thickness (int, *optional*, 5): thickness for box drawing lines
            """
            # Plots one bounding box on image img
            tl = line_thickness or round(
                0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
            color = color or [random.randint(0, 255) for _ in range(3)]
            c1, c2 = (int(box[0]), int(box[1])), (int(box[2]), int(box[3]))
            cv2.rectangle(img, c1, c2, color, thickness=tl,
                          lineType=cv2.LINE_AA)
            if label:
                tf = max(tl - 1, 1)  # font thickness
                t_size = cv2.getTextSize(
                    label, 0, fontScale=tl / 3, thickness=tf)[0]
                c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
                cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
                cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3,
                            [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)
            if mask is not None:
                image_with_mask = img.copy()
                mask
                cv2.fillPoly(image_with_mask, pts=[
                             mask.astype(int)], color=color)
                img = cv2.addWeighted(img, 0.5, image_with_mask, 0.5, 1)
            return img

        label_map = label if label is not None else self.model_labels
        boxes = results["det"]
        masks = results.get("segment")
        h, w = source_image.shape[:2]
        for idx, (*xyxy, conf, lbl) in enumerate(boxes):
            if int(lbl) in label_map:
                label = f'{label_map[int(lbl)]} {conf:.2f}'
                mask = masks[idx] if masks is not None else None
                source_image = plot_one_box(xyxy, source_image, mask=mask, label=label, color=colors(int(lbl)), line_thickness=1)
        return source_image

    def run_inference(self, image):
        num_outputs = len(self.model.outputs)
        preprocessed_image = self._preprocess_img(image)
        input_tensor = self._image_to_tensor(preprocessed_image)
        result = self.model(input_tensor)
        boxes = result[self.model.output(0)]

        masks = None
        if num_outputs > 1:
            masks = result[self.model.output(1)]
        input_hw = input_tensor.shape[2:]
        detections = self._postprocess(
            pred_boxes=boxes, input_hw=input_hw, orig_img=image, pred_masks=masks)
        return detections

    def color_img_callback(self, msg):
        if not msg:
            self.get_logger().info(f"No message received from camera topic. Please verify if the camera topic is set correctly.")
            return

        current_frame = self.br.imgmsg_to_cv2(msg)
        detections = self.run_inference(current_frame)[0]
        filtered_detections = [
            row for row in detections['det'] if row[4] >= self.model_detection_threshold]
        if len(filtered_detections) > 0:
            filtered_tensor = torch.stack(filtered_detections)
        else:
            filtered_tensor = torch.tensor([])
        filtered_data = {'det': filtered_tensor}
        image_with_boxes = self.draw_results(filtered_data, current_frame)

        self.get_logger().info(f"Publishing Objects data", once=True)
        self._publish_objects_msgs(filtered_data)

        self.get_logger().info(f"Publishing detection frame in size: {self.publish_frame_size[0], self.publish_frame_size[1]}", once=True)
        stream_img = image_with_boxes[:,:,::-1]
        image_message = self.br.cv2_to_imgmsg(stream_img, encoding="bgr8")
        self.det_image_publisher.publish(image_message)

def main(args=None):
    rclpy.init(args=args)
    node = ObjectDetection()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

