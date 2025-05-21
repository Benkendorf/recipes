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
from .filters import RecipeFilter
from .models import Favorites, Ingredient, Recipe, ShoppingCart, Tag
from .serializers import (IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, ShortRecipeSerializer,
                          TagSerializer)


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


class RecipeShortLinkAPIView(APIView):
    http_method_names = ['get', 'head']

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
    if Recipe.objects.filter(id=recipe_id).exists():
        return redirect(f'/recipes/{recipe_id}')
    return redirect('/')


class ShoppingCartAPIView(APIView):
    permission_classes = [IsAuthenticated, ]
    http_method_names = ['post', 'head', 'delete']

    def post(self, request, pk):
        if ShoppingCart.objects.filter(
            owner=self.request.user,
            recipe=Recipe.objects.get(pk=pk)
        ).exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            ShoppingCart.objects.create(
                owner=self.request.user,
                recipe=Recipe.objects.get(pk=pk)
            )
            new_cart_recipe = Recipe.objects.get(pk=pk)
            serializer = ShortRecipeSerializer(instance=new_cart_recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

    def delete(self, request, pk):
        if not ShoppingCart.objects.filter(
            owner=self.request.user,
            recipe=get_object_or_404(Recipe, pk=pk)
        ).exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            existing_cart_item = ShoppingCart.objects.filter(
                owner=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)
            )
            existing_cart_item.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )


class ShoppingCartDownloadAPIView(APIView):
    permission_classes = [IsAuthenticated, ]
    http_method_names = ['get', 'head']

    def get(self, request):
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


class FavoritesAPIView(APIView):
    permission_classes = [IsAuthenticated, ]
    http_method_names = ['post', 'head', 'delete']

    def post(self, request, pk):
        if Favorites.objects.filter(
            owner=self.request.user,
            recipe=Recipe.objects.get(pk=pk)
        ).exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            Favorites.objects.create(
                owner=self.request.user,
                recipe=Recipe.objects.get(pk=pk)
            )
            new_list_recipe = Recipe.objects.get(pk=pk)
            serializer = ShortRecipeSerializer(instance=new_list_recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

    def delete(self, request, pk):
        if not Favorites.objects.filter(
            owner=self.request.user,
            recipe=get_object_or_404(Recipe, pk=pk)
        ).exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            existing_list_item = Favorites.objects.filter(
                owner=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)
            )
            existing_list_item.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
