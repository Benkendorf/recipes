import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

from sqids import Sqids

from .constants import SHORT_LINK_DOMAIN, SHORT_LINK_MIN_LENGTH

#User = get_user_model()
from users.models import CustomUser


class Tag(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField()

    class Meta:
        default_related_name = 'tags'


class Ingredient(models.Model):
    name = models.CharField(max_length=256)
    measurement_unit = models.CharField(max_length=50)

    class Meta:
        default_related_name = 'ingredients'


class Recipe(models.Model):
    name = models.CharField(max_length=256)
    image = models.ImageField(upload_to='recipes')
    text = models.TextField()
    cooking_time = models.IntegerField()
    #short_link = models.SlugField()
    datetime_created = models.DateTimeField(
        'Дата создания',
        auto_now_add=True
    )

    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Тэги'
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        #through_fields=('recipe', 'ingredient'),
        verbose_name='Ингредиенты'
    )

    class Meta:
        default_related_name = 'recipes'

    def get_short_link(self):
        sqids = Sqids(
            min_length=SHORT_LINK_MIN_LENGTH,
        )
        short_code = sqids.encode([self.id])
        return f"{SHORT_LINK_DOMAIN}/s/{short_code}"


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тэг'
    )

    class Meta:
        unique_together = ('recipe', 'tag')


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipe_ingredients',
    )
    amount = models.PositiveIntegerField()

    class Meta:
        unique_together = ('recipe', 'ingredient')


class Favorites(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    list_owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Владелец списка избранного'
    )


class ShoppingCart(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_carts',
    )
    cart_owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Владелец списка покупок'
    )
