import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse("recipe:recipe-list")
User = get_user_model()


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def sample_tag(user, name="Main Course"):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name="Cinnamon"):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        "title": "Sample recipe",
        "time_minutes": 10,
        "price": 5.00,
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipesApiTests(TestCase):
    """Test the publicly available recipe API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving recipes"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipesApiTests(TestCase):
    """Test the authorized user recipe API"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@gmail.com", password="test123"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test that recipes returned are for the authenticated user"""
        user_2 = User.objects.create_user(
            email="other@gmail.com",
            password="qwerty123",
        )
        sample_recipe(user=user_2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            "title": "Chocolate cheesecake",
            "time_minutes": 30,
            "price": 5.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating recipe with tags"""
        tag_1 = sample_tag(user=self.user, name="Vegan")
        tag_2 = sample_tag(user=self.user, name="Dessert")

        payload = {
            "title": "Avocado lime cheesecake",
            "tags": [tag_1.id, tag_2.id],
            "time_minutes": 60,
            "price": 20.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag_1, tags)
        self.assertIn(tag_2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating recipe with ingredients"""
        ingredient_1 = sample_ingredient(user=self.user, name="Prawns")
        ingredient_2 = sample_ingredient(user=self.user, name="Ginger")

        payload = {
            "title": "Thai prawn red curry",
            "ingredients": [ingredient_1.id, ingredient_2.id],
            "time_minutes": 20,
            "price": 7.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient_1, ingredients)
        self.assertIn(ingredient_2, ingredients)

    def test_partial_update_recipe(self):
        """Test update a recipe with patch"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name="Curry")

        payload = {
            "title": "Chicken tikka",
            "tags": [new_tag.id],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])

        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test update a recipe with put"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {
            "title": "Spaghetti carbonara",
            "time_minutes": 25,
            "price": 5.00,
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.time_minutes, payload["time_minutes"])
        self.assertEqual(recipe.price, payload["price"])

        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)

    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""
        recipe_1 = sample_recipe(user=self.user, title="Thai vegetable curry")
        recipe_2 = sample_recipe(user=self.user, title="Aubergine with tahini")
        tag_1 = sample_tag(user=self.user, name="Vegan")
        tag_2 = sample_tag(user=self.user, name="Vegetarian")
        recipe_1.tags.add(tag_1)
        recipe_2.tags.add(tag_2)
        recipe_3 = sample_recipe(user=self.user, title="Fish and chip")

        res = self.client.get(
            RECIPES_URL,
            {"tags": f"{tag_1.id},{tag_2.id}"},
        )
        serializer_1 = RecipeSerializer(recipe_1)
        serializer_2 = RecipeSerializer(recipe_2)
        serializer_3 = RecipeSerializer(recipe_3)

        self.assertIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """Test returning recipes with specific ingredients"""
        recipe_1 = sample_recipe(user=self.user, title="Posh beans on toast")
        recipe_2 = sample_recipe(user=self.user, title="Chicken cacciatore")
        ingredient_1 = sample_ingredient(user=self.user, name="Feta cheese")
        ingredient_2 = sample_ingredient(user=self.user, name="Chicken")
        recipe_1.ingredients.add(ingredient_1)
        recipe_2.ingredients.add(ingredient_2)
        recipe_3 = sample_recipe(user=self.user, title="Steak and mushrooms")

        res = self.client.get(
            RECIPES_URL,
            {"ingredients": f"{ingredient_1.id},{ingredient_2.id}"},
        )
        serializer_1 = RecipeSerializer(recipe_1)
        serializer_2 = RecipeSerializer(recipe_2)
        serializer_3 = RecipeSerializer(recipe_3)

        self.assertIn(serializer_1.data, res.data)
        self.assertIn(serializer_2.data, res.data)
        self.assertNotIn(serializer_3.data, res.data)


class RecipeImageUploadTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@gmail.com", password="test123"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading an image to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            # Create a black square of 10 pixels
            img = Image.new("RGB", (10, 10))
            # Save the image to ntf file as JPEG
            img.save(ntf, format="JPEG")
            # Reset the pointer to the begin of the file so the reading
            # cannot be blank
            ntf.seek(0)
            # multipart form request includes file data instead only JSON
            # as default
            res = self.client.post(
                url,
                {"image": ntf},
                format="multipart",
            )

            self.recipe.refresh_from_db()
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIn("image", res.data)
            self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
