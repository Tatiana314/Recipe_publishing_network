import base64

from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from djoser.conf import settings
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from users.models import User, Subscription
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag, Cart


class CustomUserSerializer(serializers.ModelSerializer):
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


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Ingredient


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        fields = ('amount', 'id')
        model = RecipeIngredient


class AmountIngredientSerializer(serializers.ModelSerializer):
    """Список ингредиентов-количество для рецепта."""
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
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    """Создание/редактирование рецепта."""
    author = CustomUserSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        depth = 1
        exclude = ('pub_date',)
        read_only_fields = ('author',)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            recipe.ingredients.add(ingredient.get('id'), through_defaults={'amount': ingredient.get('amount')})
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        tags = validated_data.pop('tags')
        if tags:
            instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients')
        if ingredients:
            instance.recipes.all().delete()
            for ingredient in ingredients:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    amount=ingredient.get('amount'),
                    ingredient=ingredient.get('id')
                )
        instance.save()
        return instance


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


class SubscribeSerializer(CustomUserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = GetRecipeSerializer(many=True, read_only=True)

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
    

class RecipeInfoSerializer(serializers.ModelSerializer):
    """Краткая информация о рецепте."""
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Cart
        validators = [
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=('user', 'recipe')
            )
        ]
    def to_representation(self, instance):
        return RecipeInfoSerializer(instance.recipe).data


    # def validate(self, data):
    #     if Cart.objects.filter(user=data.get('user'), recipe=data.get('recipe')).exists():
    #         raise serializers.ValidationError(
    #             'Рецеп уже находится в списке покупок.')
    #     return data
    
    # def validate_recipe(self, value):
    #     if self.context['request'].method != 'POST':
    #         return value
    #     if Cart.objects.filter(user=self.context['request'].user, recipe=value).exists():
    #         raise serializers.ValidationError(
    #             'Рецеп уже находится в списке покупок.')
    #     return value


# class SubscribeSerializer(serializers.ModelSerializer):

#     class Meta:
#         fields = '__all__'
#         model = Subscription

#     def validate(self, data):
#         if data.get('username') == self.context['request'].user:
#             raise serializers.ValidationError(
#                 'Пользователь не может подписаться на самого себя.')
#         return data
    
#             """Создаем/удаляет подписку на автора."""
#         author = self.author_object(id=id)
#         if request.method == 'post':
#         author = self.author_object(id=id)
#         if request.user == author:
#             return Response(
#                 {'errors': 'Вы не можете подписаться на себя'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         if Subscription.objects.filter(user=request.user, author=author).exists():
#             return Response(
#                 {'errors': 'Подписка уже существует'},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         Subscription.objects.create(author=author, user=request.user)
#         serializer = CustomUserSerializer(author, context={'request': request})
#         return Response(serializer.data, status=status.HTTP_200_OK)

    

#     def validate(self, data):
#     """Валидация username в API"""
#     username = data.get('username')
#     if username and not re.match(r'^[\w.@+-]+$', username):
#         raise serializers.ValidationError(
#             'Поле username не соответствует паттерну',
#         )
#     if data.get('username') == 'me':
#         raise serializers.ValidationError('Использовать имя me запрещено')
#     return data
        
        #('id', 'email', 'username', 'first_name', 'last_name')
    
    # def validate(self, data):
    #     validate(self, data)
    #     return super().validate(data)


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = (
#             'id', 'email', 'username', 'first_name', 'last_name'
#         )


# class UserCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = (
#             'email', 'username', 'first_name', 'last_name', 'password'
#         )


# class SetPasswordSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = (
#             'id',
#             'email',
#             'username',
#             'first_name',
#             'last_name',
#             'password',
#         )
#         read_only_fields = (
#             'id',
#             'email',
#             'username',
#             'first_name',
#             'last_name',
#         )

#     def validate(self, data):
#         """Валидация password в API."""
#         password = data.get('password')
#         if password and not re.match(r'^[\w.@+-]+$', username):
#             raise serializers.ValidationError(
#                 'Поле username не соответствует паттерну',
#             )
#         if data.get('username') == 'me':
#             raise serializers.ValidationError('Использовать имя me запрещено')
#         return data
