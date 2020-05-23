import logging
import subprocess
import sys
import os

from pytorch_transformers import BertTokenizer

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def tokenize(input_string, output_file):
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    tokens = tokenizer.tokenize(input_string)
    line = " ".join(tokens)
    line = '{}\n'.format(line)

    with open(output_file + ".src", 'w', encoding='utf-8') as src:
        src.write(line)

    with open(output_file + ".tgt", 'w', encoding='utf-8') as tgt:
        tgt.write("line")


def summarize(input_string, request_id):
    request_dir = "./requests-files/" + request_id + "/"
    tokenized = request_dir + "tokenized"
    os.makedirs(request_dir, exist_ok=True)
    model = "./models/cnndm.pt"
    lenpen = "0.8"

    tokenize(input_string, tokenized)

    try:
        return subprocess.check_output(["./summarizer.sh",
                                        tokenized,
                                        request_dir,
                                        model,
                                        lenpen]).decode(sys.stdout.encoding).strip()
    except subprocess.CalledProcessError as e:
        logging.error("exit: " + str(e.returncode) + " output: " + str(e.output))
