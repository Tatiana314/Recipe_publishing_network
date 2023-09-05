from django.db import models
from django.core.validators import MinValueValidator

from users.models import User


RECIPE_DATA = '{name} - {author} - {date:%d.%m.%Y}'


class Tag(models.Model):
    """Модель Тег."""
    name = models.CharField('Название', blank=False, null=False, max_length=200)
    color = models.CharField('Цвет', null=True, max_length=7)
    slug = models.SlugField('Метка', unique=True, max_length=200)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель Ингредиент."""
    name = models.CharField('Название', blank=False, null=False, max_length=200)
    measurement_unit = models.CharField(
        'Ед.измерения', blank=False, null=False, max_length=200
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Модель Рецепт."""
    REQUIRED_FIELDS = [
        'tags',
        'author',
        'ingredients',
        'name',
        'text',
        'cooking_time',
        'image'
    ]
    tags = models.ManyToManyField(Tag)
    author = models.ForeignKey(
        User, verbose_name='Автор', on_delete=models.CASCADE, related_name='recipes'
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиент',
        help_text='Ингредиент, входящий в рецепт',
    )
    name = models.CharField('Название', blank=False, null=False, max_length=200)
    text = models.TextField('Описание')
    cooking_time = models.IntegerField(
        'Время приготовления', default=1, validators=(MinValueValidator(1),)
    )
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/images/',
        null=True,
        default=None
    )

    class Meta:
        ordering = ('pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return RECIPE_DATA.format(
            name=self.name, author=self.author.username, date=self.pub_date
        )


class RecipeIngredient(models.Model):
    """Модель связи id рецепта и id ингредиента."""

    ingredient = models.ForeignKey(Ingredient, verbose_name='Ингредиент', on_delete=models.CASCADE, related_name='ingredients')
    recipe = models.ForeignKey(Recipe, verbose_name='Рецепт', on_delete=models.CASCADE, related_name='recipes')
    amount = models.IntegerField('Кол-во', default=1, validators=(MinValueValidator(1),))

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Рецепт-ингредиент'
        verbose_name_plural = 'Рецепт-ингредиенты'

    def __str__(self):
        return f'{self.ingredient}, {self.recipe}, {self.amount}'


class Cart(models.Model):
    """Модель Корзина."""
    user = models.ForeignKey(
        User, verbose_name='Пользователь', on_delete=models.CASCADE, related_name='carts'
    )
    recipe = models.ForeignKey(
        Recipe, verbose_name='Рецепт', on_delete=models.CASCADE, related_name='recipes_cart', unique=False
    )

    class Meta:
        ordering = ('user',)
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_cart',
                violation_error_message='Рецеп уже находится в списке покупок.'
            )
        ]

    def __str__(self):
        return f'{self.user.username}, {self.recipe.name}'


class Favorite(models.Model):
    """Модель Избраное."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipes_favorite',
        unique=False
    )

    class Meta:
        ordering = ('user',)
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избраные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'
