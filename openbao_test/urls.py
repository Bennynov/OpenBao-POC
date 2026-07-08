from django.urls import path
from . import views

urlpatterns = [
    path("", views.secret_updater, name="secret_updater"),
    path("legacy", views.placeholder, name="placeholder"),
    path("introspect/", views.introspect_check, name="introspect_check"),
]