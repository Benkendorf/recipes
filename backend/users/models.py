from django.contrib.auth.models import AbstractUser
from django.db import models

#from recipes.models import Recipe, Favorites, ShoppingCart


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    avatar = models.ImageField(upload_to='avatars', blank=True, null=True)

    followings = models.ManyToManyField(
        'CustomUser',
        through='Subscription',
        verbose_name='Подписки'
    )

    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='followers'
    )

    subscribed_to = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Подписан на',
        related_name='follows'
    )
