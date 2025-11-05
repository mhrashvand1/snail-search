from django.urls import path

from main_app.api.search import SearchAPIView

urlpatterns = [
    path("api/search", SearchAPIView.as_view(), name='search'),
]