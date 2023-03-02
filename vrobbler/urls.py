from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

import vrobbler.apps.scrobbles.views as scrobbles_views
from vrobbler.apps.books.api.views import AuthorViewSet, BookViewSet
from vrobbler.apps.music import urls as music_urls
from vrobbler.apps.sports import urls as sports_urls
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
from vrobbler.apps.sports.api.views import (
    LeagueViewSet,
    PlayerViewSet,
    SeasonViewSet,
    SportEventViewSet,
    SportViewSet,
    TeamViewSet,
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
router.register(r'leagues', LeagueViewSet)
router.register(r'sports', SportViewSet)
router.register(r'seasons', SeasonViewSet)
router.register(r'players', PlayerViewSet)
router.register(r'sport-events', SportEventViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'users', UserViewSet)
router.register(r'user_profiles', UserProfileViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/auth', include("rest_framework.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include(music_urls, namespace="music")),
    path("", include(video_urls, namespace="videos")),
    path("", include(sports_urls, namespace="sports")),
    path("", include(scrobble_urls, namespace="scrobbles")),
    path(
        "", scrobbles_views.RecentScrobbleList.as_view(), name="vrobbler-home"
    ),
]
