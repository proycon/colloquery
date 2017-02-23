####################################################
# Colloquery
#   by Maarten van Gompel
#   Centre for Language and Speech Technology
#   Radboud University Nijmegen
#
#  developed for Van Dale
#
#  https://github.com/proycon/colloquery
#  Licensed under AGPLv3
###################################################

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from collections import defaultdict

from colloquery.web.models import Collection, Collocation, Translation
from colloquery.web.forms import SearchForm

MAXSOURCES=250


TARGETSORTFUNCTION = {
    'text': lambda x: x['target'].text if isinstance(x, dict) else x.target.text,
    'freq': lambda x: -1 * x['target'].freq if isinstance(x, dict) else -1 * x.target.freq,
    'prob': lambda x: -1 * x['prob'] if isinstance(x, dict) else -1 * x.prob,
    'revprob': lambda x: -1 * x['revprob'] if isinstance(x, dict) else -1 * x.revprob,
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
        freqthreshold = searchform.cleaned_data['freqthreshold']
        probthreshold = searchform.cleaned_data['probthreshold']
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
            sources = Collocation.objects(collection=collection, language=sourcelanguage).search_text(searchform.cleaned_data['text'].lower()).filter(freq__gte=freqthreshold).order_by(sourceorder)[skip:skip+MAXSOURCES]
        else:
            #exact search
            sources = Collocation.objects(collection=collection, language=sourcelanguage, text=searchform.cleaned_data['text'].lower()).filter(freq__gte=freqthreshold).order_by(sourceorder)[skip:skip+MAXSOURCES]

        translationsbysource = defaultdict(list)
        for translation in Translation.objects(source__in=sources, prob__gte=probthreshold).select_related():
            translationsbysource[translation.source.id].append(translation)

        translations = []

        i = 0 #in case the loop doesn't run with no sources

        if mode in (Mode.FORWARD, Mode.REVERSE):
            buffer = []
            for i, source in enumerate(sources):
                buffer = sorted(translationsbysource[source.id], key=TARGETSORTFUNCTION[targetorder])
                for translation in buffer[1:]:
                    translation.repeatedsource = True
                translations += buffer
        elif mode in (Mode.SOURCESYN, Mode.TARGETSYN):
            translationsbytarget = defaultdict(set)
            for revtranslation in Translation.objects(source__in=[ t.target for sublist in translationsbysource.values() for t in sublist  ]).select_related():
                translationsbytarget[revtranslation.source.id].add(revtranslation)
                #print("adding reverse translation: " + revtranslation.source.text + " -> " + revtranslation.target.text )

            for i, source in enumerate(sources):
                buffer = []
                for translation in translationsbysource[source.id]:
                    for revtranslation in translationsbytarget[translation.target.id]:
                        #print("Considering synonym: " + revtranslation.target.text )
                        if revtranslation.target.id != source.id:
                            #print("(target is source, skipping)")
                            if revtranslation.target.id not in [ t['target'].id for t in buffer ]:
                                #buffer.append(Translation(source, target=revtranslation.target, sourcefreq= source.freq, targetfreq=revtranslation.target.freq,  prob=translation.prob * revtranslation.prob, repeatedsource= bool(buffer)))
                                buffer.append({'source': source, 'target': revtranslation.target, 'sourcefreq': source.freq, 'targetfreq': revtranslation.target.freq,  'prob': translation.prob * revtranslation.prob, 'repeatedsource': bool(buffer) })
                translations += sorted(buffer, key=TARGETSORTFUNCTION[targetorder])

        prevlink = (skip > 0)
        forwardlink = ((i-skip)>=MAXSOURCES-1)
        noresults = (not translations)

        return render(request, "search.html", {
            'searchform': searchform,
            'version': settings.VERSION,
            'translations': translations,
            'prevlink': prevlink,
            'forwardlink': forwardlink,
            'noresults': noresults,
            'maxsources': MAXSOURCES,
            'collection': collection.id,
            'mode': mode
        })
    else:
        return render(request, "index.html", {
            'searchform': searchform,
            'version': settings.VERSION,
        })

