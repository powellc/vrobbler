from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from scrobbles.views import RecentScrobbleList
from scrobbles import urls as scrobble_urls

# from scrobbles.api.views import ScrobbleViewSet
# from media_types.api.views import (
#    ShowViewSet,
#    MovieViewSet,
# )
from rest_framework import routers

# router = routers.DefaultRouter()
# router.register(r"scrobbles", ScrobbleViewSet)
# router.register(r"shows", ShowViewSet)
# router.register(r"movies", MovieViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    # path("api-auth/", include("rest_framework.urls")),
    # path("movies/", include(movies, namespace="movies")),
    # path("shows/", include(shows, namespace="shows")),
    path("api/v1/scrobbles/", include(scrobble_urls, namespace="scrobbles")),
    path("", RecentScrobbleList.as_view(), name="home"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
