import scrobbles.views as scrobbles_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from vrobbler.apps.books.api.views import AuthorViewSet, BookViewSet
from vrobbler.apps.music import urls as music_urls
from vrobbler.apps.music.api.views import (
    AlbumViewSet,
    ArtistViewSet,
    TrackViewSet,
)
from vrobbler.apps.profiles.api.views import UserProfileViewSet, UserViewSet
from vrobbler.apps.scrobbles import urls as scrobble_urls
from vrobbler.apps.scrobbles.api.views import (
    AudioScrobblerTSVImportViewSet,
    KoReaderImportViewSet,
    LastFmImportViewSet,
    ScrobbleViewSet,
)
from vrobbler.apps.videos import urls as video_urls
from vrobbler.apps.videos.api.views import SeriesViewSet, VideoViewSet

router = routers.DefaultRouter()
router.register(r'scrobbles', ScrobbleViewSet)
router.register(r'lastfm-imports', LastFmImportViewSet)
router.register(r'tsv-imports', AudioScrobblerTSVImportViewSet)
router.register(r'koreader-imports', KoReaderImportViewSet)
router.register(r'artist', ArtistViewSet)
router.register(r'album', AlbumViewSet)
router.register(r'tracks', TrackViewSet)
router.register(r'series', SeriesViewSet)
router.register(r'videos', VideoViewSet)
router.register(r'authors', AuthorViewSet)
router.register(r'books', BookViewSet)
router.register(r'users', UserViewSet)
router.register(r'user_profiles', UserProfileViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/auth', include("rest_framework.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include(music_urls, namespace="music")),
    path("", include(video_urls, namespace="videos")),
    path("", include(scrobble_urls, namespace="scrobbles")),
    path(
        "", scrobbles_views.RecentScrobbleList.as_view(), name="vrobbler-home"
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
