from django.db import models


class Collection(models.model):
    collection = models.IntegerField()
    name = models.CharField(max_length=50)
    language1 = models.CharField(max_length=3)
    language2 = models.CharField(max_length=3)

class Collocation(models.Model):
    collection = models.IntegerField()
    language = models.CharField(max_length=3)
    text = models.CharField(max_length=125)
    freq = models.IntegerField() #occurrence frequency (absolute)

    class Meta:
        unique_together = (("collection","language","text"),)
        index_together = (("collection","language","text"),)

class Translation(models.Model):
    pattern1 = models.ForeignField(Collocation, db_index=True)
    pattern2 = models.ForeignField(Collocation, db_index=True)
    prob = models.FloatField() #p(pattern1|pattern2)
    reverseprob = models.FloatField() #p(pattern2|pattern1)
