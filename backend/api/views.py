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

from users.models import Subscription, User
from recipes.models import (
    Ingredient,
    Recipe,
    Tag,
    Cart,
    RecipeIngredient,
    Favorite
)
from .filters import IngredientFilter, RecipeFilter
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


def delete_obj(obj):
    """Удаление объекта."""
    if obj:
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(
        {'errors': 'Объект не существует.'},
        status=status.HTTP_400_BAD_REQUEST
    )


def create_obj(obj, model, data, serializer):
    """Создание объекта."""
    if obj:
        return Response(
            {'errors': 'Объект уже существует.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    model.objects.create(**data)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


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
        """Добавляем автора в подписку."""
        author = self.get_object()
        user = request.user
        if author == user:
            return Response(
                {'errors': 'Пользователь не может подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return create_obj(
            model=Subscription,
            obj=author.subscribing.filter(user=user).exists(),
            serializer=SubscribeSerializer(author, context={'request': request}),
            data={'user': user, 'author': author}
        )

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        """Удаляем автора из подписки."""
        author = self.get_object()
        return delete_obj(author.subscribing.filter(user=request.user))


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
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('name',)
    #filterset_class = IngredientFilter


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
            methods=('post',), detail=True
        )
    def shopping_cart(self, request, pk=None):
        """Добавляем рецепт в список покупок."""
        recipe = self.get_object()
        return create_obj(
            model=Cart,
            obj=recipe.recipes_cart.filter(user=request.user).exists(),
            serializer=RecipeInfoSerializer(recipe),
            data={'user': request.user, 'recipe': recipe}
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удаляем рецепт из списка покупок."""
        recipe = self.get_object()
        return delete_obj(recipe.recipes_cart.filter(user=request.user))

    @action(
        permission_classes=(IsAuthenticated,),
        methods=('post',), detail=True
    )
    def favorite(self, request, pk=None):
        """Добавляем рецепт в список избранное."""
        recipe = self.get_object()
        return create_obj(
            model=Favorite,
            obj=recipe.recipes_favorite.filter(user=request.user).exists(),
            serializer=RecipeInfoSerializer(recipe),
            data={'user': request.user, 'recipe': recipe}
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаляем рецепт из избранного."""
        recipe = self.get_object()
        return delete_obj(recipe.recipes_favorite.filter(user=request.user))
