#!/usr/bin/env python3

#Colloquery - Data loading pipeline
# Maarten van Gompel
# Licensed under AGPLv4

import argparse
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "Compute and load collocation data into the database"

    def add_arguments(self,parser):
        parser.add_argument('--title', type=int,help="Title for this data collection", action='store',default=0, required=True)
        parser.add_argument('--phrasetable', type=str,help="Moses phrasetable file", action='store',required=True)
        parser.add_argument('--lang1', type=str,help="Language 1 (iso-639-3)", action='store',required=True)
        parser.add_argument('--lang2', type=str,help="Language 2 (iso-939-3)", action='store',required=True)
        parser.add_argument('--corpus1', type=str,help="Corpus file 1", action='store',required=True)
        parser.add_argument('--corpus2', type=str,help="Corpus file 2", action='store',required=True)
        parser.add_argument('-t', type=int,help="Minimum frequency threshold", action='store',default=2,required=True)
        parser.add_argument('-n', type=int,help="Maximum collocation size", action='store',default=8,required=True)

    def handle(self, *args, **options):
        #raise CommandError("error")
        #self.stdout.write(self.style.SUCCESS('Success'))

