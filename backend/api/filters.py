from django.core.exceptions import ValidationError
from django_filters import rest_framework as filters
from recipes.models import Recipe, Tag


class TagsMultipleChoiceField(
        filters.fields.MultipleChoiceField):
    def validate(self, value):
        if self.required and not value:
            raise ValidationError(
                self.error_messages['required'],
                code='required')
        for val in value:
            if val in self.choices and not self.valid_value(val):
                raise ValidationError(
                    self.error_messages['invalid_choice'],
                    code='invalid_choice',
                    params={'value': val},)


class TagsFilter(filters.AllValuesMultipleFilter):
    field_class = TagsMultipleChoiceField


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
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']

    def get_favorite(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
