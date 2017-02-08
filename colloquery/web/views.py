from django.shortcuts import render
from django.conf import settings

from colloquery.web.forms import SearchForm

def index(request):
    searchform = SearchForm()
    return render(request, "index.html", {
        'searchform': searchform,
        'version': settings.VERSION,
    })
