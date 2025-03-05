from django.contrib.auth.models import AbstractUser
from django.db import models

from recipes.models import Recipe, Favorites, ShoppingCart


class CustomUser(AbstractUser):
    # Переопределяем поля без blank=True.
    email = models.EmailField()
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    avatar = models.ImageField(upload_to='avatars', blank=True)

    favorites = models.ManyToManyField(
        Recipe,
        through=Favorites,
        verbose_name='Избранное'
    )

    shopping_cart = models.ManyToManyField(
        Recipe,
        through=ShoppingCart,
        verbose_name='Список покупок'
    )

    follows = models.ManyToManyField(
        'CustomUser',
        through='Follow',
        verbose_name='Подписки'
    )


class Follow(models.Model):
    follower = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Подписчик'
    )

    follows = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Подписан на'
    )
