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

from colloquery.web.models import Collection, Collocation, Translation, stopwords
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


STOPWORDTHRESHOLD = 0.5 #if the ratio of leading + trailing stopwords in the pattern exceeds this, the pattern is pruned by the smart filter

def smartfilter_relevant(source, sourcelanguage):
    """Determines whether the source collocation is relevant or should be filtered out:
        Criteria: <Tjerk> Definitie van niet-relevante resultaten is m.i.:
          - begint met EN eindigt op een hoogfrequent functiewoord (bijv. "the sun on", "the sun in") OF
          - begint met OF eindigt op een hoofdfrequent functiewoord EN aantal woorden = 2 OF
          - begint met EN/OF eindigt op meerdere opeenvolgende hoogfrequente functiewoorden (bijv. "on the sun", "is the
          sun")
          - daarbij geldt: hoe kleiner het aantal woorden, hoe 'storender' de aanwezigheid van de functiewoorden.
    """
    sourcewords = source.text.split(' ')
    beginisstopword = sourcewords[0] in stopwords[sourcelanguage]
    endisstopword = sourcewords[-1] in stopwords[sourcelanguage]
    wordcount = len(sourcewords)
    #- begint met EN eindigt op een hoogfrequent functiewoord (bijv. "the sun on", "the sun in") OF
    #- begint met OF eindigt op een hoofdfrequent functiewoord EN aantal woorden = 2 OF
    if (beginisstopword and endisstopword) or ((beginisstopword or endisstopword) and wordcount == 2):
        return False
    elif not beginisstopword and not endisstopword:
        return True

    #- begint met EN/OF eindigt op meerdere opeenvolgende hoogfrequente functiewoorden (bijv. "on the sun", "is the sun")
    #- daarbij geldt: hoe kleiner het aantal woorden, hoe 'storender' de aanwezigheid van de functiewoorden.
    stopwordseq_begin = 0 #number of consecutive leading stopwords
    for i, word in enumerate(sourcewords):
        if word in stopwords[sourcelanguage] and i == stopwordseq_begin:
            stopwordseq_begin += 1
    stopwordseq_end = 0 #number of consecutive trailing stopwords
    for i, word in enumerate(reversed(sourcewords)):
        if word in stopwords[sourcelanguage] and i == stopwordseq_end:
            stopwordseq_end += 1
    if (stopwordseq_begin + stopwordseq_end) / wordcount >= STOPWORDTHRESHOLD:
        return False

    return True

def search(request):
    searchform = SearchForm(request.GET)

    if searchform.is_valid():
        mode = searchform.cleaned_data['collection'][0]
        bykeyword = searchform.cleaned_data['bykeyword']
        sourceorder = searchform.cleaned_data['sourceorder']
        targetorder = searchform.cleaned_data['targetorder']
        freqthreshold = searchform.cleaned_data['freqthreshold']
        probthreshold = searchform.cleaned_data['probthreshold']
        filterstopwords = searchform.cleaned_data['filterstopwords']
        smartfilter = searchform.cleaned_data['smartfilter']
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


        fullquerytext = searchform.cleaned_data['text'].lower()
        searches = []

        for querytext in fullquerytext.split(';'):
            querytext = querytext.strip()


            if bykeyword:
                #search by keyword
                if '&' in querytext:
                    for i, queryword in enumerate(querytext.split('&')):
                        queryword = queryword.strip()
                        if i == 0:
                            sources = list(Collocation.objects(collection=collection, language=sourcelanguage).search_text(queryword).filter(freq__gte=freqthreshold).order_by(sourceorder))
                        else:
                            secondsources = list(Collocation.objects(collection=collection, language=sourcelanguage).search_text(queryword).filter(freq__gte=freqthreshold))
                            newsources = []
                            for source in sources:
                                if source in secondsources:
                                    newsources.append(source)
                            sources = newsources
                else:
                    sources = Collocation.objects(collection=collection, language=sourcelanguage).search_text(querytext).filter(freq__gte=freqthreshold).order_by(sourceorder)[skip:skip+MAXSOURCES]
            else:
                #exact search
                sources = Collocation.objects(collection=collection, language=sourcelanguage, text=querytext).filter(freq__gte=freqthreshold).order_by(sourceorder)[skip:skip+MAXSOURCES]

            #filter source-side results with stop words
            if filterstopwords and sourcelanguage in stopwords:
                #crude filter
                newsources = []
                for source in sources:
                    hide = False
                    for word in source.text.split(' '):
                        if word in stopwords[sourcelanguage]:
                            hide = True
                            break
                    if not hide:
                        newsources.append(source)
                sources = newsources
            elif smartfilter and sourcelanguage in stopwords:
                newsources = []
                for source in sources:
                    if smartfilter_relevant(source, sourcelanguage):
                        newsources.append(source)
                sources = newsources


            translationsbysource = defaultdict(list)
            for translation in Translation.objects(source__in=sources, prob__gte=probthreshold).select_related():
                translationsbysource[translation.source.id].append(translation)


            i = 0 #in case the loop doesn't run with no sources

            translations = []

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


            noresults = (not translations)
            searches.append( (querytext, translations, noresults ) )

        prevlink = (skip > 0)
        forwardlink = ((i-skip)>=MAXSOURCES-1)


        return render(request, "search.html", {
            'searchform': searchform,
            'version': settings.VERSION,
            'searches': searches,
            'simple':  len(searches) == 1,
            'prevlink': prevlink,
            'forwardlink': forwardlink,
            'maxsources': MAXSOURCES,
            'collection': collection.id,
            'mode': mode
        })
    else:
        return render(request, "index.html", {
            'searchform': searchform,
            'version': settings.VERSION,
        })

