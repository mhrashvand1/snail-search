from django.db import models

from main_app.models import Base


class MoviePerson(Base):
    movie = models.ForeignKey(
        "Movie", on_delete=models.CASCADE, related_name="movie_persons", related_query_name="movie_person"
    )
    person = models.ForeignKey(
        "Person", on_delete=models.CASCADE, related_name="movie_persons", related_query_name="movie_person"
    )

    class Meta:
        verbose_name = "MoviePerson"
        verbose_name_plural = "MoviePersons"

