from django.contrib import admin

from .models import (Favorites, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'display_tags',
                    'display_ingredients', 'favorites_count')
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    filter_horizontal = ('tags', 'ingredients')

    inlines = [
        IngredientInline,
    ]

    @admin.display(description='Добавлений в избранное')
    def favorites_count(self, obj):
        return obj.favorites.count()

    @admin.display(description='Тэги')
    def display_tags(self, obj):
        tags = obj.tags.all()
        return ', '.join([tag.name for tag in tags]) if tags else '-'

    @admin.display(description='Ингредиенты')
    def display_ingredients(self, obj):
        ingredients = obj.recipe_ingredients.all()
        if not ingredients:
            return '-'
        return ', '.join(
            f'{ing.ingredient.name} ({ing.amount}'
            f' {ing.ingredient.measurement_unit})'
            for ing in ingredients
        )


@admin.register(Favorites)
class FavoritesAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'owner')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'owner')
