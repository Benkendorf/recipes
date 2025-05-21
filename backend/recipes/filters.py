import django_filters
from django.db.models import Q

from .models import Favorites, Recipe, ShoppingCart, Tag


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
    )
    is_in_shopping_cart = django_filters.CharFilter(method='filter_by_cart')
    is_favorited = django_filters.CharFilter(method='filter_by_favorite')

    class Meta:
        model = Recipe
        fields = ['tags', 'is_in_shopping_cart', 'is_favorited', 'author']

    def filter_by_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        cart_recipe_ids = ShoppingCart.objects.filter(
            owner=user).values_list('recipe_id', flat=True)
        if value:
            return queryset.filter(id__in=cart_recipe_ids)
        return queryset.exclude(id__in=cart_recipe_ids)

    def filter_by_favorite(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        favorites_recipe_ids = Favorites.objects.filter(
            owner=user).values_list('recipe_id', flat=True)
        if value:
            return queryset.filter(id__in=favorites_recipe_ids)
        return queryset.exclude(id__in=favorites_recipe_ids)
