from django.contrib import admin
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.html import format_html

from . import models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'username', 'email', 'first_name', 'last_name'
    )
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
    empty_value_display = '-пусто-'


@admin.register(models.Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')
    list_editable = ('user', 'author')
    empty_value_display = '-пусто-'


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    list_editable = ('name', 'measurement_unit')
    list_filter = ('name', )
    search_fields = ('name', )


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    list_editable = ('name', 'color', 'slug')
    empty_value_display = '-пусто-'


class RecipeIngredientInline(admin.TabularInline):
    model = models.RecipeIngredient
    min_num = 1


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'author', 'in_favorites', 'consist',
        'cooking_time', 'text', 'image', 'tag'
    )
    readonly_fields = ('in_favorites',)
    list_filter = ('name', 'author', 'tags')
    search_fields = ('name',)
    empty_value_display = '-пусто-'
    inlines = (RecipeIngredientInline,)

    def in_favorites(self, obj):
        count = obj.recipes_favorite.count()
        url = (
            reverse("admin:recipes_favorite_changelist")
            + "?"
            + urlencode({"recipe__id": f"{obj.id}"})
        )
        return format_html('<a href="{}">{} пользователь</a>', url, count)

    in_favorites.short_description = 'В избранном'

    def consist(self, obj):
        count = obj.ingredients.count()
        url = (
            reverse("admin:recipes_recipeingredient_changelist")
            + "?"
            + urlencode({"recipe__id": f"{obj.id}"})
        )
        return format_html('<a href="{}">{} шт.</a>', url, count)

    consist.short_description = 'Ингредиенты'

    def tag(self, obj):
        return list(obj.tags.all())

    tag.short_description = 'Теги'


@admin.register(models.RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    list_editable = ('recipe', 'ingredient', 'amount')


@admin.register(models.Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_editable = ('user', 'recipe')


@admin.register(models.Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
