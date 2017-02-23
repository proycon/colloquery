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

import mongoengine

class Collection(mongoengine.Document):
    name = mongoengine.StringField()
    sourcelanguage = mongoengine.StringField()
    targetlanguage = mongoengine.StringField()
    meta = {
        'indexes': [ 'name' ]
    }


class Collocation(mongoengine.Document):
    collection = mongoengine.ReferenceField(Collection)
    language = mongoengine.StringField(max_length=3)
    text = mongoengine.StringField(max_length=125)
    freq = mongoengine.IntField() #occurrence frequency (absolute)

    meta = {
        'indexes': [
            {
                'fields': ['$text'],
            },
            {
                'fields': ('collection', 'language', 'text'),
                'unique': True,
            }
        ]
    }

class Translation(mongoengine.Document):
    source = mongoengine.ReferenceField(Collocation)
    target = mongoengine.ReferenceField(Collocation)
    prob = mongoengine.FloatField() #p(target|source)
    revprob = mongoengine.FloatField() #p(source|target)

    meta = {
        'indexes': [
            'source',
            'target',
        ]
    }
