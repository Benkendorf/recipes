import logging

from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.constants import SHORT_LINK_MIN_LENGTH
from recipes.filters import IngredientFilter, RecipeFilter
from recipes.models import Favorites, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from sqids import Sqids
from users.models import Subscription, UserModel

from .serializers import (AvatarSerializer, FavoritesSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          ShortRecipeSerializer, SubscriptionCreateSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserSerializer)


class UserModelViewSet(UserViewSet):
    queryset = UserModel.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [AllowAny, ]

    @action(detail=False, methods=['put', 'delete'],
            permission_classes=[IsAuthenticated, ], url_path='me/avatar')
    def avatar(self, request):
        user = self.get_instance()
        serializer = AvatarSerializer(data=request.data)
        if request.method == 'PUT':
            serializer.is_valid(raise_exception=True)

            user.avatar = serializer.validated_data['avatar']
            user.save()
            response_serializer = AvatarSerializer(
                data={'avatar': user.avatar}
            )
            response_serializer.is_valid()

            return Response(response_serializer.data)

        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get', 'head'],
            permission_classes=[IsAuthenticated, ],
            pagination_class=PageNumberPagination,
            url_path='subscriptions')
    def subscription_get(self, request):

        if request.method == 'GET':
            subs = UserModel.objects.filter(
                follows__subscriber=request.user
            ).distinct().order_by('username').annotate(
                recipes_count=Count('recipes'))

            paginator = self.pagination_class()
            page = paginator.paginate_queryset(subs, request)

            serializer = SubscriptionSerializer(
                instance=page,
                many=True,
                context={'request': request}
            )

            return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'head', 'delete'],
            permission_classes=[IsAuthenticated, ],
            pagination_class=PageNumberPagination,
            url_path='subscribe')
    def subscription_post_delete(self, request, id):

        if request.method == 'POST':
            if self.request.user.pk == id or Subscription.objects.filter(
                subscriber=self.request.user,
                subscribed_to=UserModel.objects.get(pk=id)
            ).exists():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                serializer = SubscriptionCreateSerializer(
                    data={'subscriber': self.request.user.pk,
                          'subscribed_to': id}
                )
                serializer.is_valid()
                logging.debug(serializer.errors)
                serializer.save()

                serializer_to_return = SubscriptionSerializer(
                    instance=UserModel.objects.get(pk=id),
                    context={'request': request}
                )

                return Response(
                    serializer_to_return.data,
                    status=status.HTTP_201_CREATED
                )

        elif request.method == 'DELETE':
            if not Subscription.objects.filter(
                subscriber=self.request.user,
                subscribed_to=UserModel.objects.get(pk=id)
            ).delete():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    status=status.HTTP_204_NO_CONTENT
                )


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

    @action(detail=True, methods=['get', 'head'], url_path='get-link')
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

    @action(detail=True, methods=['post', 'delete', 'head'],
            permission_classes=[IsAuthenticated, ], url_path='shopping_cart')
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
            permission_classes=[IsAuthenticated, ],
            url_path='download_shopping_cart')
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

    @action(detail=True, methods=['post', 'delete', 'head'],
            permission_classes=[IsAuthenticated, ], url_path='favorite')
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
