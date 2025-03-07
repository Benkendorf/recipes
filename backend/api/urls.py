from django.urls import include, path
from rest_framework.routers import DefaultRouter

from recipes.views import IngredientViewset, TagViewset

app_name = 'api'

router = DefaultRouter()

router.register('tags', TagViewset, basename='tag')
router.register('ingredients', IngredientViewset, basename='ingredient')

urlpatterns = [
    path('', include(router.urls)),
]
