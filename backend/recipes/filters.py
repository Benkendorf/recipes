import logging
import django_filters

from django.db.models import Q

from .models import Recipe, ShoppingCart


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(method='filter_by_tags')
    is_in_shopping_cart = django_filters.CharFilter(method='filter_by_cart')

    class Meta:
        model = Recipe
        fields = ['tags', 'is_in_shopping_cart']

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

        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        cart_recipe_ids = ShoppingCart.objects.filter(cart_owner=user).values_list('recipe_id', flat=True)
        if is_in_shopping_cart == '1':
            return queryset.filter(id__in=cart_recipe_ids)
        return queryset.exclude(id__in=cart_recipe_ids)
