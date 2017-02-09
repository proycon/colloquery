from django import forms
from django.db.utils import ProgrammingError
from colloquery.web.models import Collection


LANGUAGENAMES = {
    'eng': 'English',
    'nld': 'Dutch',
    'spa': 'Spanish',
}

collectionchoices = []
try:
    for collection in Collection.objects.all():
        collectionchoices.append( ('F' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.sourcelanguage] + " to " + LANGUAGENAMES[collection.targetlanguage]))
        collectionchoices.append( ('R' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.targetlanguage] + " to " + LANGUAGENAMES[collection.sourcelanguage]))
        collectionchoices.append( ('S' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.sourcelanguage] + " synonyms/paraphrases"))
        collectionchoices.append( ('T' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.sourcelanguage] + " synonyms/paraphrases"))
except ProgrammingError:
    #database may not be present yet
    pass


class SearchForm(forms.Form):
    text = forms.CharField(label="Search terms", max_length=150)
    collection = forms.ChoiceField(label="Collection", choices=collectionchoices )
    keywordsearch = forms.BooleanField(label="Search by keywords")
