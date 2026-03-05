from django.urls import path
from . import views

app_name = "tests"

urlpatterns = [
    path("", views.test_list, name="list"),
    path("t/<slug:slug>/", views.test_detail, name="detail"),
    path("t/<slug:slug>/result/<int:submission_id>/", views.test_result, name="result"),
]