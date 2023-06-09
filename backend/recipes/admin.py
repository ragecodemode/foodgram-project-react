from django.contrib import admin

from .models import Tag, Recipe, Ingredient, RecipeIngridient, Favorite, ShoppingCart


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('author', 'name', 'favorite_count', 'text','cooking_time')
    search_fields = ('author', 'name', 'tag')
    empty_value_display = '-пусто-'


    def favorite_count(self, obj):
        return obj.favorite_recipe.count()


@admin.register(Ingredient)  
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    empty_value_display = '-пусто-'



admin.site.register(Tag)
admin.site.register(RecipeIngridient)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
