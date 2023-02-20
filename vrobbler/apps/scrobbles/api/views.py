from rest_framework import permissions, viewsets
from scrobbles.api.serializers import (
    AudioScrobblerTSVImportSerializer,
    KoReaderImportSerializer,
    LastFmImportSerializer,
    ScrobbleSerializer,
)
from scrobbles.models import (
    AudioScrobblerTSVImport,
    KoReaderImport,
    Scrobble,
    LastFmImport,
)


class ScrobbleViewSet(viewsets.ModelViewSet):
    queryset = Scrobble.objects.all().order_by('-timestamp')
    serializer_class = ScrobbleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class KoReaderImportViewSet(viewsets.ModelViewSet):
    queryset = KoReaderImport.objects.all().order_by('-created')
    serializer_class = KoReaderImportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class AudioScrobblerTSVImportViewSet(viewsets.ModelViewSet):
    queryset = AudioScrobblerTSVImport.objects.all().order_by('-created')
    serializer_class = AudioScrobblerTSVImportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class LastFmImportViewSet(viewsets.ModelViewSet):
    queryset = LastFmImport.objects.all().order_by('-created')
    serializer_class = LastFmImportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
