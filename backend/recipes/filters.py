import django_filters
from django.db.models import Q

from .models import Recipe


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(method='filter_by_tags')

    class Meta:
        model = Recipe
        fields = ['tags']

    def filter_by_tags(self, queryset, name, value):
        tags = self.request.GET.getlist('tags')
        q_objects = Q()
        for tag in tags:
            q_objects |= Q(tags__slug=tag)
        return queryset.filter(q_objects).distinct()
