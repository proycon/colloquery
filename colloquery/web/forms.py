from django import forms
from colloquery.web.models import Collection


LANGUAGENAMES = {
        'eng': 'English',
        'nld': 'Dutch',
        'spa': 'Spanish',
}

collectionchoices = []
for collection in Collection.objects.all():
    collectionchoices.append( ('F' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.sourcelanguage] + " to " + LANGUAGENAMES[collection.targetlanguage]))
    collectionchoices.append( ('R' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.targetlanguage] + " to " + LANGUAGENAMES[collection.sourcelanguage]))
    collectionchoices.append( ('S' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.sourcelanguage] + " synonyms/paraphrases"))
    collectionchoices.append( ('T' + str(collection.id), collection.name + ": " + LANGUAGENAMES[collection.sourcelanguage] + " synonyms/paraphrases"))


class SearchForm(forms.Form):
    text = forms.CharField(label="Search terms", max_length=150)
    keywordsearch = forms.BooleanField(label="Search by keywords")
    collection = forms.ChoiceField(label="Collection", choices=collectionchoices )

