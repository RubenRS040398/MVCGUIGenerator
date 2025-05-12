from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import RobustScaler
import pandas as pd
import numpy as np
import sys

def preprocess_and_split(data):
    data_types = ['int', 'float', 'bool', 'complex', 'str', 'list', 'tuple', 'set', 'dict']
    new_data = data[data['Name'] != '__init__']
    if new_data.shape[1] == 52:
        X = new_data
        y = None
    else:
        X = new_data.iloc[:, :-1]
        y = new_data.iloc[:, -1]
    X = X.drop(columns=['Name', 'DefaultValue', 'PossibleValues', 'BelongsTo', 'ClassName', 'UsedByView'])
    for i in range(1, 11):
        X = X.drop(columns=['ArgumentName' + str(i), 'ArgumentType' + str(i), 'ReturnValueName' + str(i), 'ReturnValueType' + str(i)])
    one_hot_encoding = pd.get_dummies(X['Type'], prefix='Type')
    X = X.drop(columns=['Type'])
    X = pd.concat([one_hot_encoding, X], axis=1)
    for data_type in data_types:
        if 'Type_' + data_type not in X.columns.to_list():
            X['Type_' + data_type] = False
    scaler = RobustScaler()
    X['From'] = scaler.fit_transform(X[['From']])
    X['To'] = scaler.fit_transform(X[['To']])
    X = X[sorted(X.columns)]
    if 'Type_None' in X.columns:
        X = X.drop('Type_None', axis=1)
    return X, y

def classify(X_train, y_train, X_test):
    classifier = SGDClassifier(alpha=0.001, max_iter=100)
    classifier.fit(X_train, y_train)
    y_test = classifier.predict(X_test)
    return pd.DataFrame(y_test, columns=['Widget'])