from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
from webpages.forms import WebPageReadForm
from webpages.models import WebPage


class WebPageListView(LoginRequiredMixin, generic.ListView):
    model = WebPage
    paginate_by = 20

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(scrobble_count=Count("scrobble"))
            .order_by("-scrobble_count")
        )


class WebPageDetailView(LoginRequiredMixin, generic.DetailView):
    model = WebPage
    slug_field = "uuid"

    def get_context_data(self, **kwargs):
        user = self.request.user
        context_data = super().get_context_data(**kwargs)
        context_data["scrobbles"] = self.object.scrobbles(user)
        return context_data


class WebPageReadView(
    LoginRequiredMixin, generic.edit.FormView, generic.DetailView
):
    model = WebPage
    slug_field = "uuid"
    template_name = "webpages/webpage_read.html"
    form_class = WebPageReadForm

    def get(self, *args, **kwargs):
        user = self.request.user
        webpage = WebPage.objects.get(uuid=kwargs.get("slug"))
        latest_scrobble = webpage.scrobbles(user).last()
        if latest_scrobble.played_to_completion:
            redirect(
                reverse(
                    "webpages:webpage-detail", kwargs={"slug": webpage.uuid}
                )
            )
        return super().get(*args, **kwargs)

    def form_valid(self, *args):
        user = self.request.user
        webpage = WebPage.objects.get(uuid=self.kwargs.get("slug"))
        latest_scrobble = webpage.scrobbles(user).last()
        if not latest_scrobble.played_to_completion:

            latest_scrobble.stop()

            latest_scrobble.log["notes"] = self.request.POST.get("notes")
            latest_scrobble.save(update_fields=["log"])

        return HttpResponseRedirect(webpage.url)
