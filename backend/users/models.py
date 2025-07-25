from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from recipes.constants import (USER_FIRST_NAME_MAX_LENGTH,
                               USER_LAST_NAME_MAX_LENGTH)


class UserModel(AbstractUser):
    email = models.EmailField(unique=True, verbose_name='Адрес почты')
    first_name = models.CharField(
        max_length=USER_FIRST_NAME_MAX_LENGTH,
        verbose_name='Имя'
    )

    last_name = models.CharField(
        max_length=USER_LAST_NAME_MAX_LENGTH,
        verbose_name='Фамилия'
    )

    avatar = models.ImageField(
        upload_to='avatars',
        blank=True,
        default='',
        verbose_name='Аватар'
    )

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'

    class Meta:
        ordering = ['email']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='followers'
    )

    subscribed_to = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        verbose_name='Подписан на',
        related_name='follows'
    )

    class Meta:
        unique_together = ('subscriber', 'subscribed_to')
        ordering = ['subscribed_to']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.subscriber} подписан на {self.subscribed_to}'

    def clean(self):
        super().clean()

        if self.subscriber == self.subscribed_to:
            raise ValidationError("Нельзя подписаться на самого себя!")
