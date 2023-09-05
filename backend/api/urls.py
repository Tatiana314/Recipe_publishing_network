from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet, IngredientViewSet, RecipeViewSet, TagViewSet

app_name = 'api'

router_1 = DefaultRouter()
router_1.register('users', CustomUserViewSet, basename='users')
router_1.register('tags', TagViewSet, basename='tags')
router_1.register('ingredients', IngredientViewSet, basename='ingredients')
router_1.register('recipes', RecipeViewSet, basename='recipes')
# router_1.register(
#     r'recipes/(?P<recipe_id>\d+)/shopping_cart', ShoppingCartViewSet, basename='cars'
# )

# router_1.register('groups', GroupViewset, basename='groups')
# router_1.register('follow', FollowViewSet, basename='follows')
#router_1.register(r'users/(?P<user_id>\d+)/subscriptions', SubscriptionsViewSet, basename='subscriptions'
# )

urlpatterns = [
    path('', include((router_1.urls))),
    path('auth/', include('djoser.urls.authtoken')),  # Работа с токенами
]
