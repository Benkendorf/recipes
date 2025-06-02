from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewset, RecipeViewset, TagViewset,
                    UserModelViewSet)

app_name = 'api'

router = DefaultRouter()

router.register('tags', TagViewset, basename='tag')
router.register('ingredients', IngredientViewset, basename='ingredient')
router.register('recipes', RecipeViewset, basename='recipe')
router.register('users', UserModelViewSet, basename='user')

urlpatterns = [
    path('users/me/avatar/', UserModelViewSet.as_view(
        {'put': 'avatar', 'delete': 'avatar'}
    ), name='avatar'),
    path(
        'users/<int:pk>/subscribe/',
        UserModelViewSet.as_view({
            'post': 'subscription_post_delete',
            'delete': 'subscription_post_delete'}),
        name='subscription_post_delete'
    ),
    path(
        'users/subscriptions/',
        UserModelViewSet.as_view({
            'get': 'subscription_get'}),
        name='subscription_get'
    ),
    path(
        'recipes/download_shopping_cart/',
        RecipeViewset.as_view({'get': 'cart_download'}),
        name='cart-download'
    ),
    path('', include(router.urls)),
    path(
        'recipes/<int:pk>/get-link/',
        RecipeViewset.as_view({'get': 'short_link'}),
        name='recipe-get-link'
    ),
    path(
        'recipes/<int:pk>/favorite/',
        RecipeViewset.as_view({'post': 'favorites',
                               'delete': 'favorites'}),
        name='favorites'
    ),
    path(
        'recipes/<int:pk>/shopping_cart/',
        RecipeViewset.as_view({'post': 'shopping_cart',
                               'delete': 'shopping_cart'}),
        name='shopping-cart'
    ),
]
