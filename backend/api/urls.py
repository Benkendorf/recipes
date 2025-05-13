from django.urls import include, path
from recipes.views import (FavoritesAPIView, IngredientViewset,
                           RecipeShortLinkAPIView, RecipeViewset,
                           ShoppingCartAPIView, ShoppingCartDownloadAPIView,
                           TagViewset)
from rest_framework.routers import DefaultRouter
from users.views import CustomUserViewSet, SubcriptionAPIView

app_name = 'api'

router = DefaultRouter()

router.register('tags', TagViewset, basename='tag')
router.register('ingredients', IngredientViewset, basename='ingredient')
router.register('recipes', RecipeViewset, basename='recipe')
router.register('users', CustomUserViewSet, basename='user')

urlpatterns = [
    path('users/me/avatar/', CustomUserViewSet.as_view(
        {'put': 'avatar', 'delete': 'avatar'}
    ), name='avatar'),
    path('users/<int:pk>/subscribe/', SubcriptionAPIView.as_view(),
         name='subscribe'),
    path(
        'users/subscriptions/',
        SubcriptionAPIView.as_view(),
        name='subscriptions'
    ),
    path(
        'recipes/download_shopping_cart/',
        ShoppingCartDownloadAPIView.as_view(),
        name='download-shopping-cart'
    ),
    path('', include(router.urls)),
    path(
        'recipes/<int:pk>/get-link/',
        RecipeShortLinkAPIView.as_view(),
        name='recipe-get-link'
    ),
    path(
        'recipes/<int:pk>/favorite/',
        FavoritesAPIView.as_view(),
        name='favorites'
    ),
    path(
        'recipes/<int:pk>/shopping_cart/',
        ShoppingCartAPIView.as_view(),
        name='shopping-cart'
    ),
]
