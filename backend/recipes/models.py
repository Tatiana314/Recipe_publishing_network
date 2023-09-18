from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator

from foodgram.settings import AUTH_USER_MODEL


RECIPE_DATA = '{name} - {author} - {date:%d.%m.%Y}'
SUBSCRIPTIONS_DATA = '{user} подписан на {author}'
USER_DATA = '{username} - {email} - {first_name} {last_name}'


class User(AbstractUser):
    """Модель Пользователя."""
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]
    email = models.EmailField(
        unique=True, max_length=254, blank=False, null=False
    )
    first_name = models.CharField(
        'Имя', blank=False, null=False, max_length=150
    )
    last_name = models.CharField(
        'Фамилия', blank=False, null=False, max_length=150
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return USER_DATA.format(
            username=self.username,
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name
        )


class Subscription(models.Model):
    """Модель Подписки."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        unique=False,
        related_name='subscribing',
        verbose_name='Автор',
    )

    class Meta:
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return SUBSCRIPTIONS_DATA.format(
            user=self.user.username,
            author=self.author.username
        )


class Tag(models.Model):
    """Модель Тег."""
    name = models.CharField(
        'Название', blank=False, null=False, max_length=200
    )
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
    name = models.CharField(
    'Название', blank=False, null=False, max_length=200
)
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
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиент',
        help_text='Ингредиент, входящий в рецепт',
    )
    name = models.CharField(
        'Название', blank=False, null=False, max_length=200
    )
    text = models.TextField('Описание')
    cooking_time = models.IntegerField(
        'Время приготовления',
        blank=False, null=False, default=1, validators=(MinValueValidator(1),)
    )
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/images/',
        null=True,
        default=None
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return RECIPE_DATA.format(
            name=self.name, author=self.author.username, date=self.pub_date
        )


class RecipeIngredient(models.Model):
    """Модель связи id рецепта и id ингредиента."""

    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        related_name='ingredients'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    amount = models.IntegerField(
        verbose_name='Кол-во',
        default=1,
        validators=(MinValueValidator(1),)
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Рецепт-ингредиент'
        verbose_name_plural = 'Рецепт-ингредиенты'

    def __str__(self):
        return f'{self.ingredient}, {self.recipe}, {self.amount}'


class CreatedModel(models.Model):
    """Абстрактная модель."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s',
        unique=False,
        verbose_name='Рецепт',
    )
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Пользователь',
    )

    class Meta:
        abstract = True
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s',
                violation_error_message='Рецеп уже находится в списке %(class)s.'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Cart(CreatedModel):
    """Модель Корзина."""

    class Meta(CreatedModel.Meta):
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'


class Favorite(CreatedModel):
    """Модель Избраное."""

    class Meta(CreatedModel.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избраные рецепты'
