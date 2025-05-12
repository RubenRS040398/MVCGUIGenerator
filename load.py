import os
import pandas as pd

def load_source_code():
    folder = os.path.join(os.getcwd(), 'code')
    file_names = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    source_code = merge(folder, file_names)
    return source_code

def merge(folder, file_names, data=False):
    merged = None
    if not data:
        merged = ""
    else:
        merged = pd.DataFrame()
    for file_name in file_names:
        file_path = os.path.join(folder, file_name)
        if not data:
            if os.path.isfile(file_path) and file_name not in ['main.py', 'view.py']:
                with open(file_path, "r", encoding="utf-8") as file:
                    merged += file.read()
        else:
            if os.path.isfile(file_path):
                print(file_path)
                dataframe = pd.read_excel(file_path)
                merged = pd.concat([merged, dataframe], ignore_index=True)
    return merged

def load_train_data():
    folder = os.path.join(os.getcwd(), 'data')
    file_names = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    train_data = merge(folder, file_names, True)
    return train_data