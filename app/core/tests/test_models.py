from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Tag, Ingredient, Recipe, recipe_image_file_path

User = get_user_model()


def sample_user(email="nhattai.nguyen88@gmail.com", password="test123"):
    """Create a simple User"""
    return User.objects.create_user(email, password)


class ModelsTest(TestCase):
    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful"""
        email = "test@gmail.com"
        password = "Testpass123"

        user = User.objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        email = "test@GMAIL.COM"
        user = User.objects.create_user(email, "test123")

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            User.objects.create_user(None, "test123")

    def test_create_new_superuser(self):
        """Test creating  a new superuser"""
        user = User.objects.create_superuser("test@GMAIL.COM", "test123")

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tag string representation"""
        tag = Tag.objects.create(user=sample_user(), name="Vegan")

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Test the ingredient string representation"""
        ingredient = Ingredient.objects.create(
            user=sample_user(), name="Cucumber"
        )

        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """Test the recipe string representation"""
        recipe = Recipe.objects.create(
            user=sample_user(),
            title="Steak and mushroom sauce",
            time_minutes=5,
            price=5.00,
        )

        self.assertEqual(str(recipe), recipe.title)

    @patch("uuid.uuid4")
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test that image is saved in a correct location"""
        uuid = "test-uuid"
        mock_uuid.return_value = uuid
        file_path = recipe_image_file_path(None, "myimage.jpg")

        exp_path = f"uploads/recipe/{uuid}.jpg"
        self.assertEqual(file_path, exp_path)
