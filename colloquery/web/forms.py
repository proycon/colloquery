from django import forms
from django.db.utils import ProgrammingError
from django.conf import settings
from colloquery.web.models import Collection
import mongoengine


LANGUAGENAMES = {
    'en': 'English',
    'nl': 'Dutch',
    'es': 'Spanish',
}

collectionchoices = []
try:
    mongoengine.connect("colloquery", host=settings.MONGODB_HOST, port=settings.MONGODB_PORT)
    for collection in Collection.objects():
        collectionchoices.append( ('F' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.sourcelanguage] + " to " + LANGUAGENAMES[collection.targetlanguage]))
        collectionchoices.append( ('R' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.targetlanguage] + " to " + LANGUAGENAMES[collection.sourcelanguage]))
        collectionchoices.append( ('S' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.sourcelanguage] + " synonyms/paraphrases"))
        collectionchoices.append( ('T' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.targetlanguage] + " synonyms/paraphrases"))
except ProgrammingError:
    #database may not be present yet
    pass


class SearchForm(forms.Form):
    collection = forms.ChoiceField(label="Collection", choices=collectionchoices )
    text = forms.CharField(label="Search terms", max_length=150)
    bykeyword = forms.BooleanField(label="Search by keyword",required=False)
    sourceorder = forms.ChoiceField(label="Source order", choices=[('text','Text'), ('-freq', 'Frequency')],initial='-freq')
    targetorder = forms.ChoiceField(label="Target order", choices=[('text','Text'), ('freq', 'Frequency'),('prob','Translation probability'), ('revprob', 'Reverse probability') ],initial='prob')
    freqthreshold = forms.IntegerField(label="Frequency threshold", initial=1, min_value=1)
    probthreshold = forms.FloatField(label="Translation probability threshold", initial=0.2, min_value=0.0, max_value=1.0)
    skip = forms.IntegerField(widget=forms.HiddenInput(), initial=0)
