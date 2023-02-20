from rest_framework import serializers
from scrobbles.models import (
    AudioScrobblerTSVImport,
    KoReaderImport,
    LastFmImport,
    Scrobble,
)


class ScrobbleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Scrobble
        fields = "__all__"


class KoReaderImportSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = KoReaderImport
        fields = "__all__"


class AudioScrobblerTSVImportSerializer(
    serializers.HyperlinkedModelSerializer
):
    class Meta:
        model = AudioScrobblerTSVImport
        fields = "__all__"


class LastFmImportSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LastFmImport
        fields = "__all__"
