from django.shortcuts import render
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from colloquery.web.models import Collection, Collocation, Keyword,  Translation
from colloquery.web.forms import SearchForm


class Mode:
    FORWARD = 'F'
    REVERSE = 'R'
    SOURCESYN = 'S'
    TARGETSYN = 'T'

def index(request):
    searchform = SearchForm()
    return render(request, "index.html", {
        'searchform': searchform,
        'version': settings.VERSION,
    })

def search(request):
    searchform = SearchForm(request.GET)

    if searchform.is_valid():
        mode = searchform.cleaned_data['collection'][0]
        bykeyword = searchform.cleaned_data['bykeyword']
        collection = Collection.objects.get(id=int(searchform.cleaned_data['collection'][1:]))

        #set language
        if mode == Mode.FORWARD:
            sourcelanguage = collection.sourcelanguage
            targetlanguage = collection.targetlanguage
        elif mode == Mode.REVERSE:
            sourcelanguage = collection.targetlanguage
            targetlanguage = collection.sourcelanguage
        elif mode == Mode.SOURCESYN:
            sourcelanguage = targetlanguage = collection.sourcelanguage
        elif mode == Mode.TARGETSYN:
            sourcelanguage = targetlanguage = collection.targetlanguage

        if bykeyword:
            #search by keyword
            pass #TODO
        else:
            #exact search
            #results = Collocation.objects.filter(collection=collection,language=sourcelanguage,text=searchform.cleaned_data['text'].lower()).prefetch_related(Prefetch('translations',queryset=Translation.objects.order_by('prob')))
            pass

        return render(request, "search.html", {
            'searchform': searchform,
            'version': settings.VERSION,
            'results': results,
        })
    else:
        return render(request, "index.html", {
            'searchform': searchform,
            'version': settings.VERSION,
        })

