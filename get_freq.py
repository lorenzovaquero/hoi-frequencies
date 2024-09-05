#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import requests

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

    final_freq = max(freq, freq_wildcard)

    return final_freq



def process_file(file_path):
    actions = []
    with open(file_path, 'r') as file:
        for line in file:
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve HOI frequencies')
    parser.add_argument('--file', help='Path to the input file')
    parser.add_argument('--text', help='Input text')

    args = parser.parse_args()

    if args.file:
        actions = process_file(args.file)
    elif args.text:
        actions = process_text(args.text)
    else:
        print("Please provide either a file or text as input.")
        raise SystemExit
    
    for action in actions:
        action_freq = get_frequency(action)
        print('{}: {}'.format(action, action_freq))
    
