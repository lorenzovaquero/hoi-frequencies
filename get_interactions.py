#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import torch


def process_file(file_path):
    file = torch.load(file_path, weights_only=False)
    hoi_data = {}

    # We first get the objects and their frequencies
    hoi_data['objects'] = {}
    objects = file['objects']
    object_freqs = file['num_annotations_per_verb']
    for obj, freq in zip(objects, object_freqs):
        hoi_data['objects'][obj[1]] = freq
    
    # We then get the verbs and their frequencies
    hoi_data['verbs'] = {}
    verbs = file['verbs']
    verb_freqs = file['num_annotations_per_verb']
    for verb, freq in zip(verbs, verb_freqs):
        hoi_data['verbs'][verb[1]] = freq
    
    # We then get the interactions and their frequencies
    hoi_data['interactions'] = {}
    interactions = file['interactions']
    interaction_freqs = file['num_annotations_per_interaction']
    interaction_rare = set(file['rare_interaction_ids'])
    for int_num, (interaction, freq) in enumerate(zip(interactions, interaction_freqs)):
        interaction_name = '{},{}'.format(interaction[1][1], interaction[1][0])  # <verb>,<object>
        is_rare = 1 if int_num in interaction_rare else 0
        hoi_data['interactions'][interaction_name] = '{},{}'.format(freq, is_rare)  # What kind of data structure is this? Am I stupid?
    
    return hoi_data

def process_text(text):
    text = text.strip()
    action = text.split(',')
    action = [action[0].strip(), action[1].strip()]  # Verb and object
    actions = [action]
    return actions

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve HOI interactions')
    parser.add_argument('--file', help='Path to the input file', required=True)

    args = parser.parse_args()

    if args.file:
        hoi_data = process_file(args.file)
    else:
        print("Please provide either a file or text as input.")
        raise SystemExit
    
    # We will save csv file with the interactions and their frequencies
    # we get name without extension of file
    file_name = os.path.splitext(os.path.basename(args.file))[0]
    file_name_interactions = '{}_interactions.csv'.format(file_name)
    with open(file_name_interactions, 'w') as file:
        file.write('Verb,Object,Frequency,IsRare\n')
        for interaction, freq in hoi_data['interactions'].items():
            verb, obj = interaction.split(',')
            freq, is_rare = freq.split(',')
            file.write('{},{},{},{}\n'.format(verb, obj, freq, is_rare))
    
    # We will save csv file with the objects and their frequencies
    file_name_objects = '{}_objects.csv'.format(file_name)
    with open(file_name_objects, 'w') as file:
        file.write('Object,Frequency\n')
        for obj, freq in hoi_data['objects'].items():
            file.write('{},{}\n'.format(obj, freq))
    
    # We will save csv file with the verbs and their frequencies
    file_name_verbs = '{}_verbs.csv'.format(file_name)
    with open(file_name_verbs, 'w') as file:
        file.write('Verb,Frequency\n')
        for verb, freq in hoi_data['verbs'].items():
            file.write('{},{}\n'.format(verb, freq))

    print('Files saved as: {}, {}, {}'.format(file_name_interactions, file_name_objects, file_name_verbs))