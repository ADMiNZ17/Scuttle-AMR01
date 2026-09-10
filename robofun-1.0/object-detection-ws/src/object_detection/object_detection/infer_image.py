import os
import cv2
import numpy as np
import openvino as ov
#from object_detection.plate_detect import find_plate_candidates

# Initialize OpenVINO globally
core = ov.Core()

# Build the ABSOLUTE path to the model so ROS 2 always finds it
HOME = os.path.expanduser('~')
MODEL_PATH = os.path.join(HOME, 'workspace/robofun-1.0/object-detection-ws/model/text-recognition-0014.xml')

# Load the model
compiled_rec_model = core.compile_model(model=MODEL_PATH, device_name="CPU") # Change to NPU if testing the neural chip
recognition_output_layer = compiled_rec_model.output(0)

LETTERS = "~1234567890abcdefghijklmnopqrstuvwxyz"

def run_openvino_ocr(image_bgr: np.ndarray) -> tuple[str, float]:
    """Runs OCR and returns (text, confidence_score)"""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (128, 32))
    input_tensor = np.expand_dims(np.expand_dims(resized, 0), 0)
    
    result = compiled_rec_model([input_tensor])[recognition_output_layer]
    result = np.squeeze(result)
    
    text = ""
    confidences = []
    for letter_probs in result:
        idx = letter_probs.argmax()
        if idx == 0:
            continue
        text += LETTERS[idx]
        confidences.append(letter_probs[idx]) # Store the probability of this letter
        
    if not text:
        return "", 0.0
        
    # Calculate average confidence across all letters
    avg_conf = sum(confidences) / len(confidences)
    return text.upper(), float(avg_conf)

def draw_results(image_bgr: np.ndarray, results: list) -> np.ndarray:
    vis = image_bgr.copy()
    for (x, y, w, h), text in results:
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)
        (tw, th), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        cv2.rectangle(vis, (x, y - th - baseline - 5), (x + tw, y), (0, 255, 0), -1)
        cv2.putText(vis, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    return vis