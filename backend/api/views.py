from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from djoser.views import UserViewSet
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework import filters, status, viewsets


from recipes.models import Ingredient, Recipe, Tag, Cart, RecipeIngredient
from .permissions import AuthorOrReadOnly
from .serializers import (
    CustomUserSerializer,
    GetRecipeSerializer,
    IngredientSerializer,
    RecipeInfoSerializer,
    RecipeSerializer,
    SubscribeSerializer,
    TagSerializer
)
from django.db.models import Count
from djoser.conf import settings

from users.models import User, Subscription


class CustomUserViewSet(UserViewSet):
    """Получаем/создаем пользователей."""
    serializer_class = CustomUserSerializer
    permission_classes = (AllowAny,)
    http_method_names = ('get', 'post', 'delete')
    queryset = User.objects.all()

    @action(
            permission_classes=(IsAuthenticated,),
            methods=('get',),
            detail=False
        )
    def me(self, request):
        """Обрабатывает GET запрос users/me"""
        serializer = CustomUserSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
            permission_classes=(IsAuthenticated,),
            methods=('get',),
            detail=False
        )
    def subscriptions(self, request):
        result = self.paginate_queryset(User.objects.filter(subscribing__user=request.user))
        serializer = SubscribeSerializer(result, context={'request': request}, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
            permission_classes=(IsAuthenticated,), methods=('post',), detail=True
        )
    def subscribe(self, request, id):
        """Обрабатывает POST запрос users/subscribe."""
        author = self.get_object()
        user = request.user
        subscription = Subscription.objects.filter(
            user=user, author=author
        )
        if subscription:
            return Response(
                {'errors': 'Подписка уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if author == user:
            return Response(
                {'errors': 'Пользователь не может подписаться на самого себя.'},
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


class RecipeViewSet(viewsets.ModelViewSet):
    """CRUD модели - рецепт."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, AuthorOrReadOnly)
    http_method_names = ('get', 'post', 'patch', 'delete', 'create')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return GetRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
            permission_classes=(IsAuthenticated,),
            detail=False
        )
    def download_shopping_cart(self, request):
        """Скачать файл со списком покупок."""
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__recipes_cart__user=request.user)
            .values('ingredient')
            .annotate(result=Sum('amount'))
            .values_list('ingredient__name', 'result',
                         'ingredient__measurement_unit')
        )
        print(ingredients)
        return Response({'recep': "recep"}, status=status.HTTP_200_OK)

    @action(
            permission_classes=(IsAuthenticated,),
            methods=('post',),
            detail=True
        )
    def shopping_cart(self, request, pk):
        """Добавляем рецепт в список покупок."""
        cart = Cart.objects.filter(user=request.user, recipe=self.get_object())
        if cart:
            return Response(
                {'errors': 'Рецеп уже находится в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Cart.objects.create(user=request.user, recipe=self.get_object())
        return Response(RecipeInfoSerializer(self.get_object()).data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """Удаляем рецепт из списка покупок."""
        cart = Cart.objects.filter(user=request.user, recipe=self.get_object())
        if cart:
            cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепта нет в корзину.'},
            status=status.HTTP_400_BAD_REQUEST
        )
