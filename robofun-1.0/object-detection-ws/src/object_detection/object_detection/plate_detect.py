import os
import cv2
import numpy as np
import openvino as ov
# Import the existing OpenVINO core from your OCR script so we don't initialize two!
from object_detection.infer_image import core 


# Initialize OpenVINO directly inside plate_detect to avoid circular imports
core = ov.Core()

# Build the ABSOLUTE path to the new Stage 1 Detection Model
HOME = os.path.expanduser('~')
DETECTION_MODEL_PATH = os.path.join(HOME, 'workspace/models/intel/vehicle-license-plate-detection-barrier-0106/FP16/vehicle-license-plate-detection-barrier-0106.xml')

# Load and compile the Stage 1 model to your CPU/iGPU
compiled_det_model = core.compile_model(model=DETECTION_MODEL_PATH, device_name="CPU")
det_output_layer = compiled_det_model.output(0)

def find_plate_candidates(image_bgr: np.ndarray, use_mser: bool = False) -> list[tuple[int, int, int, int]]:
    """
    Hardware-accelerated OpenVINO plate detection.
    Replaces the old OpenCV contour method.
    """
    h, w = image_bgr.shape[:2]
    
    # 1. Preprocess the image to match the model's strict 300x300 BGR requirement
    resized = cv2.resize(image_bgr, (300, 300))
    # Remove the transpose so the shape remains [1, 300, 300, 3]
    input_tensor = np.expand_dims(resized, 0)
    
    # 2. Run Stage 1 Inference
    result = compiled_det_model([input_tensor])[det_output_layer]
    
    candidates = []
    
    # 3. Parse bounding boxes [1, 1, N, 7]
    for obj in result[0][0]:
        _, label, conf, xmin, ymin, xmax, ymax = obj
        
        # PRODUCTION MODE: Only look for Plates (Label 2) with > 50% confidence
        if int(label) == 2 and conf > 0.50:
            x1 = int(xmin * w)
            y1 = int(ymin * h)
            x2 = int(xmax * w)
            y2 = int(ymax * h)
            
            cw = x2 - x1
            ch = y2 - y1
            
            if cw > 0 and ch > 0:
                candidates.append((x1, y1, cw, ch))
            
    return candidates