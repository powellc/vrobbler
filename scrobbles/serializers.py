from rest_framework import serializers
from scrobbles.models import Scrobble


class ScrobbleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scrobble
        fields = "__all__"
