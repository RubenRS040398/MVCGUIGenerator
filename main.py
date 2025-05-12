from load import *
from scanner import *
from model import *
from refiner import *
from generator import *

source_code = load_source_code()
train = load_train_data()
test = scan(source_code)
init_data = test[test['Name'] == '__init__'].reset_index(drop=True)
model_data = test[test['Name'] != '__init__'].reset_index(drop=True)
model_data = model_data[model_data['UsedByView'] == False].reset_index(drop=True)
test = test[test['Name'] != '__init__'].reset_index(drop=True)
test = test[test['UsedByView'] == True].reset_index(drop=True)
X_train, y_train = preprocess_and_split(train)
X_test, _ = preprocess_and_split(test)
y_test = classify(X_train, y_train, X_test)
main_data = pd.concat([test, y_test], axis=1)
main_data = refine(main_data, "ControladorEstudiant")
generate(main_data, init_data, model_data, "ControladorEstudiant", "Per defecte", "Copyright 2025", show_model_attr=True)