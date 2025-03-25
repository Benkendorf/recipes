import logging

from django.conf import settings
from django.shortcuts import redirect

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, mixins, viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from sqids import Sqids

from .constants import SHORT_LINK_MIN_LENGTH
from .filters import RecipeFilter
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
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']
    queryset = Recipe.objects.all().order_by('-datetime_created')
    permission_classes = [IsAuthenticatedOrReadOnly,]

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user
        )

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer


class RecipeShortLinkAPIView(APIView):
    def get(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
            return Response(
                {"short-link": recipe.get_short_link()},
                status=status.HTTP_200_OK
            )
        except Recipe.DoesNotExist:
            return Response(
                {"error": "Рецепт не найден"},
                status=status.HTTP_404_NOT_FOUND
            )


def redirect_short_link(request, code):
    sqids = Sqids(
        min_length=SHORT_LINK_MIN_LENGTH,
    )
    decoded_ids = sqids.decode(code)
    if not decoded_ids:
        return redirect('/')
    recipe_id = decoded_ids[0]
    try:
        recipe = Recipe.objects.get(id=recipe_id)
        return redirect(f'/recipes/{recipe_id}')
    except Recipe.DoesNotExist:
        return redirect('/')
