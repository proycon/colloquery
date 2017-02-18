from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from collections import defaultdict

from colloquery.web.models import Collection, Collocation, Translation
from colloquery.web.forms import SearchForm

MAXSOURCES=250


TARGETSORTFUNCTION = {
    'text': lambda x: x.target.text,
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
        skip = searchform.cleaned_data['skip']

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
            sources = Collocation.objects(collection=collection, language=sourcelanguage).search_text(searchform.cleaned_data['text'].lower()).order_by(sourceorder)[skip:skip+MAXSOURCES]
        else:
            #exact search
            sources = Collocation.objects(collection=collection, language=sourcelanguage, text=searchform.cleaned_data['text'].lower()).order_by(sourceorder)[skip:skip+MAXSOURCES]

        results = False
        if mode in (Mode.FORWARD, Mode.REVERSE):
            translationsbysource = defaultdict(list)
            for translation in Translation.objects(source__in=sources).select_related():
                translationsbysource[translation.source.id].append(translation)

            buffer = []
            translations = []
            i = 0 #in case the loop doesn't run with no sources
            for i, source in enumerate(sources):
                results = True
                buffer = sorted(translationsbysource[source.id], key=TARGETSORTFUNCTION[targetorder])
                for translation in buffer[1:]:
                    translation.repeatedsource = True
                translations += buffer
        else:
            #synonyms
            pass



        prevlink = (skip > 0)
        forwardlink = ((i-skip)>=MAXSOURCES-1)
        noresults = (not results)

        return render(request, "search.html", {
            'searchform': searchform,
            'version': settings.VERSION,
            'translations': translations,
            'prevlink': prevlink,
            'forwardlink': forwardlink,
            'noresults': noresults,
            'maxsources': MAXSOURCES,
        })
    else:
        return render(request, "index.html", {
            'searchform': searchform,
            'version': settings.VERSION,
        })

