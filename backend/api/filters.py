from django_filters import rest_framework as filter
from recipes.models import Ingredient


class IngredientSearch(filter.FilterSet):
    """Поиск по вхождению в начало имени ингредиента."""

    name = filter.CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = (
            'name',
        )

    def filter_queryset(self, request, queryset, view, value):
        starts_with_queryset = queryset.filter(name__startswith=value)
        contains_queryset = queryset.filter(name__icontains=value)

        sorted_queryset = starts_with_queryset.union(contains_queryset)
        return sorted_queryset
