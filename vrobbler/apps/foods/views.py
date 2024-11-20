from foods.models import Food

from scrobbles.views import ScrobbleableListView, ScrobbleableDetailView


class FoodListView(ScrobbleableListView):
    model = Food


class FoodDetailView(ScrobbleableDetailView):
    model = Food
