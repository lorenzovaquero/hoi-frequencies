#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import requests
import multiprocessing as mp
import tqdm

def call_api(query_text):
    base_url = "https://api.ngrams.dev"
    corpus = "eng"
    endpoint = "search"

    extra_params = "flags=cr"
    
    api_url = "{}/{}/{}?query={}&{}".format(base_url, corpus, endpoint, query_text, extra_params)
    response = requests.get(api_url)

    return response.json()

def querify(text, join_with_star=False):
    # Takes a text and converts it to a query string
    # We take into account variatons of the text (right now with ~, but we need to do something more elaborate)
    
    verb = text[0]
    obj = text[1]

    # Verb can have a preposition, so we only augment the first word
    verb_root = verb.split(' ')[0].strip()
    verb_root = verb_root + '~'  # We augment the verb.  # TODO: We need to do something more elaborate here (like ask GPT)

    verb_preposition = verb.split(' ')[1:]
    verb_preposition = [p.strip() for p in verb_preposition]

    verb_query = [verb_root]
    verb_query.extend(verb_preposition)
    verb_query = '+'.join(verb_query)

    # For object, we could augment all words. However, it is too many wildcards and the API does not return results.
    # We, therefore, only augment the last word (i.e. dining table -> dining table~)
    obj_root = obj.split(' ')[-1].strip()
    obj_root = obj_root + '~'  # We augment the object.  # TODO: We need to do something more elaborate here (like ask GPT)

    obj_preposition = obj.split(' ')[:-1]
    obj_preposition = [p.strip() for p in obj_preposition]
    
    obj_query = obj_preposition
    obj_query.append(obj_root)
    obj_query = '+'.join(obj_query)

    if join_with_star:
        query = "{}+*+{}".format(verb_query, obj_query)  # We add * to account for articles, adjectives, etc.
    else:
        query = "{}+{}".format(verb_query, obj_query)

    return query

def querify_simple(text):
    word_list = text.split(' ')
    word_list = [word.strip() + '~' for word in word_list]
    query = '+'.join(word_list)
    return query


def aggregate_freq(api_response):
    # Response looks like this:
    ngrams = api_response['ngrams']
    total_freq = 0
    
    for ngram in ngrams:
        total_freq += ngram['absTotalMatchCount']
    
    return total_freq



def get_frequency(text):
    text_query = querify(text)
    text_query_wildcard = querify(text, join_with_star=True)
    
    api_response = call_api(text_query)
    api_response_wildcard = call_api(text_query_wildcard)
    
    freq = aggregate_freq(api_response)
    freq_wildcard = aggregate_freq(api_response_wildcard)

    final_freq = freq + freq_wildcard

    return final_freq

def get_frequency_simple(text):
    text_query = querify_simple(text)

    api_response_text = call_api(text_query)

    freq_text = aggregate_freq(api_response_text)

    return freq_text



def process_file(file_path, ignore_header=False):
    actions = []
    with open(file_path, 'r') as file:
        for num_line, line in enumerate(file):
            if ignore_header and num_line == 0:
                continue
            line = line.strip()
            action = line.split(',')
            action = [action[0].strip(), action[1].strip()]  # Verb and object
            actions.append(action)
    return actions

def process_text(text):
    text = text.strip()
    action = text.split(',')
    action = [action[0].strip(), action[1].strip()]  # Verb and object
    actions = [action]
    return actions

def parse_underscore(actions):
    new_actions = []
    for action in actions:
        if action[0] == 'no_interaction':
            new_verb = 'and'
        else:
            new_verb = action[0].replace('_', ' ')
        
        new_obj = action[1].replace('_', ' ')
        new_action = [new_verb, new_obj]
        new_actions.append(new_action)
    return new_actions

def get_every_combination(actions):
    new_actions = []
    verbs = set([action[0] for action in actions])
    objects = set([action[1] for action in actions])
    for verb in verbs:
        for obj in objects:
            new_actions.append([verb, obj])
    return new_actions

def worker_function(a):
    action = a[0]
    action_name = a[1]
    action_freq = get_frequency(action)
    line_contents = '{},{},{}'.format(action_name[0], action_name[1], action_freq)
    return line_contents

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve HOI frequencies')
    parser.add_argument('--file', help='Path to the input file')
    parser.add_argument('--text', help='Input text')
    parser.add_argument('--ignore-header', action='store_true', help='Ignore the header of the csv file')
    parser.add_argument('--parse-underscore', action='store_true', help='Convert undersdores to spaces')
    parser.add_argument('--get-every-combination', action='store_true', help='Get every verb-object combination')
    parser.add_argument('--save', action='store_true', help='Save the results to a csv file')
    parser.add_argument('--parallel', action='store_true', help='Perform API calls in parallel')

    args = parser.parse_args()

    if args.file:
        actions = process_file(args.file, ignore_header=args.ignore_header)
    elif args.text:
        actions = process_text(args.text)
    else:
        print("Please provide either a file or text as input.")
        raise SystemExit
    
    if args.get_every_combination:
        actions = get_every_combination(actions)

    if args.parse_underscore:
        base_actions = actions
        actions = parse_underscore(actions)
    else:
        base_actions = actions
    
    
    if args.parallel:
        with mp.Pool(mp.cpu_count()) as pool:
            # We use tqdm to show a progress bar
            results = list(tqdm.tqdm(pool.imap(worker_function, zip(actions, base_actions)), total=len(actions)))
    else:
        results = []
        for action, action_name in zip(actions, base_actions):
            line_contents = worker_function((action, action_name))
            results.append(line_contents)
            print(line_contents)
    
    if args.save:
        file_name = os.path.splitext(os.path.basename(args.file))[0]
        if args.get_every_combination:
            file_name_freq = '{}_ngrams_all.csv'.format(file_name)
        else:
            file_name_freq = '{}_ngrams.csv'.format(file_name)
        with open(file_name_freq, 'w') as file:
            file.write('Verb,Object,Frequency\n')
            file.write('\n'.join(results))

        # We also get the frequency of the verbs and objects
        # For verbs:
        verbs = set([action[0] for action in base_actions])
        base_verbs = verbs
        if args.parse_underscore:
            fake_verb_actions = [[verb, ''] for verb in verbs]
            fake_verb_actions = parse_underscore(fake_verb_actions)
            verbs = [action[0] for action in fake_verb_actions]
        
        results_verbs = []
        for verb, verb_name in zip(verbs, base_verbs):
            verb_freq = get_frequency_simple(verb)
            line_contents = '{},{}'.format(verb_name, verb_freq)
            results_verbs.append(line_contents)
            print(line_contents)

        file_name_verbs = '{}_ngrams_verbs.csv'.format(file_name)
        with open(file_name_verbs, 'w') as file:
            file.write('Verb,Frequency\n')
            file.write('\n'.join(results_verbs))
        
        # For objects:
        objects = set([action[1] for action in base_actions])
        base_objects = objects
        if args.parse_underscore:
            fake_obj_actions = [['', obj] for obj in objects]
            fake_obj_actions = parse_underscore(fake_obj_actions)
            objects = [action[1] for action in fake_obj_actions]

        results_objects = []
        for obj, obj_name in zip(objects, base_objects):
            obj_freq = get_frequency_simple(obj)
            line_contents = '{},{}'.format(obj_name, obj_freq)
            results_objects.append(line_contents)
            print(line_contents)

        file_name_objects = '{}_ngrams_objects.csv'.format(file_name)
        with open(file_name_objects, 'w') as file:
            file.write('Object,Frequency\n')
            file.write('\n'.join(results_objects))