from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngridient,
                     ShoppingCart, Tag)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('author', 'name', 'favorite_count', 'text', 'cooking_time')
    search_fields = ('author', 'name', 'tag')
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '-пусто-'

    @admin.display(description='В избранном')
    def favorite_count(self, obj):
        return obj.favorites.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    empty_value_display = '-пусто-'


admin.site.register(Tag)
admin.site.register(RecipeIngridient)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
