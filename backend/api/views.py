from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend

from djoser.views import UserViewSet

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import filters, viewsets, status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)

from users.models import Subscription
from recipes.models import (
    Ingredient,
    Recipe,
    Tag,
    Cart,
    RecipeIngredient,
    Favorite
)
from .filters import RecipeFilter
from .tabl import pdf_file_table
from .permissions import AuthorOrReadOnly
from .serializers import (
    CustomUserSerializer,
    GetRecipeSerializer,
    IngredientSerializer,
    RecipeInfoSerializer,
    CreateUpdateRecipeSerializer,
    SubscribeSerializer,
    TagSerializer,
)
from users.models import User, Subscription


class CustomUserViewSet(UserViewSet):
    """Получаем/создаем пользователей."""
    serializer_class = CustomUserSerializer
    permission_classes = (AllowAny,)
    http_method_names = ('get', 'post', 'delete')
    queryset = User.objects.all()

    @action(
            permission_classes=(IsAuthenticated,),
            detail=False
        )
    def me(self, request):
        """Обрабатывает GET запрос users/me"""
        serializer = self.get_serializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
            permission_classes=(IsAuthenticated,),
            detail=False
        )
    def subscriptions(self, request):
        """Обрабатывает GET запрос users/subscriptions."""
        serializer = SubscribeSerializer(
            self.paginate_queryset(self.queryset.filter(
                subscribing__user=request.user
            )),
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        permission_classes=(IsAuthenticated,),
        methods=('post',), detail=True
    )
    def subscribe(self, request, id=None):
        """Обрабатывает POST запрос users/subscribe."""
        author = self.get_object()
        user = request.user
        if author == user:
            return Response(
                {'errors': 'Пользователь не может подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Subscription.objects.filter(user=user, author=author).exists():
            return Response(
                {'errors': 'Подписка уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.create(author=author, user=user)
        serializer = SubscribeSerializer(author, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        """Обрабатывает DELETE запрос users/subscribe."""
        subscription = Subscription.objects.filter(
            user=request.user, author=self.get_object()
        )
        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Подписки не существует.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Чтение списка/объекта тег."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Чтение списка/объекта ингредиент."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """CRUD модели - рецепт."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, AuthorOrReadOnly)
    http_method_names = ('get', 'post', 'patch', 'delete', 'create')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return GetRecipeSerializer
        return CreateUpdateRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
            permission_classes=(IsAuthenticated,),
            detail=False
        )
    def download_shopping_cart(self, request):
        """Отдаем файл со списком покупок."""
        ingredients = list(
            RecipeIngredient.objects
            .filter(recipe__recipes_cart__user=request.user)
            .values('ingredient')
            .annotate(result=Sum('amount'))
            .values_list('ingredient__name', 'result',
                         'ingredient__measurement_unit')
        )
        ingredients.insert(0, ('Ингредиент', 'Кол-во', 'Ед. измерения'))
        header_table = 'Список покупок.'
        return pdf_file_table(data=ingredients, header_table=header_table)

    @action(
            permission_classes=(IsAuthenticated,),
            methods=('post',),
            detail=True
        )
    def shopping_cart(self, request, pk=None):
        """Добавляем рецепт в список покупок."""
        recipe = self.get_object() 
        if recipe.recipes_cart.filter(user=request.user).exists():
            return Response(
                {'errors': 'Рецепт уже находиться в корзине.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Cart.objects.create(user=request.user, recipe=self.get_object())
        serializer = RecipeInfoSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удаляем рецепт из списка покупок."""
        recipe = self.get_object()
        if not recipe.recipes_cart.filter(user=request.user).exists():
            return Response(
                {'errors': 'Рецепта нет в корзине.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Cart.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        permission_classes=(IsAuthenticated,),
        methods=('post',), detail=True
    )
    def favorite(self, request, pk=None):
        """Добавляем рецепт в список избранное."""
        recipe = self.get_object() 
        if recipe.recipes_favorite.filter(user=request.user).exists():
            return Response(
                {'errors': 'Рецепт уже находиться в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.create(user=request.user, recipe=self.get_object())
        serializer = RecipeInfoSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Обрабатывает DELETE запрос recipes/favorite."""
        recipe = self.get_object()
        if not recipe.recipes_favorite.filter(user=request.user).exists():
            return Response(
                {'errors': 'Рецепта нет в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe.recipes_favorite.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
