from api.filters import RecipeFilter
from api.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from django.contrib.auth import get_user_model
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngridient,
                            ShoppingCart, Tag)
from users.models import Follow

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .serializers import (FollowSerializer, IngredientSerializer,
                          PasswordSerializer, RecipeListCreateSerializer,
                          RecipeRetrieveUpdate, RecipeShortSerializer,
                          ShoppingCartSerializer, TagSerializer,
                          UserCreateSerializer, UserSerializer,
                          SubscriptionsSerializer)

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    """
    ViewSet модели Tag.
    Предоставляет только действия list() и retrieve().
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    ViewSet модели Ingredient.
    Предоставляет только действия list() и retrieve().
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ("name",)


class UserViewSet(UserViewSet):
    """
    ViewSet модели User.
    Полный набор действий.
    """

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer()
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action == "set_password":
            return PasswordSerializer
        if self.action == "subscriptions":
            return FollowSerializer
        return UserSerializer

    @action(("get",), detail=False, permission_classes=(IsAuthenticated,))
    def get_current_user(self, request):
        """
        Запрос к эндпоинту /me/.
        Получения информации о текущем пользователе.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(("post",), detail=False, permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        """
        Запрос к эндпоинту /set_password/.
        Изменения пfроля.
        """
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.data.get("new_password"))
        user.save()
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(("get",), detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """
        Запрос к эндпоинту /subscriptions/.
        Получения списка пользователей,
        на которых подписан пользователь.
        """
        subscriptions = Follow.objects.filter(
            follower=request.user,
        ).select_related("following")
        serializer = SubscriptionsSerializer(subscriptions, many=True)
        return Response(serializer.data)


class RecipeViewSet(ModelViewSet):
    """
    ViewSet модели Recipe.
    Поддерживает полный набор действий.
    """

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_class = RecipeFilter()

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return RecipeListCreateSerializer
        return RecipeRetrieveUpdate

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            user = None
        return (
            Recipe.objects.select_related("author")
            .prefetch_related(
                "tags",
                "ingredients",
                "recipe",
                "shopping_cart",
                "favorite_recipe"
            )
            .annotate(
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user, recipe=OuterRef("pk")
                    )
                ),
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=self.request.user, recipe=OuterRef("pk")
                    )
                ),
            )
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(("post",), detail=False, permission_classes=(IsAuthenticated))
    def post_shopping_cart(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        ShoppingCart.objects.create(recipe=recipe, user=request.user)
        serializer = ShoppingCartSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(("delete",), detail=False, permission_classes=(IsAuthenticated))
    def delete_shopping_cart(self, request):
        get_object_or_404(
            ShoppingCart, user=request.user.id, recipe=get_object_or_404(
                Recipe, id=id
            )
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(("post",), detail=False, permission_classes=(IsAuthenticated))
    def post_favorite(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        Favorite.objects.create(recipe=recipe, user=request.user)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(("delete",), detail=False, permission_classes=(IsAuthenticated))
    def delete_favorite(self, request):
        get_object_or_404(
            Favorite, user=request.user, recipe=get_object_or_404(
                Recipe, id=id
            )
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def create_ingredients_file():
        ingredients = (
            RecipeIngridient.objects.all()
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(amount=Sum("amount"))
        )
        shopping_cart = []
        for ingredient in ingredients:
            shopping_cart.append(
                f'{ingredient["ingredient__name"]}'
                f'{ingredient["amount"]} '
                f'{ingredient["ingredient__measurement_unit"]}\n'
            )
        return shopping_cart

    @action(("get",), detail=False, permission_classes=(IsAuthenticated,))
    def download_ingredients(self, request):
        shopping_cart = self.create_ingredients_file()
        response = HttpResponse(shopping_cart, content_type="text/plain")
        response["Content-Disposition"] = (
            'attachment; filename="ingredients.txt"'
        )
        return response
