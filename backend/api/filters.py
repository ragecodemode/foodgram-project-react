from django_filters import rest_framework as filters

from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    """Фильтр для модели Recipe."""

    author = filters.ModelChoiceFilter(field_name='author__id__in')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart__in',
        label='В корзине.'
    )
    is_favorited = filters.BooleanFilter(
        field_name='is_favorited__in',
        label='В избранных.'
    )
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug',
        label='Ссылка'
    )

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']