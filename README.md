# Data Matching

## Short Description
This repo consists of a source code of a Python script which takes an input file and and output file and tries to match the records depneding on a field. The output is a file with each row containing one set of matches. 

## Relevant aspects
* The matching used is fizzy matching on tokenized matching field
* If the field is not with latin latters, the field is translated to English to make sure that all fields are using the same alphabet which aids in the matching
* The matching alforithm allows for customization on which field is used for matching, which field is printed in the output file as well as the threshold for something to be considered a match.

## Local environment setup

### For development
```
pip install -r requirements-dev.txt
pre-commit install
```

### For running the code
```
pip install -r requirements.txt
```

## Test reproducibility and relevant aspects
* The input and outfile files are compulary command line arguments
* The inpit file should always be a .csv file
* adding `-mf` or `--match_field` as optional command line arguments allows the selection of another matching attribute. The default values is `Address`
* adding `-of` or `--output_field` as optional command line arguments allows the to use another field to print in the output. The default values is `Name`
* adding `-t` or `--threshold` as optional command line arguments allows us to change the matching threshold. The matching threashold can be between 0 and 100 with 100 being an exact match. The default values is `70`
