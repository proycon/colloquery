#!/usr/bin/env python3

#Colloquery - Data loading pipeline
# Maarten van Gompel
# Licensed under AGPLv3

import argparse

def main():
    parser = argparse.ArgumentParser(description="Compute and load collocation data into the database", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--id', type=int,help="Numeric ID for this data collection", action='store',default=0, required=True)
    parser.add_argument('--title', type=int,help="Title for this data collection", action='store',default=0, required=True)
    parser.add_argument('--phrasetable', type=str,help="Moses phrasetable file", action='store',required=True)
    parser.add_argument('--lang1', type=str,help="Language 1 (iso-639-3)", action='store',required=True)
    parser.add_argument('--lang2', type=str,help="Language 2 (iso-939-3)", action='store',required=True)
    parser.add_argument('--corpus1', type=str,help="Corpus file 1", action='store',required=True)
    parser.add_argument('--corpus2', type=str,help="Corpus file 2", action='store',required=True)
    parser.add_argument('-t', type=int,help="Minimum frequency threshold", action='store',default=2,required=True)
    parser.add_argument('-n', type=int,help="Maximum collocation size", action='store',default=8,required=True)
    args = parser.parse_args()

if __name__ == '__main__':
    main()

