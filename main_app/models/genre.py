from django.db import models

from main_app.models import Base


class Genre(Base):
    title = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Genre"
        verbose_name_plural = "Genres"
