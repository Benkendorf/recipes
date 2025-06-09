from django.db.models import Count, F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (SAFE_METHODS,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from sqids import Sqids

from recipes.constants import SHORT_LINK_MIN_LENGTH
from recipes.filters import IngredientFilter, RecipeFilter
from recipes.models import Favorites, Ingredient, Recipe, ShoppingCart, Tag
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
    permission_classes = [IsAuthenticatedOrReadOnly, ]

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
            response_serializer.is_valid(raise_exception=True)

            return Response(response_serializer.data)

        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get',],
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

    @action(detail=True, methods=['post', ],
            permission_classes=[IsAuthenticated, ],
            pagination_class=PageNumberPagination,
            url_path='subscribe')
    def subscription(self, request, id):
        if Subscription.objects.filter(
            subscriber=self.request.user,
            subscribed_to=get_object_or_404(UserModel, pk=id)
        ).exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SubscriptionCreateSerializer(
            data={'subscriber': self.request.user.pk,
                  'subscribed_to': id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        serializer_to_return = SubscriptionSerializer(
            instance=get_object_or_404(UserModel, pk=id),
            context={'request': request}
        )

        return Response(
            serializer_to_return.data,
            status=status.HTTP_201_CREATED
        )

    @subscription.mapping.delete
    def subscription_delete(self, request, id):
        if not Subscription.objects.filter(
            subscriber=self.request.user,
            subscribed_to=get_object_or_404(UserModel, pk=id)
        ).delete()[0] == 1:
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )

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
    http_method_names = ['get', 'post', 'patch', 'delete']

    queryset = Recipe.objects.all().select_related('author').prefetch_related(
        'ingredients', 'tags').order_by('-datetime_created')

    permission_classes = [IsAuthenticatedOrReadOnly, ]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user
        )

    def get_serializer_class(self):
        if self.action in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    def userlist_delete(self, request, pk, model):
        if not model.objects.get(
            owner=self.request.user,
            recipe=get_object_or_404(Recipe, pk=pk)
        ).delete()[0] == 1:
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    def userlist_create(self, request, pk, serializer):
        serializer = serializer(
            data={'owner': self.request.user.pk, 'recipe': pk})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        recipe_serializer = ShortRecipeSerializer(
            instance=Recipe.objects.get(pk=pk))

        return Response(
            recipe_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get',], url_path='get-link')
    def short_link(self, request, pk):
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

    @action(detail=False, methods=['get',],
            permission_classes=[IsAuthenticated, ],
            url_path='download_shopping_cart')
    def cart_download(self, request):
        cart_q = ShoppingCart.objects.values(
            ing_name=F('recipe__ingredients__name'),
            ing_unit=F('recipe__ingredients__measurement_unit')).annotate(
            ing_amount=Sum(F('recipe__recipe_ingredients__amount'))
        ).order_by('ing_name')
        response_string = ''
        for ing in cart_q:
            response_string += (f'{ing["ing_name"]} - {ing["ing_amount"]}'
                                f' {ing["ing_unit"]}' + '\n')
        response = HttpResponse(response_string, content_type='text/plain')
        return response

    @action(detail=True, methods=['post', ],
            permission_classes=[IsAuthenticated, ], url_path='shopping_cart')
    def shopping_cart(self, request, pk):
        return self.userlist_create(request, pk, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        return self.userlist_delete(request, pk, ShoppingCart)

    @action(detail=True, methods=['post', ],
            permission_classes=[IsAuthenticated, ], url_path='favorite')
    def favorites(self, request, pk):
        return self.userlist_create(request, pk, FavoritesSerializer)

    @favorites.mapping.delete
    def delete_favorite(self, request, pk):
        return self.userlist_delete(request, pk, Favorites)


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
