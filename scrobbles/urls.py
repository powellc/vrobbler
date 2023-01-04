from django.urls import path
from scrobbles import views

app_name = 'scrobbles'

urlpatterns = [
    path('', views.scrobble_list, name='scrobble-list'),
]
