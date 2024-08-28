import base64
import logging
from io import BytesIO

import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

from app.config.settings import settings

logger = logging.getLogger(__name__)
# Load your Keras model
model = load_model(settings.RECEIPT_CLASSIFIER_PATH)

image_size = (224, 224)  # Adjust the target size according to your model


# Function to preprocess the image
def preprocess_image_from_base64(encoded_img, target_size=(224, 224)):
    # Decode the base64 image
    img_data = base64.b64decode(encoded_img)
    img = Image.open(BytesIO(img_data))
    img = img.resize(target_size)
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0  # Rescale the image to [0, 1]
    return img_array


# Function to make a prediction
def predict_receipt_type(encoded_img):
    logger.info("<<<<<  predict_receipt_type called")
    img_array = preprocess_image_from_base64(encoded_img)
    prediction = model.predict(img_array)
    class_index = int(
        prediction[0] > 0.5
    )  # Assuming binary classification with threshold 0.5
    class_labels = ["Handwritten", "Printed"]
    return class_labels[class_index], prediction[0]