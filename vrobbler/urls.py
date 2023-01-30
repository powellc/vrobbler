import scrobbles.views as scrobbles_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from scrobbles import urls as scrobble_urls
from music import urls as music_urls
from videos import urls as video_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    # path("api-auth/", include("rest_framework.urls")),
    # path("movies/", include(movies, namespace="movies")),
    # path("shows/", include(shows, namespace="shows")),
    path("api/v1/scrobbles/", include(scrobble_urls, namespace="scrobbles")),
    path(
        'manual/imdb/',
        scrobbles_views.ManualScrobbleView.as_view(),
        name='imdb-manual-scrobble',
    ),
    path("", include(music_urls, namespace="music")),
    path("", include(video_urls, namespace="videos")),
    path("", scrobbles_views.RecentScrobbleList.as_view(), name="home"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
