from django.contrib.auth.models import AbstractUser
from django.db import models


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
    first_name = models.CharField('Имя', blank=False, null=False, max_length=150)
    last_name = models.CharField('Фамилия', blank=False, null=False, max_length=150)

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
