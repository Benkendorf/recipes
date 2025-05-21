from django.core.validators import MinValueValidator

from django.db import models
from sqids import Sqids
from users.models import CustomUser

from .constants import SHORT_LINK_DOMAIN, SHORT_LINK_MIN_LENGTH, TAG_NAME_MAX_LENGTH, INGREDIENT_NAME_MAX_LENGTH, RECIPE_NAME_MAX_LENGTH, MEASUREMENT_UNIT_MAX_LENGTH, COOKING_TIME_MIN_VALUE, INGREDIENT_AMOUNT_MIN_VALUE
from .validators import cooking_time_validator, ingredient_amount_validator

class Tag(models.Model):
    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        verbose_name='Название'
    )

    slug = models.SlugField(unique=True, verbose_name='Слаг')

    class Meta:
        default_related_name = 'tags'
        ordering = ['name']
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        verbose_name='Название'
    )

    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        unique_together = ('name', 'measurement_unit')
        default_related_name = 'ingredients'
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name='Название'
    )

    image = models.ImageField(upload_to='recipes', verbose_name='Картинка')
    text = models.TextField(verbose_name='Текст рецепта')
    cooking_time = models.SmallIntegerField(
        verbose_name='Время готовки',
        validators=[
            cooking_time_validator,
        ]
    )

    datetime_created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время создания'
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
        ordering = ['name']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

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
        ordering = ['recipe']
        verbose_name = 'РецептТэг'
        verbose_name_plural = 'РецептТэги'

    def __str__(self):
        return f'{self.recipe} помечен тэгом {self.tag}'


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
    amount = models.SmallIntegerField(
        verbose_name='Количество',
        validators=[
            ingredient_amount_validator,
        ]
    )

    class Meta:
        unique_together = ('recipe', 'ingredient')
        ordering = ['recipe']
        verbose_name = 'РецептИнгредиент'
        verbose_name_plural = 'РецептИнгредиенты'

    def __str__(self):
        return (f'{self.recipe} содержит {self.amount}'
                f' {self.ingredient.measurement_unit} {self.ingredient}')


class BaseUserRecipeList(models.Model):
    _recipe_related_name = None
    _owner_related_name = None

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name=_recipe_related_name,
    )
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Владелец списка',
        related_name=_owner_related_name,
    )

    class Meta:
        abstract = True
        unique_together = ('recipe', 'owner')
        ordering = ['owner']

    def __str__(self):
        return (f'{self.owner} добавил {self.recipe} в'
                f' {self._meta.verbose_name}')


class Favorites(BaseUserRecipeList):
    _recipe_related_name = 'favorites'
    _owner_related_name = 'favorites'

    class Meta(BaseUserRecipeList.Meta):
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Рецепты в избранном'


class ShoppingCart(BaseUserRecipeList):
    _recipe_related_name = 'shopping_carts'
    _owner_related_name = 'shopping_carts'

    class Meta(BaseUserRecipeList.Meta):
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
