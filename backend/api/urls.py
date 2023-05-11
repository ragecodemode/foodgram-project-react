from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    TagViewSet,
    IngredientViewSet,
    FavoriteViewSet,
    ShoppingCartView,
    FavoriteView,
    RecipeViewSet,
    UserViewSet,
    FollowView,
)

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register(r'user', UserViewSet)
router_v1.register(r'tags', TagViewSet)
router_v1.register(r'ingredients', IngredientViewSet)
router_v1.register(r'recipes', RecipeViewSet)


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path("users/<int:id>/subscribe/", FollowView.as_view()),
    path("recipes/<int:id>/favorite/", FavoriteViewSet.as_view()),
    path("users/<int:id>/subscribe/", FavoriteView.as_view()),
    path("recipes/<int:id>/shopping_cart/", ShoppingCartView.as_view()),
    path('', include(router_v1.urls)),
]