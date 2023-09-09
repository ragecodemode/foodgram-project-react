from rest_framework.filters import SearchFilter
from recipes.models import Ingredient


class IngredientSearch(SearchFilter):
    """Поиск по вхождению в начало имени ингредиента."""

    class Meta:
        model = Ingredient
        fields = ('name',)
