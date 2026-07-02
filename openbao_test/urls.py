from django.urls import path
from . import views
from .logout import full_logout

urlpatterns = [
    path("", views.secret_updater, name="secret_updater"),
    path("legacy", views.placeholder, name="placeholder"),
    path("logout/", full_logout, name="logout_all"),
]