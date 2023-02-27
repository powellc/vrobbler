from django.urls import path
from scrobbles import views

app_name = 'scrobbles'

urlpatterns = [
    path(
        'manual/imdb/',
        views.ManualScrobbleView.as_view(),
        name='imdb-manual-scrobble',
    ),
    path(
        'manual/audioscrobbler/',
        views.AudioScrobblerImportCreateView.as_view(),
        name='audioscrobbler-file-upload',
    ),
    path(
        'manual/koreader/',
        views.KoReaderImportCreateView.as_view(),
        name='koreader-file-upload',
    ),
    path('finish/<slug:uuid>', views.scrobble_finish, name='finish'),
    path('cancel/<slug:uuid>', views.scrobble_cancel, name='cancel'),
    path(
        'upload/',
        views.AudioScrobblerImportCreateView.as_view(),
        name='audioscrobbler-file-upload',
    ),
    path(
        'lastfm-import/',
        views.lastfm_import,
        name='lastfm-import',
    ),
    path(
        'webhook/jellyfin/',
        views.jellyfin_webhook,
        name='jellyfin-webhook',
    ),
    path(
        'webhook/mopidy/',
        views.mopidy_webhook,
        name='mopidy-webhook',
    ),
    path('export/', views.export, name='export'),
    path(
        'imports/',
        views.ScrobbleImportListView.as_view(),
        name='import-detail',
    ),
    path(
        'imports/tsv/<slug:slug>/',
        views.ScrobbleTSVImportDetailView.as_view(),
        name='tsv-import-detail',
    ),
    path(
        'imports/lastfm/<slug:slug>/',
        views.ScrobbleLastFMImportDetailView.as_view(),
        name='lastfm-import-detail',
    ),
    path(
        'imports/koreader/<slug:slug>/',
        views.ScrobbleKoReaderImportDetailView.as_view(),
        name='koreader-import-detail',
    ),
    path(
        'charts/',
        views.ChartRecordView.as_view(),
        name='charts-home',
    ),
]
