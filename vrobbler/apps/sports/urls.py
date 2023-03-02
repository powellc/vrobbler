from django.urls import path
from sports import views

app_name = 'sports'


urlpatterns = [
    path(
        'sport-events/',
        views.SportEventListView.as_view(),
        name='event_list',
    ),
    path(
        'sport-events/<slug:slug>/',
        views.SportEventDetailView.as_view(),
        name='event_detail',
    ),
]
