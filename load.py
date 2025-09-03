import os
import pandas as pd

def load_source_code():
    """
    Loads the source code found in the /code folder.

    Return:

    - source_code (str): The whole source code.
    """
    folder = os.path.join(os.getcwd(), 'code')
    file_names = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f.endswith('.py')]
    source_code = merge(folder, file_names)
    return source_code

def merge(folder, file_names, data=False):
    """
    Merge files into a single output format, whether it's the entire source code or training data.

    Param:

    - folder (str): The folder where the files are located.
    - file_names (list): List of file names (these can be .py/.xlsx files).
    - data (bool): Indicates whether is data or not (default is False).

    Return:

    - merged (str/pandas.core.frame.DataFrame): The merged data in its respective format.
    """
    merged = None
    if not data:
        merged = ""
    else:
        merged = pd.DataFrame()
    for file_name in file_names:
        file_path = os.path.join(folder, file_name)
        if not data:
            if os.path.isfile(file_path) and file_name not in ['main.py', 'view.py', 'utilities.py']:
                with open(file_path, "r", encoding="utf-8") as file:
                    merged += file.read()
        else:
            if os.path.isfile(file_path):
                print(file_path)
                dataframe = pd.read_excel(file_path)
                merged = pd.concat([merged, dataframe], ignore_index=True)
    return merged

def load_train_data():
    """
    Loads the training data found in the /data folder.

    Return:

    - train_data (pandas.core.frame.DataFrame): The whole training dataset.
    """
    folder = os.path.join(os.getcwd(), 'data')
    file_names = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f.endswith('.xlsx')]
    train_data = merge(folder, file_names, True)
    return train_data