import django_filters
from django.db.models import Q

from .models import Favorites, Recipe, ShoppingCart


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(method='filter_by_tags')
    is_in_shopping_cart = django_filters.CharFilter(method='filter_by_cart')
    is_favorited = django_filters.CharFilter(method='filter_by_favorite')

    class Meta:
        model = Recipe
        fields = ['tags', 'is_in_shopping_cart', 'is_favorited', 'author']

    def filter_by_tags(self, queryset, name, value):
        tags = self.request.GET.getlist('tags')
        q_objects = Q()
        for tag in tags:
            q_objects |= Q(tags__slug=tag)
        return queryset.filter(q_objects).distinct()

    def filter_by_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        cart_recipe_ids = ShoppingCart.objects.filter(
            cart_owner=user).values_list('recipe_id', flat=True)
        if is_in_shopping_cart == '1':
            return queryset.filter(id__in=cart_recipe_ids)
        return queryset.exclude(id__in=cart_recipe_ids)

    def filter_by_favorite(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        is_favorited = self.request.query_params.get('is_favorited')
        favorites_recipe_ids = Favorites.objects.filter(
            list_owner=user).values_list('recipe_id', flat=True)
        if is_favorited == '1':
            return queryset.filter(id__in=favorites_recipe_ids)
        return queryset.exclude(id__in=favorites_recipe_ids)
