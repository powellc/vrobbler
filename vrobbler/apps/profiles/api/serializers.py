from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

from profiles.models import UserProfile


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        exclude = ('password',)


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserProfile
        exclude = ('lastfm_password',)
