from django.core.exceptions import ValidationError

from .constants import COOKING_TIME_MIN_VALUE, INGREDIENT_AMOUNT_MIN_VALUE


def cooking_time_validator(value):
    if value < COOKING_TIME_MIN_VALUE:
        raise ValidationError('Время готовки не может быть меньше 1 минуты!')


def ingredient_amount_validator(value):
    if value < INGREDIENT_AMOUNT_MIN_VALUE:
        raise ValidationError('Количество не может быть меньше 1!')
