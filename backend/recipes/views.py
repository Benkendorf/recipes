import logging
from rest_framework.decorators import action
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from sqids import Sqids

from .constants import SHORT_LINK_MIN_LENGTH
from .filters import RecipeFilter, IngredientFilter
from .models import Favorites, Ingredient, Recipe, ShoppingCart, Tag
from .serializers import (IngredientSerializer, RecipeCreateSerializer, FavoritesSerializer,
                          RecipeSerializer, ShortRecipeSerializer, ShoppingCartSerializer,
                          TagSerializer)


class BaseDataViewset(viewsets.ReadOnlyModelViewSet):
    pagination_class = None


class TagViewset(BaseDataViewset):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewset(BaseDataViewset):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewset(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']

    queryset = Recipe.objects.all().select_related('author').prefetch_related(
        'ingredients').prefetch_related('tags').order_by('-datetime_created')

    permission_classes = [IsAuthenticatedOrReadOnly, ]
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

    @action(detail=False, methods=['get', 'head'])
    def short_link(self, request, pk):
        if request.method == 'GET':
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

    @action(detail=False, methods=['post', 'delete', 'head'],
            permission_classes=[IsAuthenticated, ])
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                owner=self.request.user,
                recipe=Recipe.objects.get(pk=pk)
            ).exists():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                serializer = ShoppingCartSerializer(
                    data={'owner': self.request.user.pk, 'recipe': pk})
                serializer.is_valid()
                serializer.save()

                recipe_serializer = ShortRecipeSerializer(
                    instance=Recipe.objects.get(pk=pk))

                return Response(
                    recipe_serializer.data,
                    status=status.HTTP_201_CREATED
                )
        elif request.method == 'DELETE':
            if not ShoppingCart.objects.get(
                owner=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)
            ).delete():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    status=status.HTTP_204_NO_CONTENT
                )

    @action(detail=False, methods=['get', 'head'],
            permission_classes=[IsAuthenticated, ])
    def cart_download(self, request):
        if request.method == 'GET':
            cart_recipes = ShoppingCart.objects.filter(
                owner=request.user
            ).values_list('recipe__name',
                        'recipe__ingredients',
                        'recipe__ingredients__name',
                        'recipe__ingredients__measurement_unit',
                        'recipe__recipe_ingredients__amount')

            ing_dict = {}
            for recipe in list(cart_recipes):
                if recipe[1] in ing_dict:
                    ing_dict[recipe[1]]['ing_amount'] += recipe[4]
                else:
                    ing_dict[recipe[1]] = {
                        'ing_name': recipe[2],
                        'ing_unit': recipe[3],
                        'ing_amount': recipe[4],
                    }

            response_string = ''
            for ing in ing_dict.values():
                response_string += (f'{ing["ing_name"]} - {ing["ing_amount"]}'
                                    f' {ing["ing_unit"]}' + '\n')

            response = HttpResponse(response_string, content_type='text/plain')
            return response

    @action(detail=False, methods=['post', 'delete', 'head'],
            permission_classes=[IsAuthenticated, ])
    def favorites(self, request, pk):
        if request.method == 'POST':
            if Favorites.objects.filter(
                owner=self.request.user,
                recipe=Recipe.objects.get(pk=pk)
            ).exists():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                serializer = FavoritesSerializer(
                    data={'owner': self.request.user.pk, 'recipe': pk})
                serializer.is_valid()
                serializer.save()

                recipe_serializer = ShortRecipeSerializer(
                    instance=Recipe.objects.get(pk=pk))

                return Response(
                    recipe_serializer.data,
                    status=status.HTTP_201_CREATED
                )
        elif request.method == 'DELETE':
            if not Favorites.objects.get(
                owner=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)
            ).delete():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    status=status.HTTP_204_NO_CONTENT
                )


def redirect_short_link(request, code):
    sqids = Sqids(
        min_length=SHORT_LINK_MIN_LENGTH,
    )
    decoded_ids = sqids.decode(code)
    if not decoded_ids:
        return redirect('/')
    recipe_id = decoded_ids[0]
    if Recipe.objects.filter(id=recipe_id).exists():
        return redirect(f'/recipes/{recipe_id}')
    return redirect('/')
