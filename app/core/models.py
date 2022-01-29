import uuid
import os
from django.db import models

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

from django.conf import settings


def recipe_image_file_path(instance, filename):
    """Generate file path for new recipe image"""
    ext = filename.split(".")[-1]
    # we use uuid version 4 (random uuid) as unique image filename
    filename = f"{uuid.uuid4()}.{ext}"

    return os.path.join("uploads/recipe/", filename)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create and saves a new user"""
        if not email:
            raise ValueError("User must have an email address")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        # using=None if using default database
        # https://stackoverflow.com/questions/57667334/what-is-the-value-of-self-db-by-default-in-django/57667422
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and save a superuser"""
        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model that supports using email instead of username"""

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"


class Tag(models.Model):
    """Tag to be used for a recipe"""

    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ingredient to be used for a recipe"""

    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Recipe obejct"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)
    # Pass a string instead of a class for a model name so you don't have to
    # order the models if there are dependencies
    ingredients = models.ManyToManyField("Ingredient")
    tags = models.ManyToManyField("Tag")
    image = models.ImageField(null=True, upload_to=recipe_image_file_path)

    def __str__(self):
        return self.title
