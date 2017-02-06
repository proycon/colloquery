#!/usr/bin/env python3

#Colloquery - Data loading pipeline
# Maarten van Gompel
# Licensed under AGPLv4

import argparse
import os
import colibricore
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from colloquery.web.models import Collection, Collocation, Keyword, Translation


def sqlescape(s):
    return s.replace('"','\\"')

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
        parser.add_argument('--out', type=str,help="Output to the following sql file", action='store',default="out.sql")

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

        collection,_ = Collection.objects.get_or_create(name=options['title'], sourcelanguage=options['sourcelang'], targetlanguage=options['targetlang'])
        self.stdout.write(self.style.SUCCESS('Created collection'))


        self.stdout.write("Generating translation pairs (this may take a while)..." )

        try:
            collocation_id = Collocation.objects.latest('id').id
        except ObjectDoesNotExist:
            collocation_id = 0
        try:
            keywords_id = Keyword.objects.latest('id').id
        except ObjectDoesNotExist:
            keywords_id = 0
        try:
            translation_id = Translation.objects.latest('id').id
        except ObjectDoesNotExist:
            translation_id = 0
        try:
            keyword_collocations_id = Keyword.collocations.through.objects.latest('id').id
        except ObjectDoesNotExist:
            keyword_collocations_id = 0
        sourcekeywords = colibricore.UnindexedPatternModel() #maps keyword text to primary key
        targetkeywords = colibricore.UnindexedPatternModel()  #maps keyword text to primary key
        targetcollocations = colibricore.UnindexedPatternModel()  #maps collocation text to primary key
        prevsourcepattern = None
        with open(options['out'], 'w', encoding='utf-8') as f:
            f.write("SET NAMES utf8;\n")
            for i, (sourcepattern, targetpattern, scores) in enumerate(alignmodel.triples()):
                if i % 10000 == 0:
                    self.stdout.write("Generated " + str(i+1) + " pairs") #(source=" + str(n_source) + ", target=" + str(n_target) + ", source-keywords=" + str(n_source_keywords) + ", target-keywords=" + str(n_target_keywords) + ")")

                if prevsourcepattern is None or sourcepattern != prevsourcepattern:
                    collocation_id += 1
                    sourcefreq = sourcemodel[sourcepattern]
                    f.write("INSERT INTO `web_collocation` (`id`,`collection_id`,`language`,`text`,`freq`) VALUES ("+str(collocation_id)+","+str(collection.id)+",\"" + options['sourcelang'] + "\",\"" + sqlescape(sourcepattern.tostring(sourceclassdecoder)) + "\"," + str(sourcefreq) + ") ON DUPLICATE KEY UPDATE `freq`=`freq`;\n")
                    prevsourcepattern = sourcepattern
                    #source,created  = Collocation.objects.get_or_create(collection=collection, language=options['sourcelang'], text=sourcepattern.tostring(sourceclassdecoder), freq=sourcefreq)

                    #n_source += int(created)
                    for wordpattern in sourcepattern.ngrams(1):
                        text = wordpattern.tostring(sourceclassdecoder)
                        if wordpattern not in sourcekeywords:
                            keywords_id += 1
                            sourcekeywords.add(wordpattern, keywords_id)
                            f.write("INSERT INTO `web_keyword` (`id`,`collection_id`,`language`,`text`) VALUES ("+str(sourcekeywords[wordpattern])+","+str(collection.id)+",\"" + options['sourcelang'] + "\",\"" + sqlescape(text) + "\");\n")
                        keyword_collocations_id += 1
                        f.write("INSERT INTO `web_keyword_collocations` (`id`,`keyword_id`,`collocation_id`) VALUES ("+str(keyword_collocations_id)+","+str(sourcekeywords[wordpattern])+"," + str(collocation_id) + ");\n")
                        #keyword,created = Keyword.objects.get_or_create(text=text, language=options['sourcelang'], collection=collection)
                        # n_source_keywords += int(created)
                        #keyword.collocations.add(source)

                    source_collocation_id = collocation_id


                targetfreq = targetmodel[targetpattern]
                if targetpattern in targetcollocations:
                    collocation_id = targetcollocations[targetpattern]
                else:
                    collocation_id += 1
                    targetcollocations.add(targetpattern, collocation_id)
                    f.write("INSERT INTO `web_collocation` (`id`,`collection_id`,`language`,`text`,`freq`) VALUES ("+str(collocation_id)+","+str(collection.id)+",\"" + options['targetlang'] + "\",\"" + sqlescape(targetpattern.tostring(targetclassdecoder)) + "\"," + str(targetfreq) + ") ON DUPLICATE KEY UPDATE `freq`=`freq`;\n")

                #target,created = Collocation.objects.get_or_create(collection=collection, language=options['targetlang'], text=targetpattern.tostring(targetclassdecoder), freq=targetfreq)
                #n_target += int(created)
                for wordpattern in targetpattern.ngrams(1):
                    text = wordpattern.tostring(targetclassdecoder)
                    if wordpattern not in targetkeywords:
                        keywords_id += 1
                        targetkeywords.add(wordpattern, keywords_id)
                        f.write("INSERT INTO `web_keyword` (`id`,`collection_id`,`language`,`text`) VALUES ("+str(targetkeywords[wordpattern])+","+str(collection.id)+",\"" + options['targetlang'] + "\",\"" + sqlescape(text) + "\");\n")
                    keyword_collocations_id += 1
                    f.write("INSERT INTO `web_keyword_collocations` (`id`,`keyword_id`,`collocation_id`) VALUES ("+str(keyword_collocations_id)+","+str(targetkeywords[wordpattern])+"," + str(collocation_id) + ");\n")

                    #keyword,created = Keyword.objects.get_or_create(text=wordpattern.tostring(targetclassdecoder), language=options['targetlang'], collection=collection)
                    #n_target_keywords += int(created)
                    #keyword.collocations.add(target)

                translation_id += 1
                f.write("INSERT INTO `web_translation` (`id`,`source_id`,`target_id`) VALUES ("+str(translation_id)+","+str(source_collocation_id)+"," + str(collocation_id) + ");\n")


                #Translation.objects.create(source=source,target=target, prob=scores[0],  reverseprob=scores[2])

            self.stdout.write(self.style.SUCCESS('Generated ' + str(i+1) + ' translation pairs for import into database'))
            self.stdout.write("Now import manually using: mysql -u USERNAME -p DATABASE < " + options['out'] )



        #raise CommandError("error")

