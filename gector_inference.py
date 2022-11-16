# import libraries

import pandas as pd
from nltk import tokenize

from utils.helpers import read_lines
from gector.gec_model import GecBERTModel

# initialize model with fine-tuned checkpoints
try:
    model = GecBERTModel('./data/gector/output_vocabulary/',
                         model_paths=['./data/gector/model/model.th'],
                         weigths=None,
                         max_len=50,
                         min_len=3,
                         iterations=5,
                         lowercase_tokens=0,
                         log=False,
                         model_name='roberta',
                         special_tokens_fix=1,
                         is_ensemble=0,
                         min_error_probability=0.0,
                         confidence=0)
except FileNotFoundError:
    print("The file of the model has not been found where it should be (./data/gector/model/model.th)")
    print("You can download it from here:https://drive.google.com/file/d/1GXxl6mThLKBpImjFNpL9sRTYu4mR93kX/view?usp=sharing")


def predict_for_string(model, input_data, out_file, batch_size=16):
    """
    Categorizes each sentence in the string of sentences as grammatically correct (1) or incorrect (0)

    Args:
        model: initialized instance of GecBERTModel
        input_data: one input string containing sentences to be categorized. No \n assumed in the string
        batch_size: batch size over which inference is performed; default = 16
        out_file: path to csv file where classified data is written to sentence-wise

    """
    # split input string into sentences
    data = tokenize.sent_tokenize(input_data)
    predictions = []
    correctness_value = []
    batch = []
    cnt_corrections = 0
    for sent in data:
        batch.append(sent.split())
        if len(batch) == batch_size:
            preds, cnt = model.handle_batch(batch)
            predictions.extend(preds)
            cnt_corrections += cnt
            batch = []
    # for smaller batches
    if batch:
        preds, cnt = model.handle_batch(batch)
        predictions.extend(preds)
        cnt_corrections += cnt
    # put predicted tokens back into sentence
    predictions_sents = [" ".join(x) for x in predictions]
    # check if input sentence was grammatically correct
    for (s_in, s_out) in zip(data, predictions_sents):
        if s_in == s_out:
            correctness_value.append(0.5)
        else:
            correctness_value.append(0)
    # write classified data to csv
    # to be adjusted to corresponding endpoint for discussion task scoring
    pd.DataFrame({'sent_in': data, 'sent_out': predictions_sents,
                 'correctness_value': correctness_value}).to_csv(out_file)
