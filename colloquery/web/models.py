from django.db import models


class Collection(models.Model):
    name = models.CharField(max_length=50)
    sourcelanguage = models.CharField(max_length=3)
    targetlanguage = models.CharField(max_length=3)

    def __str__(self):
        return self.name

class Collocation(models.Model):
    collection = models.ForeignKey(Collection)
    language = models.CharField(max_length=3)
    text = models.CharField(max_length=125)
    freq = models.IntegerField() #occurrence frequency (absolute)
    translations = models.ManyToManyField("self", through="Translation", symmetrical=False)

    class Meta:
        unique_together = (("collection","language","text"),)
        index_together = (("collection","language","text"),)

    def __str__(self):
        return self.text

class Keyword(models.Model):
    collection = models.ForeignKey(Collection)
    language = models.CharField(max_length=3)
    text = models.CharField(max_length=60)
    collocations = models.ManyToManyField(Collocation)

    def __str__(self):
        return self.text

    class Meta:
        unique_together = (("collection","language","text"),)
        index_together = (("collection","language","text"),)

class Translation(models.Model):
    source = models.ForeignKey(Collocation, on_delete=models.CASCADE, related_name="rev_source")
    target = models.ForeignKey(Collocation, on_delete=models.CASCADE, related_name="rev_target")
    prob = models.FloatField() #p(target|source)
    reverseprob = models.FloatField() #p(source|target)
