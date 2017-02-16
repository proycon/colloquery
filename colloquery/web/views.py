from django.shortcuts import render
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from colloquery.web.models import Collection, Collocation, Translation
from colloquery.web.forms import SearchForm

MAXSOURCES=250


TARGETSORTFUNCTION = {
    'text': lambda x: x.text,
    'freq': lambda x: -1 * x.target.freq,
    'prob': lambda x: -1 * x.prob,
    'revprob': lambda x: -1 * x.revprob,
}

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

def sortbuffer(buffer, targetorder):
    return sorted(buffer, key=TARGETSORTFUNCTION[targetorder] )

def search(request):
    searchform = SearchForm(request.GET)

    if searchform.is_valid():
        mode = searchform.cleaned_data['collection'][0]
        bykeyword = searchform.cleaned_data['bykeyword']
        sourceorder = searchform.cleaned_data['sourceorder']
        targetorder = searchform.cleaned_data['targetorder']
        collection = Collection.objects.get(id=searchform.cleaned_data['collection'][1:])


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
            sources = Collocation.objects(collection=collection, language=sourcelanguage).search_text(searchform.cleaned_data['text'].lower()).order_by(sourceorder)[:MAXSOURCES]
        else:
            #exact search
            sources = Collocation.objects(collection=collection, language=sourcelanguage, text=searchform.cleaned_data['text'].lower()).order_by(sourceorder)[:MAXSOURCES]


        buffer = []
        translations = []
        prevsource = None
        for translation in Translation.objects(source__in=sources).select_related():
            if translation.source.text == prevsource:
                translation.repeatedsource = True
            elif buffer:
                translations += sortbuffer(buffer, targetorder)
                buffer = []
            buffer.append(translation)
            prevsource = translation.source.text
        translations += sortbuffer(buffer, targetorder)

        return render(request, "search.html", {
            'searchform': searchform,
            'version': settings.VERSION,
            'translations': translations,
        })
    else:
        return render(request, "index.html", {
            'searchform': searchform,
            'version': settings.VERSION,
        })

