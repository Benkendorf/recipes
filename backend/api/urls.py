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
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))
]
