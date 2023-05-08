from unittest.mock import MagicMock

import pandas as pd
from pkg_resources import resource_filename

from matching.matching import DataMatcher

input_file_path = resource_filename(
    "test",
    "data/input.csv",
)

dm = DataMatcher(
    matching_field="address",
    field_to_print="name",
    input_file_path=input_file_path,
    output_file_path="data/output.csv",
)


def test_find_matches():
    assert (
        dm.find_matches("Yulin Rd, Xuhui District, Shanghai", {"key2": "北京市海淀区"}) == []
    )
    assert (
        dm.find_matches("北京市海淀区", {"key": "Yulin Rd, Xuhui District, Shanghai"}) == []
    )
    assert dm.find_matches("北京市海淀区", {"key1": "北京市海淀区", "key2": "东城区"}) == ["key1"]


def test_translate_field():
    assert dm.translate_field("北京市海淀区") == "Haidian District, Beijing"
    assert dm.translate_field("Tokyo, Japan") == "Tokyo, Japan"
    assert dm.translate_field("蘋果") == "Apples"


def test_add_translated_values_calls_translate_field_for_each_row():
    dm.translate_field = MagicMock(return_value="translated value")

    dm.add_translated_values()

    assert dm.translate_field.call_count == len(dm.df)


def test_add_translated_values_adds_translated_column_to_df():
    dm = DataMatcher(
        matching_field="address",
        field_to_print="name",
        input_file_path=input_file_path,
        output_file_path="data/output.csv",
    )
    dm.add_translated_values()

    assert dm.df.columns[0] == f"{dm.matching_field} translated"


def test_add_translated_values_translates_non_latin_values():
    dm = DataMatcher(
        matching_field="address",
        field_to_print="name",
        input_file_path=input_file_path,
        output_file_path="data/output.csv",
    )
    dm.df.loc[0, dm.matching_field] = "здравей"

    dm.add_translated_values()

    assert dm.df.iloc[0, 0] == "hi"


def test_matching_with_dataframe_of_one_row():
    data = {
        "index": [0],
        "name": ["Alice"],
        "name translated": ["Alicia"],
    }
    dm.df = pd.DataFrame(data).reset_index()
    dm.matching_field = "name"
    dm.matching()
    assert dm.df["Match"].to_list() == [0]


def test_matching_with_empty_dataframe():
    dm.df = pd.DataFrame().reset_index()
    dm.matching()
    assert dm.df.empty


def test_matching_with_no_identical_data():
    data = {
        "index": [0, 1, 2],
        "name": ["Alice", "Bob", "Charlie"],
        "name translated": ["Alicia", "Bobby", "Charlotte"],
    }
    dm.df = pd.DataFrame(data).reset_index()
    dm.matching_field = "name"
    dm.matching()
    assert dm.df["Match"].to_list() == [0, 1, 2]


def test_matching_with_partially_identical_data():
    data = {
        "index": [0, 1, 2],
        "name": ["Alice K", "Bob", "Alice Kate"],
        "name translated": ["Alice K", "Bob", "Alice Kate"],
    }
    dm.df = pd.DataFrame(data).reset_index()
    dm.matching_field = "name"
    dm.matching()
    assert dm.df["Match"].tolist() == [0, 1, 0]


def test_matching_with_identical_data():
    data = {
        "index": [0, 1, 2],
        "name": ["Alice", "Bob", "Alice"],
        "name translated": ["Alice", "Bob", "Alice"],
    }
    dm.df = pd.DataFrame(data).reset_index()
    dm.matching_field = "name"
    dm.matching()
    assert dm.df["Match"].tolist() == [0, 1, 0]
