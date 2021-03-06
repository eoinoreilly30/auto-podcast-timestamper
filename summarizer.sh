#!/bin/bash

input_prefix=$1
output_dir=$2
model=$3
lenpen=$4
preprocessworkers=$5
generateworkers=$6
beam=$7

prophetnet_path=./prophetnet/

fairseq-preprocess \
--no-progress-bar \
--user-dir "$prophetnet_path" \
--task translation_prophetnet \
--source-lang src \
--target-lang tgt \
--testpref "$input_prefix" \
--destdir "$output_dir" \
--srcdict "$prophetnet_path/vocab.txt" \
--tgtdict "$prophetnet_path/vocab.txt" \
--workers "$preprocessworkers" \
> /dev/null

fairseq-generate "$output_dir" \
--path "$model" \
--user-dir "$prophetnet_path" \
--task translation_prophetnet \
--batch-size 80 \
--gen-subset test \
--beam "$beam" \
--num-workers "$generateworkers" \
--lenpen "$lenpen" \
> "$output_dir/unparsed_output.txt"

summary=$(grep ^H "$output_dir/unparsed_output.txt" | cut -c 3- | sort -n | cut -f3- | sed "s/ ##//g")

echo "$summary"