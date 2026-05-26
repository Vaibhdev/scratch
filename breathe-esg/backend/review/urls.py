from django.urls import path
from . import views

urlpatterns = [
    path("records/", views.record_list, name="record-list"),
    path("records/summary/", views.record_summary, name="record-summary"),
    path("records/bulk-action/", views.bulk_review, name="bulk-review"),
    path("records/<uuid:pk>/", views.record_detail, name="record-detail"),
    path("records/<uuid:pk>/review/", views.record_review, name="record-review"),
]
