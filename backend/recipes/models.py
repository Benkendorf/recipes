from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


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
    short_link = models.SlugField()

    author = models.ForeignKey(
        User,
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


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.IntegerField()


class Favorites(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )


class ShoppingCart(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
