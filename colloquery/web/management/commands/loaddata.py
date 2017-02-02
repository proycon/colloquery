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
        parser.add_argument('--title', type=int,help="Title for this data collection", action='store',default=0, required=True)
        parser.add_argument('--phrasetable', type=str,help="Moses phrasetable file", action='store',required=True)
        parser.add_argument('--sourcelang', type=str,help="Language 1 (iso-639-3)", action='store',required=True)
        parser.add_argument('--targetlang', type=str,help="Language 2 (iso-939-3)", action='store',required=True)
        parser.add_argument('--sourcecorpus', type=str,help="Corpus file 1", action='store',required=True)
        parser.add_argument('--targetcorpus', type=str,help="Corpus file 2", action='store',required=True)
        parser.add_argument('--freqthreshold', type=int,help="Minimum frequency threshold", action='store',default=2,required=True)
        parser.add_argument('--maxlength', type=int,help="Maximum collocation size", action='store',default=8,required=True)
        parser.add_argument('--tmpdir', type=str,help="Temporary directory", action='store',default=os.env['TMPDIR'] if 'TMPDIR' in os.env else "/tmp")

    def handle(self, *args, **options):
        self.stdout.write("Encoding source corpus ...")
        sourceclassfile = os.path.join(args.tmpdir, os.path.basename(args.sourcecorpus).replace('.txt','') + '.colibri.cls')
        sourcecorpusfile = os.path.join(args.tmpdir, os.path.basename(args.sourcecorpus).replace('.txt','') + '.colibri.dat')
        sourcemodelfile = os.path.join(args.tmpdir, os.path.basename(args.sourcecorpus).replace('.txt','') + '.colibri.patternmodel')
        sourceclassencoder = colibricore.ClassEncoder()
        sourceclassencoder.build(args.sourcecorpus)
        sourceclassencoder.save(sourceclassfile)
        sourceclassencoder.encodefile(args.sourcecorpus, sourcecorpusfile)
        self.stdout.write(self.style.SUCCESS('DONE'))

        self.stdout.write("Encoding target corpus ...")
        targetclassfile = os.path.join(args.tmpdir, os.path.basename(args.targetcorpus).replace('.txt','') + '.colibri.cls')
        targetcorpusfile = os.path.join(args.tmpdir, os.path.basename(args.targetcorpus).replace('.txt','') + '.colibri.dat')
        targetmodelfile = os.path.join(args.tmpdir, os.path.basename(args.targetcorpus).replace('.txt','') + '.colibri.patternmodel')
        targetclassencoder = colibricore.ClassEncoder()
        targetclassencoder.build(args.targetcorpus)
        targetclassencoder.save(targetclassfile)
        targetclassencoder.encodefile(args.targetcorpus, targetcorpusfile)
        self.stdout.write(self.style.SUCCESS('DONE'))

        self.stdout.write('Computing pattern model of source corpus ...')
        options = colibricore.PatternModelOptions(mintokens=args.freqthreshold,maxlength=args.maxlength)
        sourcemodel = colibricore.UnindexedPatternModel()
        sourcemodel.train(sourcecorpusfile, options)
        sourcemodel.save(sourcemodelfile)
        self.stdout.write(self.style.SUCCESS('DONE'))

        self.stdout.write('Computing pattern model of target corpus ...')
        options = colibricore.PatternModelOptions(mintokens=args.freqthreshold,maxlength=args.maxlength)
        targetmodel = colibricore.UnindexedPatternModel()
        targetmodel.train(targetcorpusfile, options)
        targetmodel.save(targetmodelfile)
        self.stdout.write(self.style.SUCCESS('DONE'))

        alignmodelfile = os.path.join(args.tmpdir, "alignmodel.colibri")

        #delete models to conserve memory during next step
        del sourcemodel
        del targetmodel
        self.stdout.write(self.style.SUCCESS('Unloaded patternmodels'))

        self.stdout.write("Computing alignment model")
        os.system("colibri-mosesphrasetable2alignmodel -i " + args.phrasetable + " -o " + alignmodelfile + " -S " + sourceclassfile + " -T " + targetclassfile + " -m " + sourcemodelfile + " -M " + targetmodelfile + " -t " + str(args.freqthreshold) + " -l " + str(args.maxlength) )
        self.stdout.write(self.style.SUCCESS('DONE'))

        self.stdout.write("Loading models")
        sourceclassdecoder = colibricore.ClassDecoder(sourceclassfile)
        targetclassdecoder = colibricore.ClassDecoder(targetclassfile)
        sourcemodel = colibricore.UnindexedPatternModel(sourcemodelfile)
        targetmodel = colibricore.UnindexedPatternModel(targetmodelfile)
        alignmodel = colibricore.PatternAlignmentModel_float(alignmodelfile)
        self.stdout.write(self.style.SUCCESS('DONE'))

        collection = Collection.objects.get_or_create(name=args.title, sourcelanguage=args.sourcelang, targetlanguage=args.targetlang)
        self.stdout.write(self.style.SUCCESS('Created collection'))

        self.stdout.write("Loading translation pairs (this may take a while)..." )
        for i, sourcepattern, targetpattern, scores in enumerate(alignmodel.triples()):
            if i % 5000 == 0:
                self.stdout.write("Added " + str(i+1) + " pairs")

            sourcefreq = sourcemodel[sourcepattern]
            source = Collocation.objects.get_or_create(collection=collection, language=args.sourcelang, text=sourcepattern.tostring(sourceclassdecoder), freq=sourcefreq)
            for wordpattern in sourcepattern.ngrams(1):
                keyword = Keyword.objects.get_or_create(text=wordpattern.tostring(sourceclassdecoder), language=args.sourcelang, collection=collection)
                keyword.add(source)

            targetfreq = targetmodel[targetpattern]
            target = Collocation.objects.get_or_create(collection=collection, language=args.targetlang, text=targetpattern.tostring(targetclassdecoder), freq=targetfreq)
            for wordpattern in targetpattern.ngrams(1):
                keyword = Keyword.objects.get_or_create(text=wordpattern.tostring(targetclassdecoder), language=args.targetlang, collection=collection)
                keyword.add(target)

            source.translations.create(target, prob=scores[0],  reverseprob=scores[1])

        self.stdout.write(self.style.SUCCESS('Added ' + str(i+1) + ' translation pairs to the database'))



        #raise CommandError("error")

