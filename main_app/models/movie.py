from django.db import models

from main_app.models import Base


class Movie(Base):
    title = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255)
    imdb_id = models.CharField(max_length=10, unique=True)
    year = models.PositiveSmallIntegerField(null=True)
    duration = models.PositiveIntegerField(null=True)
    genres = models.ManyToManyField(
        'Genre',
        through='MovieGenre',
        related_name='movies',
        related_query_name='movie'
    )
    persons = models.ManyToManyField(
        'Person',
        through='MoviePerson',
        related_name='movies',
        related_query_name='movie'
    )


    class Meta:
        verbose_name = "Movie"
        verbose_name_plural = "Movies"

