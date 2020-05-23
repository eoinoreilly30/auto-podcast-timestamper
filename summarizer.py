import logging
import subprocess
import sys

from pytorch_transformers import BertTokenizer

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def tokenize(input_string, output_file):
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    tokens = tokenizer.tokenize(input_string)
    line = " ".join(tokens)
    line = '{}\n'.format(line)

    with open(output_file, 'w', encoding='utf-8') as src:
        src.write(line)


def preprocess_input(input_prefix, prophet_net_path, preprocessed_files_dir, workers):
    command = ["fairseq-preprocess",
               "--no-progress-bar",
               "--user-dir", prophet_net_path + "prophetnet",
               "--task", "translation_prophetnet",
               "--source-lang", "src",
               "--target-lang", "tgt",
               "--testpref", input_prefix,
               "--destdir", preprocessed_files_dir,
               "--srcdict", prophet_net_path + "vocab.txt",
               "--tgtdict", prophet_net_path + "vocab.txt",
               "--workers", str(workers)]

    try:
        subprocess.check_output(command)
        logging.debug("successfully tokenized")
    except subprocess.CalledProcessError as err:
        logging.error("return code " + str(err.returncode) + ", output: " + str(err.output))


def generate_summary(prophet_net_path, preprocessed_files_dir, output_filename, model_path, length_penalty):
    generate_command = ["fairseq-generate", preprocessed_files_dir,
                        "--path", model_path,
                        "--user-dir", prophet_net_path + "prophetnet",
                        "--task", "translation_prophetnet",
                        "--batch-size", "80",
                        "--gen-subset", "test",
                        "--beam", "4",
                        "--num-workers", "4",
                        "--lenpen", str(length_penalty)]

    grep = ["grep", "^H", output_filename]
    cut = ["cut", "-c", "3-"]
    sort = ["sort", "-n"]
    cut2 = ["cut", "-f3-"]
    sed = ["sed", '"s/ ##//g"']

    try:
        with open(output_filename, "w") as out:
            subprocess.check_call(generate_command, stdout=out)
        logging.debug("successfully generated unparsed summary")
    except subprocess.CalledProcessError as err:
        logging.error("return code " + str(err.returncode) + ", output: " + str(err.output))

    try:
        result = subprocess.check_output(extract_result_command)
        logging.debug("successfully parsed summary")
        return result
    except subprocess.CalledProcessError as err:
        logging.error("return code " + str(err.returncode) + ", output: " + str(err.output))


def summarize(input_string):
    prophetnet_path = "summary-runtime-files/"
    preprocessed_files_dir = prophetnet_path + "preprocessed_input/"
    tokenized_dir = preprocessed_files_dir + "tokenized"
    unparsed_summary_path = preprocessed_files_dir + "summary.txt"
    model_path = prophetnet_path + "models/cnndm.pt"
    length_pen = 0.8

    tokenize(input_string, tokenized_dir + ".src")
    preprocess_input(tokenized_dir, prophetnet_path, preprocessed_files_dir, 20)

    return generate_summary(prophetnet_path, preprocessed_files_dir, unparsed_summary_path, model_path, length_pen)
