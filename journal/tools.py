from django.core.exceptions import ValidationError
from .constants import MAX_IMAGE_SIZE, MAX_IMAGE_SIZE_ERROR
from uuid import uuid4
from datetime import datetime


def wrapper_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    new_filename = f"{uuid4()}.{ext}"
    date_now = datetime.now()
    return f'entries/{date_now.year}/{date_now.month:02}/{new_filename}'


def validate_img_size(value):
    limit = MAX_IMAGE_SIZE
    if value.size > limit:
        raise ValidationError(MAX_IMAGE_SIZE_ERROR)
