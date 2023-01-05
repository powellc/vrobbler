from django.urls import path
from scrobbles import views

app_name = 'scrobbles'

urlpatterns = [
    path('', views.scrobble_endpoint, name='scrobble-list'),
    path('jellyfin/', views.jellyfin_websocket, name='jellyfin-websocket'),
]
