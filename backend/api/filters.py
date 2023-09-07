from rest_framework import filters


class IngredientSearch(filters.BaseFilterBackend):
    """Поиск по вхождению в начало имени ингредиента."""

    def filter_queryset(self, request, queryset, view):
        search_query = request.query_params.get('name', None)
        if search_query:
            queryset = queryset.filter(name__istartswith=search_query)
        return queryset
