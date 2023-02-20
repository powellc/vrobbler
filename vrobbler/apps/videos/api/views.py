from rest_framework import permissions, viewsets

from videos.api.serializers import (
    SeriesSerializer,
    VideoSerializer,
)
from videos.models import Series, Video


class SeriesViewSet(viewsets.ModelViewSet):
    queryset = Series.objects.all().order_by('-created')
    serializer_class = SeriesSerializer
    permission_classes = [permissions.IsAuthenticated]


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all().order_by('-created')
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticated]
