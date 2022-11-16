# This is where the two models go and the classification function
import language_tool_python
from src.backend.models.gector.gec_model import GecBERTModel


class GrammarClassifier():
    """
    A classifier that labels English input sentences as grammatically correct or
    grammatically incorrect. Combines grammarly's GECToR model and python-language-toolkit.
    """

    COMMON_ERRORS = ['COMMA_COMPOUND_SENTENCE',
                     'COMMA_COMPOUND_SENTENCE_2',
                     'WHO_WHOM',
                     'EN_A_VS_AN',
                     'HE_VERB_AGR',
                     'SUBJECT_VERB_AGREEEMENT',
                     'SUBJECT_VERB_AGREEMENT_PLURAL',
                     'DID_PAST',
                     'SINGULAR_AGREEMENT_SENT_START',
                     'AGREEMENT_SENT_START']

    # categories of errors that should be ignored altogether
    BAD_ERROR_CATEGORIES = ['STYLE', 'TYPOGRAPHY', 'REDUNDANCY', 'CASING']
    # specific errors from other categories that should be ignored
    BAD_ERRORS = ['DOUBLE_PUNCTUATION',
                  'PUNCTUATION_PARAGRAPH_END',
                  'EN_CONSISTENT_APOS',
                  'EN_UNPAIRED_BRACKETS',
                  'APOS_SPACE_CONTRACTION [1]',
                  'UPPERCASE_SENTENCE_START',
                  'EN_SPECIFIC_CASE',
                  'CHILDISH_LANGUAGE',
                  'EN_QUOTES']

    def __init__(self):
        """
        Initializes a GrammarClassifier.
        """
        try:
            self.gector_model = GecBERTModel(
                './data/gector/output_vocabulary/',
                model_paths=['./data/gector/model/model.th'],
                weigths=None, max_len=50, min_len=3, iterations=5,
                lowercase_tokens=0, log=False, model_name='roberta',
                special_tokens_fix=1, is_ensemble=0, min_error_probability=0.0,
                confidence=0)
        except FileNotFoundError:
            print(
                "The file of the model has not been found where it should be (./data/gector/model/model.th)")
            print("You can download it from here: https://drive.google.com/file/d/1GXxl6mThLKBpImjFNpL9sRTYu4mR93kX/view?usp=sharing")

        self.language_tool = language_tool_python.LanguageTool('en-US')
        # make test classification to start the python language tool
        self.language_tool.check('This is a test sentence.')

    def classify(self, sent: str) -> tuple:
        """
        Identifies errors and calculates a correctness value for a given string.

        Parameters
        ----------
            sent : str
                The sentence to be evaluated.

        Returns
        -------
            A tuple consisting of:
            - the correctness value of the sentence (in float)
            - the list of error types that were detected for the sentence
        """
        error_types = []
        correctness_value = 1

        # determine correctness according to python_language_toolkit
        error_matches = self.language_tool.check(sent)
        for error in error_matches:
            if (error.category not in self.BAD_ERROR_CATEGORIES) and (error.ruleId not in self.BAD_ERRORS):
                if error.ruleId in self.COMMON_ERRORS:
                    error_types.append(error.ruleId)
        if error_types:
            return (0, error_types)
        if error_matches:
            correctness_value -= 0.5

        # determine correctness according to GECToR
        pred, _ = self.gector_model.handle_batch([sent.split()])
        pred = " ".join(pred[0])
        if sent.lower() != pred.lower():
            correctness_value -= 0.5

        return (correctness_value, [])
