#!/usr/bin/env python3

#Colloquery - Data loading pipeline
# Maarten van Gompel
# Licensed under AGPLv4

import argparse
import os
import colibricore
import mongoengine
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from colloquery.web.models import Collection, Collocation, Translation


def sqlescape(s):
    return s.replace('"','\\"')

def ignorable(s):
    return '.' in s or ',' in s or '!' in s or '"' in s



class Command(BaseCommand):
    help = "Compute and load collocation data into the database"

    def add_arguments(self,parser):
        parser.add_argument('--title', type=str,help="Title for this data collection", action='store',default=0, required=True)
        parser.add_argument('--phrasetable', type=str,help="Moses phrasetable file", action='store',required=True)
        parser.add_argument('--sourcelang', type=str,help="Language 1 (iso-639-1)", action='store',required=True)
        parser.add_argument('--targetlang', type=str,help="Language 2 (iso-639-1)", action='store',required=True)
        parser.add_argument('--sourcecorpus', type=str,help="Corpus file 1", action='store',required=True)
        parser.add_argument('--targetcorpus', type=str,help="Corpus file 2", action='store',required=True)
        parser.add_argument('--freqthreshold', type=int,help="Minimum frequency threshold", action='store',default=2)
        parser.add_argument('--pts', type=float,help="p(target|source) threshold", action='store',default=0)
        parser.add_argument('--pst', type=float,help="p(source|target) threshold", action='store',default=0)
        parser.add_argument('--joinedthreshold', type=float,help="p(source|target) * p(target|source) threshold", action='store',default=0)
        parser.add_argument('--divergencethreshold', type=float,help="Divergence from best threshold: prunes translation options lower than set threshold times the strongest translation options (prunes weaker alternatives)", action='store',default=0)
        parser.add_argument('--maxlength', type=int,help="Maximum collocation size", action='store',default=8)
        parser.add_argument('--tmpdir', type=str,help="Temporary directory", action='store',default=os.environ['TMPDIR'] if 'TMPDIR' in os.environ else "/tmp")
        parser.add_argument('--out', type=str,help="Output to the following sql file", action='store',default="out.sql")
        parser.add_argument('--force',help="Overwrite existing files", action='store_true')
        #args.storeconst, args.dataset, args.num, args.bar

    def handle(self, *args, **options):
        sourceclassfile = os.path.join(options['tmpdir'], os.path.basename(options['sourcecorpus']).replace('.txt','') + '.colibri.cls')
        sourcecorpusfile = os.path.join(options['tmpdir'], os.path.basename(options['sourcecorpus']).replace('.txt','') + '.colibri.dat')
        sourcemodelfile = os.path.join(options['tmpdir'], os.path.basename(options['sourcecorpus']).replace('.txt','') + '.colibri.patternmodel')

        if not os.path.exists(sourceclassfile) or not os.path.exists(sourcecorpusfile) or options['force']:
            self.stdout.write("Encoding source corpus ...")
            sourceclassencoder = colibricore.ClassEncoder()
            sourceclassencoder.build(options['sourcecorpus'])
            sourceclassencoder.save(sourceclassfile)
            sourceclassencoder.encodefile(options['sourcecorpus'], sourcecorpusfile)
            self.stdout.write(self.style.SUCCESS('DONE'))
        else:
            self.stdout.write("Reusing previously encoded source corpus ...")

        targetclassfile = os.path.join(options['tmpdir'], os.path.basename(options['targetcorpus']).replace('.txt','') + '.colibri.cls')
        targetcorpusfile = os.path.join(options['tmpdir'], os.path.basename(options['targetcorpus']).replace('.txt','') + '.colibri.dat')
        targetmodelfile = os.path.join(options['tmpdir'], os.path.basename(options['targetcorpus']).replace('.txt','') + '.colibri.patternmodel')

        if not os.path.exists(targetclassfile) or not os.path.exists(targetcorpusfile) or options['force']:
            self.stdout.write("Encoding target corpus ...")
            targetclassencoder = colibricore.ClassEncoder()
            targetclassencoder.build(options['targetcorpus'])
            targetclassencoder.save(targetclassfile)
            targetclassencoder.encodefile(options['targetcorpus'], targetcorpusfile)
            self.stdout.write(self.style.SUCCESS('DONE'))
        else:
            self.stdout.write("Reusing previously encoded target corpus ...")

        modeloptions = colibricore.PatternModelOptions(mintokens=options['freqthreshold'],maxlength=options['maxlength'])

        if not os.path.exists(sourcemodelfile) or options['force']:
            self.stdout.write('Computing pattern model of source corpus ...')
            sourcemodel = colibricore.UnindexedPatternModel()
            sourcemodel.train(sourcecorpusfile, modeloptions)
            sourcemodel.write(sourcemodelfile)
            self.stdout.write(self.style.SUCCESS('DONE'))
        else:
            sourcemodel = None
            self.stdout.write("Reusing previously computed source model ...")

        if not os.path.exists(targetmodelfile) or options['force']:
            self.stdout.write('Computing pattern model of target corpus ...')
            targetmodel = colibricore.UnindexedPatternModel()
            targetmodel.train(targetcorpusfile, modeloptions)
            targetmodel.write(targetmodelfile)
            self.stdout.write(self.style.SUCCESS('DONE'))
        else:
            targetmodel = None
            self.stdout.write("Reusing previously computed target model ...")

        alignmodelfile = os.path.join(options['tmpdir'], "alignmodel.colibri")

        #delete models to conserve memory during next step
        if sourcemodel is not None:
            del sourcemodel
            self.stdout.write(self.style.SUCCESS('Unloaded source patternmodel'))
        if targetmodel is not None:
            del targetmodel
            self.stdout.write(self.style.SUCCESS('Unloaded target patternmodel'))

        if not os.path.exists(alignmodelfile) or options['force']:
            cmd = "colibri-mosesphrasetable2alignmodel -i " + options['phrasetable'] + " -o " + alignmodelfile + " -S " + sourceclassfile + " -T " + targetclassfile + " -m " + sourcemodelfile + " -M " + targetmodelfile + " -t " + str(options['freqthreshold']) + " -l " + str(options['maxlength']) + " -p " + str(options['pts']) + " -P " + str(options['pst']) + " -j " + str(options['joinedthreshold']) + " -d " + str(options['divergencethreshold'])
            self.stdout.write("Computing alignment model: " + cmd)
            os.system(cmd)
            self.stdout.write(self.style.SUCCESS('DONE'))
        else:
            self.stdout.write(self.style.SUCCESS('Reusing previously computed alignment model'))


        self.stdout.write("Loading models")
        sourceclassdecoder = colibricore.ClassDecoder(sourceclassfile)
        targetclassdecoder = colibricore.ClassDecoder(targetclassfile)
        sourcemodel = colibricore.UnindexedPatternModel(sourcemodelfile, modeloptions)
        targetmodel = colibricore.UnindexedPatternModel(targetmodelfile, modeloptions)
        alignmodel = colibricore.PatternAlignmentModel_float(alignmodelfile, modeloptions)
        self.stdout.write(self.style.SUCCESS('DONE'))

        #collection,_ = Collection.objects.get_or_create(name=options['title'], sourcelanguage=options['sourcelang'], targetlanguage=options['targetlang'])
        #collection_id = 1

        l = len(alignmodel)


        self.stdout.write("Connecting to MongoDB server at " + settings.MONGODB_HOST + ":" + str(settings.MONGODB_PORT) )
        mongoengine.connect("colloquery", host=settings.MONGODB_HOST, port=settings.MONGODB_PORT)

        self.stdout.write("Generating translation pairs (this may take a while)..." )

        targetcollocations = {}
        prevsourcepattern = None
        collection = Collection(name=options['title'], sourcelanguage=options['sourcelang'], targetlanguage=options['targetlang'])
        collection.save()
        sourcecount = 0

        for i, (sourcepattern, targetpattern, scores) in enumerate(alignmodel.triples()):
            if i % 100 == 0:
                self.stdout.write(str(round(((sourcecount + 1) / l) * 100,1)) + "% -- @" + str(sourcecount + 1) + " of " + str(l) + ": inserted " + str(i+1) + " pairs") #(source=" + str(n_source) + ", target=" + str(n_target) + ", source-keywords=" + str(n_source_keywords) + ", target-keywords=" + str(n_target_keywords) + ")")

            if prevsourcepattern is None or sourcepattern != prevsourcepattern:
                sourcefreq = sourcemodel[sourcepattern]
                text = sourcepattern.tostring(sourceclassdecoder)
                if ignorable(text):
                    continue
                sourcecollocation = Collocation(collection=collection, language=options['sourcelang'], text=text, freq=sourcefreq)
                sourcecollocation.save()

                prevsourcepattern = sourcepattern
                sourcecount += 1


            targetfreq = targetmodel[targetpattern]
            text = targetpattern.tostring(targetclassdecoder)
            if ignorable(text):
                continue
            if targetpattern in targetcollocations: #quicker in-memory lookup
                # targetcollocation = Collocation.objects(text=text, language=options['targetlang'], collection=collection)[0] #get from db
                targetcollocation = targetcollocations[targetpattern]
            else:
                targetcollocation = Collocation(collection=collection, language=options['targetlang'], text=text, freq=targetfreq)
                targetcollocation.save()
                #self.stdout.write(repr(targetcollocation.id))
                targetcollocations[targetpattern] = targetcollocation.id

            Translation(source=sourcecollocation, target=targetcollocation, prob=scores[0], revprob=scores[2]).save()
            Translation(source=targetcollocation, target=sourcecollocation, prob=scores[2], revprob=scores[0]).save()
