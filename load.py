import os

def load():
    folder = os.path.join(os.getcwd(), 'code')
    file_names = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    source_code = merge(folder, file_names)
    return source_code

def merge(folder, file_names):
    merged_code = ""
    for file_name in os.listdir(folder):
        file_path = os.path.join(folder, file_name)
        if os.path.isfile(file_path) and file_name != "view.py":
            with open(file_path, "r", encoding="utf-8") as file:
                merged_code += file.read()
    return merged_code