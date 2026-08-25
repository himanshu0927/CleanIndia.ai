import os

from django.conf import settings
from PIL import Image, ImageStat, UnidentifiedImageError


MODEL_PATH = os.path.join(settings.BASE_DIR, 'ai_model', 'keras_model.h5')
LABELS_PATH = os.path.join(settings.BASE_DIR, 'ai_model', 'labels.txt')


class AIDetectorSetupError(Exception):
    pass


def validate_actual_image_content(image_file):
    try:
        image_file.seek(0)
        image = Image.open(image_file).convert('RGB')
    except (UnidentifiedImageError, OSError):
        image_file.seek(0)
        return False, 'Invalid image file. Please capture a clear garbage/waste photo.'

    width, height = image.size

    if width < 120 or height < 120:
        image_file.seek(0)
        return False, 'Photo is too small. Please capture a clear garbage/waste photo.'

    image = image.resize((160, 160))
    stat = ImageStat.Stat(image)
    brightness = sum(stat.mean) / len(stat.mean)
    variance = sum(stat.var) / len(stat.var)
    extrema = image.getextrema()
    dynamic_range = sum(high - low for low, high in extrema) / len(extrema)

    image_file.seek(0)

    if brightness < 25:
        return False, 'Photo is too dark. Please capture the garbage area clearly.'

    if brightness > 235:
        return False, 'Photo is too bright or blank. Please capture the garbage area clearly.'

    if variance < 70 or dynamic_range < 20:
        return False, 'Photo looks blank or unclear. Please capture actual garbage/waste content.'

    return True, ''


def _load_model_and_labels():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(LABELS_PATH):
        raise AIDetectorSetupError(
            'AI model files missing. Add keras_model.h5 and labels.txt inside swachhai/ai_model/.'
        )

    try:
        import numpy as np
        from PIL import Image
        from tensorflow.keras.models import load_model
    except ImportError as error:
        raise AIDetectorSetupError(
            'AI packages missing. Install tensorflow-cpu pillow numpy.'
        ) from error

    model = load_model(MODEL_PATH, compile=False)

    with open(LABELS_PATH, 'r', encoding='utf-8') as file:
        labels = [line.strip().split(' ', 1)[-1] for line in file.readlines()]

    return model, labels, Image, np


def detect_garbage_image(image_file):
    model, labels, Image, np = _load_model_and_labels()

    image_file.seek(0)
    image = Image.open(image_file).convert('RGB')
    image = image.resize((224, 224))

    image_array = np.asarray(image)
    normalized_image = (image_array.astype(np.float32) / 127.5) - 1

    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image

    prediction = model.predict(data, verbose=0)
    index = np.argmax(prediction)

    class_name = labels[index]
    confidence = int(prediction[0][index] * 100)

    image_file.seek(0)
    return class_name, confidence
