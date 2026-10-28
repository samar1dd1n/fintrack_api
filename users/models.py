from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Language(models.TextChoices):
        UZ = 'uz', "O'zbekcha"
        RU = 'ru', 'Русский'
        EN = 'en', 'English'

    email = models.EmailField(unique=True)
    language = models.CharField(
        max_length=2, choices=Language.choices, default=Language.UZ
    )

    def __str__(self):
        return self.username
