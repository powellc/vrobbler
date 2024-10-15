from django.urls import path
from scrobbles import views
from tasks.webhooks import todoist_webhook

app_name = "scrobbles"

urlpatterns = [
    path("status/", views.ScrobbleStatusView.as_view(), name="status"),
    path(
        "manual/lookup/",
        views.ManualScrobbleView.as_view(),
        name="lookup-manual-scrobble",
    ),
    path(
        "long-play-finish/<slug:uuid>/",
        views.scrobble_longplay_finish,
        name="longplay-finish",
    ),
    path(
        "upload/audioscrobbler/",
        views.AudioScrobblerImportCreateView.as_view(),
        name="audioscrobbler-file-upload",
    ),
    path(
        "upload/koreader/",
        views.KoReaderImportCreateView.as_view(),
        name="koreader-file-upload",
    ),
    path(
        "lastfm-import/",
        views.lastfm_import,
        name="lastfm-import",
    ),
    path(
        "webhook/gps/",
        views.gps_webhook,
        name="gps-webhook",
    ),
    path(
        "webhook/jellyfin/",
        views.jellyfin_webhook,
        name="jellyfin-webhook",
    ),
    path(
        "webhook/mopidy/",
        views.mopidy_webhook,
        name="mopidy-webhook",
    ),
    path("webhook/todoist/", todoist_webhook, name="todoist-webhook"),
    path("export/", views.export, name="export"),
    path(
        "imports/",
        views.ScrobbleImportListView.as_view(),
        name="import-detail",
    ),
    path(
        "imports/tsv/<slug:slug>/",
        views.ScrobbleTSVImportDetailView.as_view(),
        name="tsv-import-detail",
    ),
    path(
        "imports/lastfm/<slug:slug>/",
        views.ScrobbleLastFMImportDetailView.as_view(),
        name="lastfm-import-detail",
    ),
    path(
        "imports/koreader/<slug:slug>/",
        views.ScrobbleKoReaderImportDetailView.as_view(),
        name="koreader-import-detail",
    ),
    path(
        "imports/retroarch/<slug:slug>/",
        views.ScrobbleRetroarchImportDetailView.as_view(),
        name="retroarch-import-detail",
    ),
    path(
        "charts/",
        views.ChartRecordView.as_view(),
        name="charts-home",
    ),
    path(
        "long-plays/",
        views.ScrobbleLongPlaysView.as_view(),
        name="long-plays",
    ),
    path("<slug:uuid>/start/", views.scrobble_start, name="start"),
    path("<slug:uuid>/finish/", views.scrobble_finish, name="finish"),
    path("<slug:uuid>/cancel/", views.scrobble_cancel, name="cancel"),
]
