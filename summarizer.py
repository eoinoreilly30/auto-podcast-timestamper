import logging
import os
import subprocess
import sys
import config
from pytorch_transformers import BertTokenizer


def tokenize(input_string, output_file):
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    tokens = tokenizer.tokenize(input_string)
    line = " ".join(tokens)
    line = '{}\n'.format(line)

    with open(output_file + ".src", 'w', encoding='utf-8') as src:
        src.write(line)

    with open(output_file + ".tgt", 'w', encoding='utf-8') as tgt:
        tgt.write("line")


def summarize(input_string, request_dir, model_dir):
    os.makedirs(request_dir, exist_ok=True)

    tokenized = request_dir + "tokenized"
    model = model_dir + config.summarizer_model
    lenpen = config.lenpen

    tokenize(input_string, tokenized)

    try:
        return subprocess.check_output(["./summarizer.sh",
                                        tokenized,
                                        request_dir,
                                        model,
                                        lenpen,
                                        config.preprocessworkers,
                                        config.generateworkers,
                                        config.beam]).decode(sys.stdout.encoding).strip()
    except subprocess.CalledProcessError as e:
        logging.error("exit: " + str(e.returncode) + " output: " + str(e.output))
