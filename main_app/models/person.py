from django.db import models

from main_app.models import Base


class Person(Base):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "Persons"

