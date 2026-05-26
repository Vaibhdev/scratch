from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.upload_file, name="upload-file"),
    path("ingestions/", views.ingestion_list, name="ingestion-list"),
    path("ingestions/<uuid:pk>/", views.ingestion_detail, name="ingestion-detail"),
]
