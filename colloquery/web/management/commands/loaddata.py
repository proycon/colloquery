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
        sourceclassfile = os.path.join(args.tmpdir, os.path.basename(args.sourcecorpus).replace('.txt','') + '.colibri.cls')
        sourcecorpusfile = os.path.join(args.tmpdir, os.path.basename(args.sourcecorpus).replace('.txt','') + '.colibri.dat')
        sourcemodelfile = os.path.join(args.tmpdir, os.path.basename(args.sourcecorpus).replace('.txt','') + '.colibri.patternmodel')
        sourceclassencoder = colibricore.ClassEncoder()
        sourceclassencoder.build(args.sourcecorpus)
        sourceclassencoder.save(sourceclassfile)
        sourceclassencoder.encodefile(args.sourcecorpus, sourcecorpusfile)
        self.stdout.write(self.style.SUCCESS('Encoded source corpus'))

        targetclassfile = os.path.join(args.tmpdir, os.path.basename(args.targetcorpus).replace('.txt','') + '.colibri.cls')
        targetcorpusfile = os.path.join(args.tmpdir, os.path.basename(args.targetcorpus).replace('.txt','') + '.colibri.dat')
        targetmodelfile = os.path.join(args.tmpdir, os.path.basename(args.targetcorpus).replace('.txt','') + '.colibri.patternmodel')
        targetclassencoder = colibricore.ClassEncoder()
        targetclassencoder.build(args.targetcorpus)
        targetclassencoder.save(targetclassfile)
        targetclassencoder.encodefile(args.targetcorpus, targetcorpusfile)
        self.stdout.write(self.style.SUCCESS('Encoded target corpus'))

        options = colibricore.PatternModelOptions(mintokens=args.freqthreshold,maxlength=args.maxlength)
        sourcemodel = colibricore.UnindexedPatternModel()
        sourcemodel.train(sourcecorpusfile, options)
        sourcemodel.save(sourcemodelfile)
        self.stdout.write(self.style.SUCCESS('Computed pattern model of source corpus'))

        options = colibricore.PatternModelOptions(mintokens=args.freqthreshold,maxlength=args.maxlength)
        targetmodel = colibricore.UnindexedPatternModel()
        targetmodel.train(targetcorpusfile, options)
        targetmodel.save(targetmodelfile)
        self.stdout.write(self.style.SUCCESS('Computed pattern model of target corpus'))

        alignmodelfile = os.path.join(tmpdir, "alignmodel.colibri")

        #delete models to conserve memory during next step
        del sourcemodel
        del targetmodel
        self.stdout.write(self.style.SUCCESS('Unloaded patternmodels'))

        os.system("colibri-mosesphrasetable2alignmodel -i " + args.phrasetable + " -o " + alignmodelfile + " -S " + sourceclassfile + " -T " + targetclassfile + " -m " + sourcemodelfile + " -M " + targetmodelfile + " -t " + str(args.freqthreshold) + " -l " + str(args.maxlength) )
        self.stdout.write(self.style.SUCCESS('Computed alignment model'))

        sourcemodel = colibricore.UnindexedPatternModel(sourcemodelfile)
        targetmodel = colibricore.UnindexedPatternModel(targetmodelfile)
        self.stdout.write(self.style.SUCCESS('Reloaded patternmodels'))

        alignmodel = colibricore.PatternAlignmentModel_float(alignmodelfile)
        self.stdout.write(self.style.SUCCESS('Loaded alignment model'))

        for sourcepattern, targetpattern, scores in alignmodel.triples():
    










        #raise CommandError("error")

