from django.urls import include, path
from rest_framework.routers import DefaultRouter

#from users.views import UserViewset
from recipes.views import IngredientViewset, RecipeViewset, TagViewset
from users.views import CustomUserViewSet

app_name = 'api'

router = DefaultRouter()

router.register('tags', TagViewset, basename='tag')
router.register('ingredients', IngredientViewset, basename='ingredient')
router.register('recipes', RecipeViewset, basename='recipe')
#router.register('users', UserViewset, basename='user')

urlpatterns = [
    path('users/me/avatar/', CustomUserViewSet.as_view({'put': 'avatar',
                                                        'delete': 'avatar'}), name='avatar'),
    path('', include(router.urls)),
]
