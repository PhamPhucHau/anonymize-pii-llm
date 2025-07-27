from functools import wraps
import re
from faker import Faker
import spacy
import uuid


class Anonymizer:
    def __init__(self, custom_patterns=None, keep_default=True):
        self.fake = Faker()
        self.load_spacy_model()

        # Extract valid labels from the NLP model
        self.valid_labels = set(label for label
                                in self.nlp.get_pipe("ner").labels)

        # # Define default regex patterns
        # person_pattern = "PERSON"
        # phone_pattern = r"\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}" # noqa
        # email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        # credit_card_pattern = r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}'
        # address_pattern = r'\d{1,5}\s\w+(\s\w+)*,\s\w+,\s\w+(\s\w+)*'

        # Initialize pattern functions
        self.pattern_functions = [
            self.create_anonymize_function()
        ]

        # Keep default patterns if specified
        # if keep_default or custom_patterns is None:
        #     self.pattern_functions.extend([
        #         self.create_anonymize_function(person_pattern,
        #                                        self.fake.name),
        #         self.create_anonymize_function(phone_pattern,
        #                                        self.fake.phone_number),
        #         self.create_anonymize_function(email_pattern,
        #                                        self.fake.email),
        #         self.create_anonymize_function(credit_card_pattern,
        #                                        self.fake.credit_card_number),
        #         self.create_anonymize_function(address_pattern,
        #                                        self.fake.address),
        #     ])

        # # Add any custom patterns
        # if custom_patterns:
        #     for pattern, func in custom_patterns.items():
        #         self.pattern_functions.append(
        #             self.create_anonymize_function(pattern, func))

    def load_spacy_model(self):
        try:
            self.nlp = spacy.load("pii_ner_model")
        except: # noqa
            print("Model not found. Downloading pii_ner_model...")
            # spacy.cli.download("en_core_web_sm")
            # self.nlp = spacy.load("en_core_web_sm")

    def generate_unique_fake(self, original, generator_func):
        fake_value = generator_func()
        while fake_value == original:
            fake_value = generator_func()
        return fake_value

    def create_anonymize_function(self):
        def anonymize_func(sentence, anon_sentence, mappings):
            doc = self.nlp(sentence)
            for ent in doc.ents:
                uuid = str(uuid.uuid4())
                fake_data = `[${ent.label_}_${uuid}]`
                data_map[ent.text] = fake_data
                anon_sentence = anon_sentence.replace(ent.text, fake_data)
                mappings[ent.label_] = data_map
            }
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
