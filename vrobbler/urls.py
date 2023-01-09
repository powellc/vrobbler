from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from scrobbles.views import RecentScrobbleList
from videos import urls as video_urls

from scrobbles import urls as scrobble_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    # path("api-auth/", include("rest_framework.urls")),
    # path("movies/", include(movies, namespace="movies")),
    # path("shows/", include(shows, namespace="shows")),
    path("api/v1/scrobbles/", include(scrobble_urls, namespace="scrobbles")),
    path("", include(video_urls, namespace="videos")),
    path("", RecentScrobbleList.as_view(), name="home"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
