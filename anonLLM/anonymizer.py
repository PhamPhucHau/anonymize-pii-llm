from functools import wraps
import re
from faker import Faker
import spacy
import random


class Anonymizer:
    def __init__(self, custom_patterns=None, keep_default=True):
        self.fake = Faker()
        self.load_spacy_model()

        # Extract valid labels from the NLP model
        self.valid_labels = set(label for label
                                in self.nlp.get_pipe("ner").labels)
        
        self.all_ids = [f"{i:04d}" for i in range(10000)]
        random.shuffle(self.all_ids)

        # Initialize pattern functions
        self.pattern_functions = [
            self.create_anonymize_function()
        ]

    def load_spacy_model(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
            #self.nlp = spacy.load("pii_ner_model")
            
        except: # noqa
            
            print("Model not found. Downloading pii_ner_model...")

    def generate_unique_fake(self, original, generator_func):
        fake_value = generator_func()
        while fake_value == original:
            fake_value = generator_func()
        return fake_value

    def create_anonymize_function(self):
        def anonymize_func(sentence, anon_sentence, mappings):
            doc = self.nlp(sentence)
            for ent in doc.ents:
                try:
                    data_map = mappings[ent.label_] if ent.label_ in mappings else {}
                    uuid = str(self.all_ids.pop())
                    fake_data = f'[{ent.label_}_{uuid}]'
                    data_map[ent.text] = fake_data
                    anon_sentence = anon_sentence.replace(ent.text, fake_data)
                    mappings[ent.label_] = data_map
                except Exception as e:
                    print("Error", e)
            return anon_sentence
        return anonymize_func

    def anonymize_data(self, sentence):
        anon_sentence = sentence
        mappings = {}
        for pattern_function in self.pattern_functions:
            anon_sentence = pattern_function(sentence, anon_sentence, mappings)
        return anon_sentence, mappings

    def anonymize(self, *args_to_anonymize):
        def inner_decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                for arg_name in args_to_anonymize:
                    if arg_name in kwargs:
                        anonymized_data, _ = self.anonymize_data(
                            kwargs[arg_name])
                        kwargs[arg_name] = anonymized_data
                return func(*args, **kwargs)
            return wrapper
        return inner_decorator
