from django import forms
from colloquery.web.models import Collection

class SearchForm(forms.Form):
    text = forms.CharField(label="Search terms", max_length=150)
    keywordsearch = forms.BooleanField(label="Search by keywords")
    synonymsearch = forms.BooleanField(label="Search for synonyms")
    collection = forms.ChoiceField(label="Collection", choices=[ (collection.id, collection.name + " (" + collection.sourcelanguage + " -> " + collection.targetlanguage+")") for collection in Collection.objects.all() ] )
    reversesearch = forms.BooleanField(label="Search by target language instead of source language")

