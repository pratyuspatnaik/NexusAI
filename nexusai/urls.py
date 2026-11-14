from django.urls import include, path

from core.views import home, serve_asset

urlpatterns = [
    path("", home, name="home"),
    path("style.css", serve_asset, {"filename": "style.css"}, name="style"),
    path("script.js", serve_asset, {"filename": "script.js"}, name="script"),
    path("api/", include("core.urls")),
]
