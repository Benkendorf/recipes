from rest_framework import filters, mixins, viewsets

from .models import Ingredient, Tag
from .serializers import IngredientSerializer, TagSerializer


class TagViewset(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer


class IngredientViewset(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientSerializer