from rest_framework import serializers
from scrobbles.models import Scrobble, AudioScrobblerTSVImport


class AudioScrobblerTSVImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioScrobblerTSVImport
        fields = ('tsv_file',)


class ScrobbleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scrobble
        fields = "__all__"
