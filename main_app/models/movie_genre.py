from django.db import models

from main_app.models import Base


class MovieGenre(Base):
    movie = models.ForeignKey(
        'Movie', on_delete=models.CASCADE, related_name='movie_genres', related_query_name='movie_genre'
    )
    genre = models.ForeignKey(
        'Genre', on_delete=models.CASCADE, related_name='movie_genres', related_query_name='movie_genre'
    )

    class Meta:
        verbose_name = "MovieGenre"
        verbose_name_plural = "MovieGenres"
