from django.core.exceptions import ValidationError
from .constants import MAX_IMAGE_SIZE, MAX_IMAGE_SIZE_ERROR


def validate_img_size(value):
    limit = MAX_IMAGE_SIZE
    if value.size > limit:
        raise ValidationError(MAX_IMAGE_SIZE_ERROR)
