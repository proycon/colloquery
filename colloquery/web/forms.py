from django import forms
from django.db.utils import ProgrammingError
import mongoengine
from colloquery.web.models import Collection


LANGUAGENAMES = {
    'en': 'English',
    'nl': 'Dutch',
    'es': 'Spanish',
}

collectionchoices = []
try:
    mongoengine.connect("colloquery", alias="default")
    for collection in Collection.objects():
        collectionchoices.append( ('F' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.sourcelanguage] + " to " + LANGUAGENAMES[collection.targetlanguage]))
        collectionchoices.append( ('R' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.targetlanguage] + " to " + LANGUAGENAMES[collection.sourcelanguage]))
        collectionchoices.append( ('S' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.sourcelanguage] + " synonyms/paraphrases"))
        collectionchoices.append( ('T' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.sourcelanguage] + " synonyms/paraphrases"))
except ProgrammingError:
    #database may not be present yet
    pass


class SearchForm(forms.Form):
    collection = forms.ChoiceField(label="Collection", choices=collectionchoices )
    text = forms.CharField(label="Search terms", max_length=150)
    bykeyword = forms.BooleanField(label="Search by keywords",required=False)
