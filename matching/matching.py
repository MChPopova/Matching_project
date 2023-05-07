import argparse
import logging
import sys

import pandas as pd
from alphabet_detector import AlphabetDetector
from thefuzz import fuzz, process
from translate import Translator

logging.basicConfig()
logging.root.setLevel(logging.NOTSET)

logger = logging.getLogger("Matching")


class DataMatcher:
    """
    Class that performs fuzzy matching on a CSV file.

    Args:
    matching_field (str): Name of the field to perform matching on.
    field_to_print (str): Name of the field to print in the output file.
    input_file_path (str): Path to the input CSV file.
    output_file_path (str): Path to the output CSV file.
    matching_threshold (int, optional): Minimum score required to consider a match. Defaults to 70.
    """

    def __init__(
        self,
        matching_field: str,
        field_to_print: str,
        input_file_path: str,
        output_file_path: str,
        matching_threshold: int = 70,
    ) -> None:
        """
        Initializes the DataMatcher object.

        Raises:
        FileNotFoundError: If the input file is not found.
        """
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
        if matching_field in df.columns:
            self.matching_field = matching_field
        else:
            logger.error("Matching Field is not part of dataframe")
            sys.exit(1)
        if field_to_print in df.columns:
            self.field_to_print = field_to_print
        else:
            logger.error("Print Field is not part of dataframe")
            sys.exit(1)
        assert (
            matching_threshold > 0 and matching_threshold < 100
        ), "threshold should be between 0 and 100"
        self.threshold = matching_threshold
        self.output_file_path = output_file_path

    def translate_field(self, field_value: str) -> str:
        """
        Translates a field value from non-Latin script to Latin script if necessary.

        Args:
        field_value (str): The value of the field to translate.

        Returns:
        str: The translated field value, or the original field value if no translation was necessary.

        """
        if not self.alphabet_detector.is_latin(field_value):
            translated_field = self.translator.translate(field_value)
            if "PLEASE SELECT TWO DISTINCT LANGUAGES" not in translated_field:
                return translated_field
        return field_value

    def find_matches(self, value_for_matching: str, unmatched_dict: dict) -> list:
        """
        Finds all keys in a dictionary of string values that match a given string value within a certain threshold.

        Args:
        value_for_matching (str): The string value to match against.
        unmatched_dict (dict): A dictionary of string values to search for matches.

        Returns:
        list: A list of keys from the unmatched_dict that match the value_for_matching within the given threshold.

        """
        matches = []
        matched_data = process.extract(
            value_for_matching, unmatched_dict, scorer=fuzz.token_sort_ratio
        )
        for _field_value, score, key in matched_data:
            if score > self.threshold:
                matches.append(key)
        return matches

    def add_translated_values(self) -> None:
        """
        Adds translated values to the dataframe.

        For each row in the dataframe, the value in the matching_field column is translated if necessary,
        and the resulting value is added as a new column to the left of the original column.

        Args:
            self (object): The instance of the object.

        Returns:
            None: The function does not return any value.
        """
        translated_values = []
        for _index, row in self.df.iterrows():
            translated_value = self.translate_field(row[self.matching_field])
            translated_values.append(translated_value)
        self.df.insert(0, f"{self.matching_field} translated", translated_values)

    def matching(self) -> None:
        """
        Finds and sets the matches between the rows in the dataframe based on translated field.

        This function uses the find_matches() function to compare the translated field of each row with the translated field of
        the remaining rows to find the potential matches based on the similarity score. Then it sets the match column in the
        dataframe as the index of the matched row.

        Args:
        None

        Returns:
        None
        """
        matches_found = {}
        new_field_name = f"{self.matching_field} translated"
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

    def run_matching(self) -> None:
        """
        Matches the similar values in the DataFrame and saves the matches in a file

        """
        self.add_translated_values()
        self.matching()
        f = open(self.output_file_path, "w")

        for match in self.df.Match.unique():
            matched_data = ", ".join(
                self.df[self.df["Match"] == match][self.field_to_print].to_list()
            )
            f.write(f"{matched_data}\n")
            logger.info(matched_data)

        f.close()


def parse_opts():
    """Parse command line arguments.

    Returns:
        Namespace: an object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Matches data from a csv file using a particular field and saves the data to a new file"
    )
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("-mf", "--match_field", default="Address")
    parser.add_argument("-of", "--output_field", default="Name")
    parser.add_argument("-t", "--threshold", default=70, type=int)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_opts()

    data_matcher = DataMatcher(
        matching_field=args.match_field,
        field_to_print=args.output_field,
        input_file_path=args.input,
        output_file_path=args.output,
        matching_threshold=args.threshold,
    )
    data_matcher.run_matching()
