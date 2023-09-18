"""
Настройка сериализации/десереализацией данных.
"""
import base64

from django.core.files.base import ContentFile

from djoser.conf import settings

from rest_framework import serializers

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag, User


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
        if user.is_anonymous:
            return False
        return obj.subscribing.filter(user=user).exists()


class RecipeInfoSerializer(serializers.ModelSerializer):
    """Краткая информация о рецепте."""
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe


class SubscribeSerializer(CustomUserSerializer):
    """Список подписки пользователя."""
    recipes_count = serializers.SerializerMethodField()
    recipes = RecipeInfoSerializer(many=True, read_only=True)

    class Meta(CustomUserSerializer.Meta):
        fields = tuple(User.REQUIRED_FIELDS) + (
            settings.USER_ID_FIELD,
            settings.LOGIN_FIELD,
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


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
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        fields = ('amount', 'id')
        model = RecipeIngredient


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
    ingredients = AmountIngredientSerializer(many=True, source='recipes')
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
    ingredients = RecipeIngredientSerializer(many=True, source='recipes')
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        depth = 1
        exclude = ('pub_date',)
        read_only_fields = ('author',)

    def create(self, validated_data):
        ingredients = validated_data.pop('recipes')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            recipe.ingredients.add(
                ingredient.get('id'),
                through_defaults={'amount': ingredient.get('amount')}
            )
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        if 'tags' in validated_data:
            instance.tags.set(validated_data.pop('tags'))
        if 'recipes' in validated_data:
            ingredients = validated_data.pop('recipes')
            instance.recipes.all().delete()
            for ingredient in ingredients:
                instance.ingredients.add(
                    ingredient.get('id'),
                    through_defaults={'amount': ingredient.get('amount')}
                )
        instance.save()
        return instance
