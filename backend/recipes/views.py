from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, mixins, viewsets

from .models import Ingredient, Recipe, Tag
from .serializers import IngredientSerializer, RecipeSerializer, RecipeCreateSerializer, TagSerializer


class TagViewset(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer

    pagination_class = None


class IngredientViewset(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        return Ingredient.objects.filter(
            name__startswith=self.request.query_params['name']
        ).order_by('name')


class RecipeViewset(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('name')

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user
        )

    def get_serializer_class(self):
        if self.action in ('create', 'update'):
            return RecipeCreateSerializer
        return RecipeSerializer
