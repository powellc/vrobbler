from django.urls import path
from music import views

app_name = 'music'


urlpatterns = [
    path('albums/', views.AlbumListView.as_view(), name='albums_list'),
    path(
        'album/<slug:slug>/',
        views.AlbumDetailView.as_view(),
        name='album_detail',
    ),
    path("tracks/", views.TrackListView.as_view(), name='tracks_list'),
    path(
        'tracks/<slug:slug>/',
        views.TrackDetailView.as_view(),
        name='track_detail',
    ),
    path('artists/', views.ArtistListView.as_view(), name='artist_list'),
    path(
        'artists/<slug:slug>/',
        views.ArtistDetailView.as_view(),
        name='artist_detail',
    ),
]
