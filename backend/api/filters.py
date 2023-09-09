from rest_framework.filters import SearchFilter
from recipes.models import Ingredient


class IngredientSearch(SearchFilter):
    """Поиск по вхождению в начало имени ингредиента."""

    # def filter_queryset(self, request, queryset, view):
    #     search_query = request.query_params.get('name')
    #     starts_with_queryset = queryset.filter(name__istartswith=search_query)
    #     contains_queryset = queryset.filter(name__icontains=search_query)

    #     queryset = starts_with_queryset | contains_queryset
    #     return queryset

    # def get_search_fileds(self, view, request):
    #     if request.query_params.get('name'):
    #         return ('^name')
    #     return super().get_search_fields(view, request)

    # search_param = 'name'

    # search_param = 'name'

    class Meta:
        model = Ingredient
        fields = ('name',)
