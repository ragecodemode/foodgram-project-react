from rest_framework import filters


class IngredientSearch(filters.BaseFilterBackend):
    """Поиск по вхождению в начало имени ингредиента."""

    def filter_queryset(self, request, queryset, view):
        search_query = request.query_params.get('name')
        starts_with_queryset = queryset.filter(name__istartswith=search_query)
        contains_queryset = queryset.filter(name__icontains=search_query)

        queryset = starts_with_queryset | contains_queryset
        return queryset
