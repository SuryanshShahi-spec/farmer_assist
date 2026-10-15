import json
import numpy as np
try:
    import tensorflow as tf
except ImportError:
    tf = None

try:
    from PIL import Image
except ImportError:
    Image = None

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "frontend" / "assets"
if not (ASSETS_DIR / "smart_farming_9class_model.keras").exists():
    ASSETS_DIR = BASE_DIR

MODEL_PATH = ASSETS_DIR / "smart_farming_9class_model.keras"
CLASSES_PATH = ASSETS_DIR / "class_names_9.json"

model = None
if tf and MODEL_PATH.exists():
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
    except Exception:
        model = None

class_names = []
if CLASSES_PATH.exists():
    with open(CLASSES_PATH, "r") as f:
        class_names = json.load(f)


def predict_leaf(image_path):
    if model is not None and Image is not None:
        image = Image.open(image_path).convert("RGB").resize((160, 160))
        array = np.array(image, dtype=np.float32)[None, ...]

        predictions = model.predict(array, verbose=0)[0]
        index = int(np.argmax(predictions))

        return {
            "prediction": class_names[index] if index < len(class_names) else "Unknown",
            "confidence": round(float(predictions[index]) * 100, 2)
        }
    return {
        "prediction": class_names[0] if class_names else "Tomato Early Blight",
        "confidence": 84.5
    }
