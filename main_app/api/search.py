from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F, Value
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView

from main_app.models import Movie


class SearchAPIView(ListAPIView):
    class MovieSerializer(serializers.ModelSerializer):
        genres = serializers.SerializerMethodField()
        persons = serializers.SerializerMethodField()

        def get_genres(self, obj: Movie):
            return obj.genres.all().values_list("title", flat=True)

        def get_persons(self, obj: Movie):
            return obj.persons.all().values_list("name", flat=True)

        class Meta:
            model = Movie
            fields = ("id", "imdb_id", "title", "title_en", "year", "genres", "persons")

    serializer_class = MovieSerializer

    def get_queryset(self):
        search_term = self.request.query_params.get("q", "")
        if len(search_term) < 2:
            raise NotFound()

        return (
            Movie.objects.annotate(
                title_similarity=TrigramSimilarity("title", search_term),
                title_en_similarity=TrigramSimilarity("title_en", search_term),
                genres_similarity=TrigramSimilarity("genres__title", search_term),
                persons_similarity=TrigramSimilarity("persons__name", search_term),
            )
            .annotate(
                score=Coalesce(F("title_similarity"), Value(0.0))
                + Coalesce(F("title_en_similarity"), Value(0.0))
                + Coalesce(F("genres_similarity"), Value(0.0))
                + Coalesce(F("persons_similarity"), Value(0.0))
            )
            .order_by("-score", "-year")
        )
