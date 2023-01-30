from django.urls import path
from videos import views

app_name = 'videos'


urlpatterns = [
    # path('', views.scrobble_endpoint, name='scrobble-list'),
    path("movies/", views.MovieListView.as_view(), name='movie_list'),
    path('series/', views.SeriesListView.as_view(), name='series_list'),
    path(
        'series/<slug:slug>/',
        views.SeriesDetailView.as_view(),
        name='series_detail',
    ),
    path(
        'video/<slug:slug>/',
        views.VideoDetailView.as_view(),
        name='video_detail',
    ),
]
