from rest_framework import permissions, viewsets

from music.api.serializers import (
    TrackSerializer,
    ArtistSerializer,
    AlbumSerializer,
)
from music.models import Artist, Album, Track


class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all().order_by('-created')
    serializer_class = ArtistSerializer
    permission_classes = [permissions.IsAuthenticated]


class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all().order_by('-created')
    serializer_class = AlbumSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all().order_by('-created')
    serializer_class = TrackSerializer
    permission_classes = [permissions.IsAuthenticated]
