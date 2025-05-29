from django.urls import include, path
from recipes.views import (IngredientViewset, RecipeViewset,
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
