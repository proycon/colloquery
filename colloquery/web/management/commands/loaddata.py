#!/usr/bin/env python3

#Colloquery - Data loading pipeline
# Maarten van Gompel
# Licensed under AGPLv4

import argparse
import os
import colibricore
from django.core.management.base import BaseCommand, CommandError
from colloquery.web.models import Collection, Collocation, Keyword, Translation

class Command(BaseCommand):
    help = "Compute and load collocation data into the database"

    def add_arguments(self,parser):
        parser.add_argument('--title', type=str,help="Title for this data collection", action='store',default=0, required=True)
        parser.add_argument('--phrasetable', type=str,help="Moses phrasetable file", action='store',required=True)
        parser.add_argument('--sourcelang', type=str,help="Language 1 (iso-639-3)", action='store',required=True)
        parser.add_argument('--targetlang', type=str,help="Language 2 (iso-939-3)", action='store',required=True)
        parser.add_argument('--sourcecorpus', type=str,help="Corpus file 1", action='store',required=True)
        parser.add_argument('--targetcorpus', type=str,help="Corpus file 2", action='store',required=True)
        parser.add_argument('--freqthreshold', type=int,help="Minimum frequency threshold", action='store',default=2)
        parser.add_argument('--pts', type=float,help="p(target|source) threshold", action='store',default=0)
        parser.add_argument('--pst', type=float,help="p(source|target) threshold", action='store',default=0)
        parser.add_argument('--joinedthreshold', type=float,help="p(source|target) * p(target|source) threshold", action='store',default=0)
        parser.add_argument('--divergencethreshold', type=float,help="Divergence from best threshold: prunes translation options lower than set threshold times the strongest translation options (prunes weaker alternatives)", action='store',default=0)
        parser.add_argument('--maxlength', type=int,help="Maximum collocation size", action='store',default=8)
        parser.add_argument('--tmpdir', type=str,help="Temporary directory", action='store',default=os.environ['TMPDIR'] if 'TMPDIR' in os.environ else "/tmp")

    def handle(self, *args, **options):
        self.stdout.write("Encoding source corpus ...")
        sourceclassfile = os.path.join(options['tmpdir'], os.path.basename(options['sourcecorpus']).replace('.txt','') + '.colibri.cls')
        sourcecorpusfile = os.path.join(options['tmpdir'], os.path.basename(options['sourcecorpus']).replace('.txt','') + '.colibri.dat')
        sourcemodelfile = os.path.join(options['tmpdir'], os.path.basename(options['sourcecorpus']).replace('.txt','') + '.colibri.patternmodel')
        sourceclassencoder = colibricore.ClassEncoder()
        sourceclassencoder.build(options['sourcecorpus'])
        sourceclassencoder.save(sourceclassfile)
        sourceclassencoder.encodefile(options['sourcecorpus'], sourcecorpusfile)
        self.stdout.write(self.style.SUCCESS('DONE'))

        self.stdout.write("Encoding target corpus ...")
        targetclassfile = os.path.join(options['tmpdir'], os.path.basename(options['targetcorpus']).replace('.txt','') + '.colibri.cls')
        targetcorpusfile = os.path.join(options['tmpdir'], os.path.basename(options['targetcorpus']).replace('.txt','') + '.colibri.dat')
        targetmodelfile = os.path.join(options['tmpdir'], os.path.basename(options['targetcorpus']).replace('.txt','') + '.colibri.patternmodel')
        targetclassencoder = colibricore.ClassEncoder()
        targetclassencoder.build(options['targetcorpus'])
        targetclassencoder.save(targetclassfile)
        targetclassencoder.encodefile(options['targetcorpus'], targetcorpusfile)
        self.stdout.write(self.style.SUCCESS('DONE'))

        self.stdout.write('Computing pattern model of source corpus ...')
        modeloptions = colibricore.PatternModelOptions(mintokens=options['freqthreshold'],maxlength=options['maxlength'])
        sourcemodel = colibricore.UnindexedPatternModel()
        sourcemodel.train(sourcecorpusfile, modeloptions)
        sourcemodel.write(sourcemodelfile)
        self.stdout.write(self.style.SUCCESS('DONE'))

        self.stdout.write('Computing pattern model of target corpus ...')
        targetmodel = colibricore.UnindexedPatternModel()
        targetmodel.train(targetcorpusfile, modeloptions)
        targetmodel.write(targetmodelfile)
        self.stdout.write(self.style.SUCCESS('DONE'))

        alignmodelfile = os.path.join(options['tmpdir'], "alignmodel.colibri")

        #delete models to conserve memory during next step
        del sourcemodel
        del targetmodel
        self.stdout.write(self.style.SUCCESS('Unloaded patternmodels'))

        self.stdout.write("Computing alignment model")
        os.system("colibri-mosesphrasetable2alignmodel -i " + options['phrasetable'] + " -o " + alignmodelfile + " -S " + sourceclassfile + " -T " + targetclassfile + " -m " + sourcemodelfile + " -M " + targetmodelfile + " -t " + str(options['freqthreshold']) + " -l " + str(options['maxlength']) + " -p " + str(options['pts']) + " -P " + str(options['pst']) + " -j " + str(options['joinedthreshold']) + " -d " + str(options['divergencethreshold']))
        self.stdout.write(self.style.SUCCESS('DONE'))

        self.stdout.write("Loading models")
        sourceclassdecoder = colibricore.ClassDecoder(sourceclassfile)
        targetclassdecoder = colibricore.ClassDecoder(targetclassfile)
        sourcemodel = colibricore.UnindexedPatternModel(sourcemodelfile, modeloptions)
        targetmodel = colibricore.UnindexedPatternModel(targetmodelfile, modeloptions)
        alignmodel = colibricore.PatternAlignmentModel_float(alignmodelfile, modeloptions)
        self.stdout.write(self.style.SUCCESS('DONE'))

        collection = Collection.objects.get_or_create(name=options['title'], sourcelanguage=options['sourcelang'], targetlanguage=options['argetlang'])
        self.stdout.write(self.style.SUCCESS('Created collection'))

        self.stdout.write("Loading translation pairs (this may take a while)..." )
        for i, sourcepattern, targetpattern, scores in enumerate(alignmodel.triples()):
            if i % 5000 == 0:
                self.stdout.write("Added " + str(i+1) + " pairs")

            sourcefreq = sourcemodel[sourcepattern]
            source = Collocation.objects.get_or_create(collection=collection, language=options['sourcelang'], text=sourcepattern.tostring(sourceclassdecoder), freq=sourcefreq)
            for wordpattern in sourcepattern.ngrams(1):
                keyword = Keyword.objects.get_or_create(text=wordpattern.tostring(sourceclassdecoder), language=options['sourcelang'], collection=collection)
                keyword.add(source)

            targetfreq = targetmodel[targetpattern]
            target = Collocation.objects.get_or_create(collection=collection, language=options['targetlang'], text=targetpattern.tostring(targetclassdecoder), freq=targetfreq)
            for wordpattern in targetpattern.ngrams(1):
                keyword = Keyword.objects.get_or_create(text=wordpattern.tostring(targetclassdecoder), language=options['targetlang'], collection=collection)
                keyword.add(target)

            source.translations.create(target, prob=scores[0],  reverseprob=scores[2])

        self.stdout.write(self.style.SUCCESS('Added ' + str(i+1) + ' translation pairs to the database'))



        #raise CommandError("error")

