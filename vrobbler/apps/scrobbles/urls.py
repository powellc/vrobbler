from django.urls import path
from scrobbles import views

app_name = 'scrobbles'

urlpatterns = [
    path('finish/<slug:uuid>', views.scrobble_finish, name='finish'),
    path('cancel/<slug:uuid>', views.scrobble_cancel, name='cancel'),
    path(
        'upload/',
        views.AudioScrobblerImportCreateView.as_view(),
        name='audioscrobbler-file-upload',
    ),
    path('lastfm-import/', views.lastfm_import, name='lastfm-import'),
    path('jellyfin/', views.jellyfin_websocket, name='jellyfin-websocket'),
    path('mopidy/', views.mopidy_websocket, name='mopidy-websocket'),
    path('export/', views.export, name='export'),
]
