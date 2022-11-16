class Word():

    def __init__(self, word, sub_types):
        wordlist = word.split(";")
        self.alternatives = []
        if len(wordlist) > 1:
            self.alternatives = wordlist[1:]
        self.word = wordlist[0].capitalize()
        self.sub_types = sub_types

    def get_word(self):
        return self.word

    def get_alternatives(self):
        return self.alternatives

    def get_proficiency_sub_types(self):
        return self.sub_types

    def __str__(self):
        return self.word

    def __repr__(self):
        return str(self)
