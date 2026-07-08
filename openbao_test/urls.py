from django.urls import path
from . import views

urlpatterns = [
    path("", views.secret_updater, name="secret_updater"),
    path("legacy", views.placeholder, name="placeholder"),
    path("debug/token/", views.debug_token, name="debug-token"),
]