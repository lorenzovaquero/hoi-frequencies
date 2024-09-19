# hoi-frequencies
N-gram retriever for HOI

```bash
./get_interactions.py --file hicodet_anno.pth

./get_freq_ngrams.py --file hicodet_anno_interactions.csv --ignore-header --parse-underscore --get-every-combination --parallel --save

./merge_datasets.py --file-hoi hicodet_anno_interactions.csv --file-ngrams hicodet_anno_interactions_ngrams_all.csv --file-verb-hoi hicodet_anno_verbs.csv --file-obj-hoi hicodet_anno_objects.csv --file-verb-ngrams hicodet_anno_interactions_ngrams_verbs.csv --file-obj-ngrams hicodet_anno_interactions_ngrams_objects.csv --allow-mismatch --output hicodet_anno_stats.csv

./plot_correlation.py --file hicodet_anno_stats.csv --ignore-no_interaction
```