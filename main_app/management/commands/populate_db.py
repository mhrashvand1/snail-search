import io
import zipfile
import csv
import requests

from django.core.management.base import BaseCommand
from django.db import transaction

from main_app.models import Movie, Genre, Person, MoviePerson, MovieGenre


class Command(BaseCommand):
    help = "Download, unzip, parse the fake IMDB dataset and bulk-insert into DB."
    DATA_URL = "https://django-statics-2.darkube.app/titandev/imdb_movies_cast_crew.zip"
    BATCH_SIZE = 5000

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting dataset download..."))
        zip_bytes = self.download_dataset()

        self.stdout.write(self.style.NOTICE("Extracting ZIP archive..."))
        with zipfile.ZipFile(zip_bytes) as zf:
            tsv_file_name = [f for f in zf.namelist() if f.endswith(".tsv")][0]
            self.stdout.write(self.style.NOTICE(f"Parsing {tsv_file_name}..."))
            with zf.open(tsv_file_name) as file:
                reader = self.parse_tsv(file)
                self.stdout.write(self.style.NOTICE("Populating database ..."))
                self.populate_db(reader)

        self.stdout.write(self.style.SUCCESS("✅ Done! Dataset prepared successfully."))

    def download_dataset(self):
        response = requests.get(self.DATA_URL, stream=True)
        response.raise_for_status()
        buffer = io.BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            buffer.write(chunk)
        buffer.seek(0)
        self.stdout.write(self.style.SUCCESS("Download complete (in memory)."))
        return buffer

    def parse_tsv(self, file_obj):
        text_stream = io.TextIOWrapper(file_obj, encoding="utf-8")
        return csv.DictReader(text_stream, delimiter="\t")

    def populate_db(self, reader):
        MoviePerson.objects.all().delete()
        MovieGenre.objects.all().delete()
        Movie.objects.all().delete()

        all_genres = set()
        all_persons = set()
        imdb_ids = []
        movies_payload = []

        for row in reader:
            imdb_id = row.get("tconst")
            if not imdb_id:
                continue

            imdb_ids.append(imdb_id)

            title = row.get("originalTitle") or ""
            title_en = row.get("primaryTitle") or ""
            year = self.parse_int(row.get("startYear"))
            runtime_minutes = self.parse_int(row.get("runtimeMinutes"))
            duration = runtime_minutes * 60 if runtime_minutes is not None else None

            genres_name = [g.strip() for g in (row.get("genres") or "").split(",") if g.strip()]
            persons_name = set(
                [p.strip() for p in (row.get("directors_list") or "").split(",") if p.strip()] +
                [p.strip() for p in (row.get("writers_list") or "").split(",") if p.strip()]
            )

            all_genres.update(genres_name)
            all_persons.update(persons_name)

            movies_payload.append(
                {
                    "imdb_id": imdb_id,
                    "title": title,
                    "title_en": title_en,
                    "year": year,
                    "duration": duration,
                    "genres": genres_name,
                    "persons": list(persons_name),
                }
            )

        self.stdout.write(self.style.NOTICE(f"Ensuring {len(all_genres)} genres exist..."))
        existing_genres = Genre.objects.filter(title__in=all_genres)
        existing_titles = set(existing_genres.values_list("title", flat=True))
        missing_genres = [Genre(title=title) for title in all_genres if title not in existing_titles]

        if missing_genres:
            for chunk in self.chunked(missing_genres, self.BATCH_SIZE):
                Genre.objects.bulk_create(chunk, batch_size=self.BATCH_SIZE)

        genres_qs = Genre.objects.filter(title__in=all_genres)
        genre_map = {g.title: g for g in genres_qs}

        self.stdout.write(self.style.NOTICE(f"Ensuring {len(all_persons)} persons exist..."))
        existing_persons = Person.objects.filter(name__in=all_persons)
        existing_names = set(existing_persons.values_list("name", flat=True))
        missing_persons = [Person(name=name) for name in all_persons if name not in existing_names]

        if missing_persons:
            for chunk in self.chunked(missing_persons, self.BATCH_SIZE):
                Person.objects.bulk_create(chunk, batch_size=self.BATCH_SIZE)

        persons_qs = Person.objects.filter(name__in=all_persons)
        person_map = {p.name: p for p in persons_qs}

        self.stdout.write(self.style.NOTICE(f"Creating {len(movies_payload)} Movie objects in bulk..."))
        movie_objs = []
        for payload in movies_payload:
            movie_objs.append(
                Movie(
                    imdb_id=payload["imdb_id"],
                    title=payload["title"],
                    title_en=payload["title_en"],
                    year=payload["year"],
                    duration=payload["duration"],
                )
            )

        with transaction.atomic():
            for chunk in self.chunked(movie_objs, self.BATCH_SIZE):
                Movie.objects.bulk_create(chunk, batch_size=self.BATCH_SIZE)

        created_movies = Movie.objects.filter(imdb_id__in=[p["imdb_id"] for p in movies_payload])
        movie_map = {m.imdb_id: m for m in created_movies}

        self.stdout.write(self.style.NOTICE("Preparing relation objects for bulk insert..."))
        movie_genre_objs = []
        movie_person_objs = []
        for payload in movies_payload:
            movie = movie_map.get(payload["imdb_id"])
            if not movie:
                continue

            for g_title in payload["genres"]:
                genre = genre_map.get(g_title)
                if genre:
                    movie_genre_objs.append(MovieGenre(movie_id=movie.id, genre_id=genre.id))

            for p_name in payload["persons"]:
                person = person_map.get(p_name)
                if person:
                    movie_person_objs.append(MoviePerson(movie_id=movie.id, person_id=person.id))

        self.stdout.write(self.style.NOTICE(f"Bulk inserting {len(movie_genre_objs)} MovieGenre rows..."))
        with transaction.atomic():
            for chunk in self.chunked(movie_genre_objs, self.BATCH_SIZE):
                MovieGenre.objects.bulk_create(chunk, batch_size=self.BATCH_SIZE)

        self.stdout.write(self.style.NOTICE(f"Bulk inserting {len(movie_person_objs)} MoviePerson rows..."))
        with transaction.atomic():
            for chunk in self.chunked(movie_person_objs, self.BATCH_SIZE):
                MoviePerson.objects.bulk_create(chunk, batch_size=self.BATCH_SIZE)

        self.stdout.write(self.style.SUCCESS("Database population via bulk_create complete."))


    def parse_int(self, value):
        try:
            return int(value)
        except:
            return None

    def chunked(self, iterable, size):
        it = iter(iterable)
        while True:
            chunk = []
            try:
                for _ in range(size):
                    chunk.append(next(it))
            except StopIteration:
                if chunk:
                    yield chunk
                break
            yield chunk