from telegram.ext import BaseFilter

class TextList(BaseFilter):
    def __init__(self, list, case_sensitive = False):
        self.case_sensitive = case_sensitive
        if self.case_sensitive:
            self.list = list
        else: 
            self.list = [s.lower() for s in list]

    def filter(self, message):
        if message.text:
            if self.case_sensitive:
                return message.text in self.list
            else:
                return message.text.lower() in self.list
        else:
            return False

    def __call__(self, update):
        return self.filter(update.message)