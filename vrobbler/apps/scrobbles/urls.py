from django.urls import path
from scrobbles import views

app_name = 'scrobbles'

urlpatterns = [
    path('', views.scrobble_endpoint, name='api-list'),
    path('finish/<slug:uuid>', views.scrobble_finish, name='finish'),
    path('cancel/<slug:uuid>', views.scrobble_cancel, name='cancel'),
    path('jellyfin/', views.jellyfin_websocket, name='jellyfin-websocket'),
    path('mopidy/', views.mopidy_websocket, name='mopidy-websocket'),
]
