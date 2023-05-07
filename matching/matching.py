import logging
import sys

import pandas as pd
from alphabet_detector import AlphabetDetector
from thefuzz import fuzz, process
from translate import Translator

logging.basicConfig()
logging.root.setLevel(logging.NOTSET)

logger = logging.getLogger("Matching")


class Matching:
    def __init__(
        self,
        matching_field: str,
        field_to_print: str,
        input_file_path: str,
        output_file_path: str,
        matching_threshold: int = 70,
    ) -> None:
        self.translator = Translator(to_lang="en", from_lang="autodetect")
        self.alphabet_detector = AlphabetDetector()

        if ".csv" not in input_file_path:
            logger.error("Your file needs to be csv")
            sys.exit(1)
        try:
            df = pd.read_csv(input_file_path)
        except FileNotFoundError:
            logger.error("Please provide a valid input file")
            sys.exit(1)
        self.df = df.reset_index()

        self.matching_field = matching_field
        self.field_to_print = field_to_print
        self.threshold = matching_threshold

    def translate_field(self, field_value: str) -> str:
        if not self.alphabet_detector.is_latin(field_value):
            translated_field = self.translator.translate(field_value)
            if "PLEASE SELECT TWO DISTINCT LANGUAGES" not in translated_field:
                return translated_field
        return field_value

    def find_matches(self, value_for_matching: str, unmatched_dict: dict) -> list:
        matches = []
        matched_data = process.extract(
            value_for_matching, unmatched_dict, scorer=fuzz.token_sort_ratio
        )
        for _field_value, score, key in matched_data:
            if score > self.threshold:
                matches.append(key)
        return matches

    def add_translated_values(self) -> None:
        normalized_values = []
        for _index, row in self.df.iterrows():
            normalized_value = self.translate_field(row[self.matching_field])
            normalized_values.append(normalized_value)
        self.df.insert(0, f"{self.matching_field} Normalized", normalized_values)

    def matching(self) -> None:
        matches_found = {}
        new_field_name = f"{self.matching_field} Normalized"
        for index, row in self.df.iterrows():
            if index not in matches_found:
                unmatched = self.df.query("index not in @matches_found.keys()")[
                    new_field_name
                ].to_dict()
                new_matches = self.find_matches(
                    row[new_field_name], unmatched_dict=unmatched
                )
                for match in new_matches:
                    matches_found[match] = index
        self.df["Match"] = self.df["index"].map(matches_found)

    def run_matching(self):
        self.add_translated_values()
        self.matching()

        for match in self.df.Match.unique():
            matched_data = ", ".join(
                self.df[self.df["Match"] == match][self.field_to_print].to_list()
            )
            logger.info(matched_data)


if __name__ == "__main__":
    matching = Matching(
        matching_field="Address",
        field_to_print="Name",
        input_file_path="/Users/mcpopova/Downloads/ResTecDevTask-sample_input_v1.csv",
        output_file_path="",
    )
    matching.run_matching()
