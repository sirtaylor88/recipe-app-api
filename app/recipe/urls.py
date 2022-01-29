from django.urls import path, include
from rest_framework.routers import DefaultRouter

from recipe.views import TagViewSet, IngredientViewSet, RecipeViewSet

router = DefaultRouter()

router.register("tags", TagViewSet)
router.register("ingredients", IngredientViewSet)
router.register("recipes", RecipeViewSet)

app_name = "recipe"

urlpatterns = [
    path("", include(router.urls)),
]
