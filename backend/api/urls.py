from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet
)


app_name = 'api'


router_1 = DefaultRouter()

router_1.register('users', CustomUserViewSet, basename='users')
router_1.register('tags', TagViewSet, basename='tags')
router_1.register('ingredients', IngredientViewSet, basename='ingredients')
router_1.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include((router_1.urls))),
    path('auth/', include('djoser.urls.authtoken')),  # Работа с токенами
]
