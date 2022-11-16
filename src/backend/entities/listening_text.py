class ListeningText():
    '''
    Object representing
    a single listening text
    and associated metadata,
    including questions and answers
    '''

    def __init__(
        self,
        text_id: int,
        topic: str,
        sub_types: int,
        text: str,
        difficulty: int,
        questions: set,
    ) -> None:
        '''
        Parameters
        ---------
            text_id : int
                Table ID (PK) for the
                retrieved listening text data.
            text : str
                The introductory listening
                text itself.
            topic : str
                A general topic describing
                the listening text and questions.
            proficiency_domain : int
                Vocabulary domain for the text,
                corresponding to a domain in the
                user proficiency model.
            difficulty : int
                Text / question difficulty for
                proficiency model.
            questions : set
                Discussion questions.
        '''
        self.text_id = text_id
        self.text = text
        self.topic = topic
        self.proficiency_domain = sub_types
        self.difficulty = difficulty
        self.questions = questions

    def get_text(self):
        temp = self.text.replace('\n', '')
        clean_text = temp.replace('. ', '.\n')
        return clean_text

    def get_text_id(self):
        return self.text_id

    def get_topic(self):
        return self.topic

    def get_proficiency_domain(self):
        return self.proficiency_domain

    def get_difficulty(self):
        return self.difficulty

    def get_new_question(self):
        '''
        Returns a new question from
        the set of available questions,
        removing the presented
        question from the
        class attribute.
        Returns
        ---------
            question : str
                Discussion question.
        '''
        return self.questions.pop(0)
