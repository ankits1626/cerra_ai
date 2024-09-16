import base64
import logging
from io import BytesIO

import numpy as np
from fastapi import HTTPException
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
    try:
        # Decode the base64 image
        img_data = base64.b64decode(encoded_img)
        img = Image.open(BytesIO(img_data))
        img = img.resize(target_size)
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array /= 255.0  # Rescale the image to [0, 1]
        return img_array
    except (base64.binascii.Error, OSError, Exception) as e:
        logger.error(f"Error while processing the image: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid image format.")


# Function to make a prediction
def predict_receipt_type(encoded_img):
    logger.info("<<<<<  predict_receipt_type called")
    try:
        img_array = preprocess_image_from_base64(encoded_img)
        prediction = model.predict(img_array)
        class_index = int(
            prediction[0] > 0.5
        )  # Assuming binary classification with threshold 0.5
        class_labels = ["Handwritten", "Printed"]
        return class_labels[class_index], prediction[0]
    except HTTPException as e:
        # Log the error and re-raise the exception
        logger.error(f"Prediction failed: {str(e.detail)}")
        raise e
    except Exception as e:
        # Catch-all for other errors
        logger.error(f"Unexpected error in prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="Model prediction failed.")
