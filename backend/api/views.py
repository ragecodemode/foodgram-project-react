from api.filters import RecipeFilter
from api.permissions import IsAuthorOrReadOnly

from django.db.models import Sum
from django.db import IntegrityError
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngridient,
                            ShoppingCart, Tag)
from users.models import Follow

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .serializers import (SubscriptionsSerializer, IngredientSerializer,
                          PasswordSerializer, RecipeListCreateSerializer,
                          RecipeRetrieveUpdate, RecipeShortSerializer,
                          ShoppingCartSerializer, TagSerializer,
                          UserCreateSerializer, UserSerializer)

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
            return SubscriptionsSerializer
        return UserSerializer

    @action(("get",), detail=False, permission_classes=(IsAuthenticated,))
    def get_current_user(self, request):
        """
        Запрос к эндпоинту /me/.
        Получения информации о текущем пользователе.
        """
        self.get_object = self.request.user
        return self.retrieve(request)

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

    @action(('post',), detail=False, permission_classes=(IsAuthenticated,))
    def post_follow(self, request, id):
        following_user = get_object_or_404(User, id=id)
        if User.objects.filter(
                user=request.user, following_user=following_user
                ):
            raise ParseError(
                'Вы уже подписаны, подписываться на самого себя нельзя!'
            )
        else:
            Follow.objects.create(
                follower=request.user, following=following_user
            )
        serializer = SubscriptionsSerializer(following_user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(('delete',), detail=False, permission_classes=(IsAuthenticated,))
    def delete_follow(self, request, id):
        following_user = get_object_or_404(User, id=id)
        follow = Follow.objects.filter(
            follower=request.user, following_user=following_user
        )
        if not follow:
            raise ParseError(
                'Вы не подписаны на этого пользователя!'
            )
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(("get",), detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """
        Запрос к эндпоинту /subscriptions/.
        Получения списка пользователей,
        на которых подписан пользователь.
        """
        subscriptions = self.list(request).filter(follower=self.request.user)
        return Response(subscriptions)


class RecipeViewSet(ModelViewSet):
    """
    ViewSet модели Recipe.
    Поддерживает полный набор действий.
    """
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filterset_class = RecipeFilter()

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return RecipeListCreateSerializer
        return RecipeRetrieveUpdate

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

    @action(detail=True, methods=("post",), permission_classes=(IsAuthenticated,))
    def post_favorite(self, request, recipe, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        try:
            Favorite.objects.create(recipe=recipe, user=request.user)
        except IntegrityError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=("delete",), permission_classes=(IsAuthenticated,))
    def delete_favorite(self, request, recipe, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        try:
            favorite = Favorite.objects.get(recipe=recipe, user=request.user).exists()
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # @action(detail=True, methods=("post", "delete",), permission_classes=(IsAuthenticated,))
    # def favorite(self, request, pk=None):
    #     recipe = get_object_or_404(Recipe, pk=pk)
    #     if request.method == "GET":
    #         return self.post_favorite(request, recipe)
    #     return self.delete_favorite(request, recipe)

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

    @action(detail=True, methods=["get"], permission_classes=(IsAuthenticated,))
    def download_ingredients(self, request):
        shopping_cart = self.create_ingredients_file()
        response = FileResponse(shopping_cart, content_type="text/plain")
        response["Content-Disposition"] = (
            'attachment; filename="ingredients.txt"'
        )
        return response
