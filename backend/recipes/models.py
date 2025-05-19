
from django.db import models
from sqids import Sqids
from users.models import CustomUser

from .constants import SHORT_LINK_DOMAIN, SHORT_LINK_MIN_LENGTH


class Tag(models.Model):
    name = models.CharField(max_length=256)
    slug = models.SlugField(unique=True)

    class Meta:
        default_related_name = 'tags'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=256)
    measurement_unit = models.CharField(max_length=50)

    class Meta:
        default_related_name = 'ingredients'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название')
    image = models.ImageField(upload_to='recipes')
    text = models.TextField()
    cooking_time = models.IntegerField()
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
        verbose_name='Ингредиенты'
    )

    class Meta:
        default_related_name = 'recipes'

    def __str__(self):
        return self.name

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
        verbose_name='Рецепт',
        related_name='favorites'
    )
    list_owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Владелец списка избранного'
    )

    class Meta:
        verbose_name_plural = 'Favorites'


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
