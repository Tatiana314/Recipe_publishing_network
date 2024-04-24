"""
Настройка сериализации/десереализацией данных.
"""
import base64

from django.core.files.base import ContentFile
from djoser.conf import settings
from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredient, Subscription, Tag, User)
from rest_framework import serializers, status
from rest_framework.settings import api_settings


class CustomUserSerializer(serializers.ModelSerializer):
    """Вывод данных пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = tuple(User.REQUIRED_FIELDS) + (
            settings.USER_ID_FIELD,
            settings.LOGIN_FIELD, 'is_subscribed'
        )
        read_only_fields = (settings.LOGIN_FIELD,)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return False if user.is_anonymous else obj.subscribing.filter(
            user=user
        ).exists()


class RecipeInfoSerializer(serializers.ModelSerializer):
    """Краткая информация о рецепте."""
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe


class SubscribeSerializer(CustomUserSerializer):
    """Список подписки пользователя."""
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = tuple(User.REQUIRED_FIELDS) + (
            settings.USER_ID_FIELD,
            settings.LOGIN_FIELD,
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        recipes_limit = self.context.get('request').query_params.get(
            'recipes_limit', api_settings.PAGE_SIZE
        )
        try:
            recipes_limit = int(self.context.get('request').query_params.get(
                'recipes_limit', api_settings.PAGE_SIZE
            ))
            recipes = obj.recipes.all()[:recipes_limit]
        except ValueError:
            recipes = obj.recipes.all()[:api_settings.PAGE_SIZE]
        return RecipeInfoSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    """Модель Tag."""
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    """Модель Ingredient."""
    class Meta:
        fields = '__all__'
        model = Ingredient


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Поле ингредиенты при создании/редактировании рецепта."""
    id = serializers.IntegerField()

    class Meta:
        fields = ('amount', 'id')
        model = RecipeIngredient

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f'{value} - ингредиента не существует.'
            )
        return value


class AmountIngredientSerializer(serializers.ModelSerializer):
    """Поле ингредиент/кол-во при Get запросе к рецепту."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        fields = (
            'id', 'name',
            'measurement_unit', 'amount'
        )
        model = RecipeIngredient


class Base64ImageField(serializers.ImageField):
    """Сериализатор для картики."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class GetRecipeSerializer(serializers.ModelSerializer):
    """GET, RETRIEVE рецепт."""
    author = CustomUserSerializer()
    ingredients = AmountIngredientSerializer(
        many=True, source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        depth = 1
        fields = tuple(Recipe.REQUIRED_FIELDS) + (
            'id',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return obj.recipes_favorite.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return obj.recipes_cart.filter(user=user).exists()


class CreateUpdateRecipeSerializer(serializers.ModelSerializer):
    """Создание/редактирование рецепта."""
    author = CustomUserSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        depth = 1
        exclude = ('pub_date',)
        read_only_fields = ('author',)

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Необходимо ввести тэг.')
        if len(list(value)) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Необходимо ввести ингредиент.')
        ingredients = [index['id'] for index in value]
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'Ингридиенты не могут повторяться!'
            )
        return value

    def save_tags_ingredients(self, ingredients, recipe):
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient.get('amount')
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.save_tags_ingredients(
            ingredients=ingredients,
            recipe=recipe
        )
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.save_tags_ingredients(
            ingredients=ingredients,
            recipe=instance
        )
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return GetRecipeSerializer(instance, context=context).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Добавление рецепта в избранное."""
    class Meta():
        model = Favorite
        fields = '__all__'

    def validate(self, attrs):
        if Favorite.objects.filter(
            user=attrs['user'], recipe=attrs['recipe']
        ).exists():
            raise serializers.ValidationError(
                detail='Рецепт уже в избранном.',
                code=status.HTTP_400_BAD_REQUEST
            )
        return attrs


class CartSerializer(serializers.ModelSerializer):
    """Добавление рецепта в корзину."""
    class Meta():
        model = Cart
        fields = '__all__'

    def validate(self, attrs):
        if Cart.objects.filter(
            user=attrs['user'], recipe=attrs['recipe']
        ).exists():
            raise serializers.ValidationError(
                detail='Рецепт уже в корзине.',
                code=status.HTTP_400_BAD_REQUEST
            )
        return attrs


class SubscriptionSerializer(serializers.ModelSerializer):
    """Добавление автора в подписки."""
    class Meta():
        model = Subscription
        fields = '__all__'

    def validate(self, attrs):
        user = attrs['user']
        author = attrs['author']
        if author == user:
            raise serializers.ValidationError(
                detail='Запрещена подписка на самого себя.',
                code=status.HTTP_400_BAD_REQUEST
            )
        if Subscription.objects.filter(
            user=user, author=author
        ).exists():
            raise serializers.ValidationError(
                detail='Вы уже подписаны на автора.',
                code=status.HTTP_400_BAD_REQUEST
            )
        return attrs
