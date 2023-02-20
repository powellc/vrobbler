from django.contrib.auth import get_user_model

from rest_framework import permissions, viewsets

from profiles.api.serializers import UserSerializer, UserProfileSerializer
from profiles.models import UserProfile

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = UserProfile.objects.all().order_by('-created')
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
