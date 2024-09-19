#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
import argparse
import seaborn as sns


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plots Database vs Ngrams frequencies')
    parser.add_argument('--file', help='Path to the input file', required=True)
    parser.add_argument('--ignore-no_interaction', action='store_true', help='Removes no_interaction from the interactions')

    args = parser.parse_args()

    # Load the data from CSV files
    # Files have a header with the columns: ['Interaction', 'Verb', 'Object', 'Interaction_freq_ngrams',  'Verb_freq_ngrams', 'Object_freq_ngrams', 'Interaction_freq_hoi', 'Verb_freq_hoi', 'Object_freq_hoi', 'IsRare_hoi']
    df = pd.read_csv(args.file, header=0)

    # We will remove the no_interaction from the database
    if args.ignore_no_interaction:
        df = df[df['Verb'] != 'no_interaction']

    
    # We will replace the IsRare_hoi column with a text column
    labels = {-1: 'Not in HOI', 0: 'Not rare', 1: 'Rare'}
    df['IsRare_hoi'] = df['IsRare_hoi'].map(labels)
    
    # We will plot the scatter plot and add color based on IsRare, with a legend where -1 = "Not in HOI", 0 = "Not rare", 1 = "Rare"
    colors = {'Not in HOI': 'black', 'Not rare': 'green', 'Rare': 'red'}

    # Let's create a 2x2 plot with the following scatter plots:
    fig, axs = plt.subplots(2, 2, figsize=(15, 8))

    # 1. Interaction_freq_ngrams vs Interaction_freq_hoi
    sns.scatterplot(ax=axs[0, 0], data=df, x='Interaction_freq_ngrams', y='Interaction_freq_hoi', hue='IsRare_hoi', palette=colors, s=5)
    corr_coef = df['Interaction_freq_ngrams'].corr(df['Interaction_freq_hoi'])
    axs[0, 0].set_title(f'Interaction Frequencies, HOI v.s ngrams (r={corr_coef:.2f})')
    axs[0, 0].legend(handles=[plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=10, label=label) for label, color in colors.items()])

    # 2. Verb_freq_ngrams vs Verb_freq_hoi
    sns.scatterplot(ax=axs[0, 1], data=df, x='Verb_freq_ngrams', y='Verb_freq_hoi', s=5) # Does not make sense to color by IsRare_hoi because all the dots are stacked
    corr_coef = df['Verb_freq_ngrams'].corr(df['Verb_freq_hoi'])
    axs[0, 1].set_title(f'Verb Frequencies, HOI v.s ngrams (r={corr_coef:.2f})')

    # 3. Object_freq_ngrams vs Object_freq_hoi
    sns.scatterplot(ax=axs[1, 0], data=df, x='Object_freq_ngrams', y='Object_freq_hoi', s=5) # Does not make sense to color by IsRare_hoi because all the dots are stacked
    corr_coef = df['Object_freq_ngrams'].corr(df['Object_freq_hoi'])
    axs[1, 0].set_title(f'Object Frequencies, HOI v.s ngrams (r={corr_coef:.2f})')

    # 4. Histogram of Interaction_freq_ngrams (stacked histogram colored by IsRare_hoi)
    # Discard outliers
    q_low = 0
    q_high = df['Interaction_freq_ngrams'].quantile(0.95)
    df_filtered = df[(df['Interaction_freq_ngrams'] > q_low) & (df['Interaction_freq_ngrams'] < q_high)]

    # Plot histogram
    sns.histplot(ax=axs[1, 1], data=df_filtered, x='Interaction_freq_ngrams', hue='IsRare_hoi', multiple='stack', palette=colors, bins=50)
    axs[1, 1].set_title('Distribution of ngrams Interaction frequencies (Filtered)')

    plt.tight_layout()
    plt.show()
    plt.close()