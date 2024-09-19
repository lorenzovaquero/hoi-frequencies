#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merges Database and Ngrams frequencies')
    parser.add_argument('--file-hoi', help='Path to the HOI input file', required=True)
    parser.add_argument('--file-ngrams', help='Path to the ngrams input file', required=True)
    parser.add_argument('--file-verb-hoi', help='Path to the verb frequencies in the HOI database', required=True)
    parser.add_argument('--file-obj-hoi', help='Path to the object frequencies in the HOI database', required=True)
    parser.add_argument('--file-verb-ngrams', help='Path to the verb frequencies in the ngrams', required=True)
    parser.add_argument('--file-obj-ngrams', help='Path to the object frequencies in the ngrams', required=True)
    parser.add_argument('--output', help='Path to the output file', required=True)
    parser.add_argument('--allow-mismatch', action='store_true', help='Allow mismatch between interactions in the two files')
    

    args = parser.parse_args()

    # Load the data from CSV files
    # Files have a header with the columns: Verb, Object, Frequency
    database_df = pd.read_csv(args.file_hoi, header=0)
    ngrams_df = pd.read_csv(args.file_ngrams, header=0)

    # A "verb,object" makes an interaction, so we will join them
    database_df['Interaction'] = database_df['Verb'] + ',' + database_df['Object']
    ngrams_df['Interaction'] = ngrams_df['Verb'] + ',' + ngrams_df['Object']

    # We will join the dataframes on the interaction column and ensure there's no mismatch
    database_df = database_df.set_index('Interaction')
    ngrams_df = ngrams_df.set_index('Interaction')

    # Check for mismatches before joining
    if not args.allow_mismatch and not database_df.index.equals(ngrams_df.index):
        raise ValueError("Mismatch between interactions in the two files")

    df = pd.merge(database_df, ngrams_df, left_index=True, right_index=True, how='outer', suffixes=('_hoi', '_ngrams'))
    # Now we have a dataframe with the columns: Interaction, Verb_hoi, Object_hoi, Frequency_hoi, IsRare, Verb_ngrams, Object_ngrams, Frequency_ngrams
    if args.allow_mismatch:
        # Now we will fill the NaN values with stuff
        # If Verb_hoi is NaN, we will fill it with Verb_ngrams
        df['Verb_hoi'] = df['Verb_hoi'].fillna(df['Verb_ngrams'])
        df['Object_hoi'] = df['Object_hoi'].fillna(df['Object_ngrams'])

        # And vice versa
        df['Verb_ngrams'] = df['Verb_ngrams'].fillna(df['Verb_hoi'])
        df['Object_ngrams'] = df['Object_ngrams'].fillna(df['Object_hoi'])

        # We will fill the NaN values in Frequency_hoi and Frequency_ngrams with 0
        df['Frequency_hoi'] = df['Frequency_hoi'].fillna(0)
        df['Frequency_ngrams'] = df['Frequency_ngrams'].fillna(0)

        # We will fill the NaN values in IsRare with -1
        df['IsRare'] = df['IsRare'].fillna(-1)
    
    database_freq_verb_df = pd.read_csv(args.file_verb_hoi, header=0)
    database_freq_obj_df = pd.read_csv(args.file_obj_hoi, header=0)
    ngrams_freq_verb_df = pd.read_csv(args.file_verb_ngrams, header=0)
    ngrams_freq_obj_df = pd.read_csv(args.file_obj_ngrams, header=0)

    # I want to normalize the frequencies of the verbs and objects based on the frequency of the word on the Internet
    # I will convert the dataframes to dictionaries and then add the frequencies to the main dataframe
    database_freq_verb = database_freq_verb_df.set_index('Verb').to_dict()['Frequency']
    database_freq_obj = database_freq_obj_df.set_index('Object').to_dict()['Frequency']
    ngrams_freq_verb = ngrams_freq_verb_df.set_index('Verb').to_dict()['Frequency']
    ngrams_freq_obj = ngrams_freq_obj_df.set_index('Object').to_dict()['Frequency']

    df['Frequency_verb_hoi'] = df['Verb_hoi'].map(database_freq_verb)
    df['Frequency_obj_hoi'] = df['Object_hoi'].map(database_freq_obj)
    df['Frequency_verb_ngrams'] = df['Verb_ngrams'].map(ngrams_freq_verb)
    df['Frequency_obj_ngrams'] = df['Object_ngrams'].map(ngrams_freq_obj)

    # Now we have a table with the columns: Interaction, Verb_hoi, Object_hoi, Frequency_hoi, IsRare, Verb_ngrams, Object_ngrams, Frequency_ngrams, Frequency_verb_database, Frequency_obj_database, Frequency_verb_ngrams, Frequency_obj_ngrams
    # I remove Verb_hoi, Object_hoi and rename Verb_ngrams and Object_ngrams
    df = df.drop(columns=['Verb_hoi', 'Object_hoi'])
    df = df.rename(columns={'Verb_ngrams': 'Verb', 'Object_ngrams': 'Object'})
    
    df = df.rename(columns={'Frequency_hoi': 'Interaction_freq_hoi', 'Frequency_ngrams': 'Interaction_freq_ngrams'})
    df = df.rename(columns={'Frequency_verb_hoi': 'Verb_freq_hoi', 'Frequency_obj_hoi': 'Object_freq_hoi'})
    df = df.rename(columns={'Frequency_verb_ngrams': 'Verb_freq_ngrams', 'Frequency_obj_ngrams': 'Object_freq_ngrams'})
    df = df.rename(columns={'IsRare': 'IsRare_hoi'})

    # Now we have a table with the columns: Interaction, Verb, Object, Interaction_freq_hoi, IsRare_hoi, Interaction_freq_ngrams, Verb_freq_hoi, Object_freq_hoi, Verb_freq_ngrams, Object_freq_ngrams
    # We cast Interaction_freq_hoi, Interaction_freq_ngrams, Verb_freq_hoi, Object_freq_hoi, Verb_freq_ngrams, Object_freq_ngrams, IsRare_hoi to int
    df['Interaction_freq_hoi'] = df['Interaction_freq_hoi'].astype(int)
    df['Interaction_freq_ngrams'] = df['Interaction_freq_ngrams'].astype(int)
    df['Verb_freq_hoi'] = df['Verb_freq_hoi'].astype(int)
    df['Object_freq_hoi'] = df['Object_freq_hoi'].astype(int)
    df['Verb_freq_ngrams'] = df['Verb_freq_ngrams'].astype(int)
    df['Object_freq_ngrams'] = df['Object_freq_ngrams'].astype(int)
    df['IsRare_hoi'] = df['IsRare_hoi'].astype(int)

    # Finally, we reorder the columns
    df.reset_index(inplace=True)
    df = df[['Interaction', 'Verb', 'Object', 'Interaction_freq_ngrams',  'Verb_freq_ngrams', 'Object_freq_ngrams', 'Interaction_freq_hoi', 'Verb_freq_hoi', 'Object_freq_hoi', 'IsRare_hoi']]
    
    # We save the dataframe to a CSV file
    df.to_csv(args.output, index=False)
    print("File saved to {}".format(args.output))
    print(df.head())
    print(df.describe())