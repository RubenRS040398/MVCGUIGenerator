from matplotlib import pyplot as plt
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import make_scorer, accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import cross_validate, GridSearchCV, learning_curve
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

def preprocess_and_split(train_data, test_data):
    """
    Preprocesses the data and divides it into independent variables (x) and target variables (y).

    Param:

    - train_data (pandas.core.frame.DataFrame): The whole training dataset.
    - test_data (pandas.core.frame.DataFrame): The whole test dataset.

    Return:

    - x_train (pandas.core.frame.DataFrame): Independent variables from training dataset.
    - y_train (pandas.core.frame.DataFrame): Target variables from training dataset.
    - x_test (pandas.core.frame.DataFrame): Independent variables from test dataset.
    """
    x = pd.concat([train_data.iloc[:, :-1], test_data])
    x = x.reset_index(drop=True)

    data_types = ['int', 'float', 'bool', 'complex', 'str', 'list', 'tuple', 'set', 'dict']
    x = x[x['Name'] != '__init__'] # Exclude samples corresponding to constructors

    # Drops columns that will not be taken into account in learning.

    x = x.drop(columns=['Name', 'DefaultValue', 'BelongsTo', 'ClassName', 'UsedByView'])
    #x = x.drop(columns=['Name', 'DefaultValue', 'PossibleValues', 'BelongsTo', 'ClassName', 'UsedByView'])
    for i in range(1, 11):
        x = x.drop(columns=['ArgumentName' + str(i), 'ArgumentType' + str(i), 'ReturnValueName' + str(i), 'ReturnValueType' + str(i)])

    # Converts PossibleValues into numeric data.

    x['PossibleValues'] = x['PossibleValues'].fillna('')
    x['PossibleValues'] = x['PossibleValues'].str.count(',')
    one_hot_encoding = pd.get_dummies(x['Type'], prefix='Type') # Applies One-Hot Encoding on the Type column.
    x = x.drop(columns=['Type'])
    x = pd.concat([one_hot_encoding, x], axis=1)
    for data_type in data_types:
        if 'Type_' + data_type not in x.columns.to_list():
            x['Type_' + data_type] = False

    # Adds additional information regarding numeric limits.

    x['HasLowerBound'] = abs(x['From']) > 1e+290
    x['HasUpperBound'] = x['To'] > 1e+290
    x[['From', 'To']] = x[['From', 'To']].map(
        lambda z: 0.0 if abs(z) > 1e+290 else z # Converts numeric limits into zeros
    )
    x['FromTo'] = x['To'] - x['From']   # Merges From and To columns by substract
    x = x.drop(columns=['From', 'To'])
    scaler = StandardScaler()   # Applies StandardScaler() over FromTo column.
    x['FromTo'] = scaler.fit_transform(x[['FromTo']])
    x['PossibleValues'] = scaler.fit_transform(x[['PossibleValues']])
    x = x[sorted(x.columns)]
    if 'Type_None' in x.columns:
        x = x.drop('Type_None', axis=1)
    x_train = x.head(len(train_data))
    y_train = train_data.iloc[:, -1]
    x_test = x.tail(len(test_data)).reset_index(drop=True)
    return x_train, y_train, x_test


def fit(x_train, y_train):
    """
    Trains a logistic regression classifier using Stochastic Gradient Descent (SGD).

    Param:

    - x_train (pandas.core.frame.DataFrame): Independent variables from training dataset.
    - y_train (pandas.core.frame.DataFrame): Target variables from training dataset.

    Return:

    - classifier (sklearn.linear_model._stochastic_gradient.SGDClassifier): Trained model.
    """
    classifier = SGDClassifier(alpha=0.001, eta0=0.001, learning_rate='optimal', loss='log_loss', penalty='l2', max_iter=1000)
    classifier.fit(x_train, y_train)
    return classifier

def classify(classifier, x_test):
    """
    Classify using the independent variables of the test data.

    Param:

    - classifier (sklearn.linear_model._stochastic_gradient.SGDClassifier): Trained model.
    - x_test (pandas.core.frame.DataFrame): Independent variables from test dataset.

    Return:

    - result (pandas.core.frame.DataFrame): Target variables from training dataset.
    """
    y_test = classifier.predict(x_test)
    return pd.DataFrame(y_test, columns=['Widget'])

def evaulate(classifier, x_train, y_train):
    """
    Evaluates the trained model visualizing the metrics and the learning curve.

    Param:

    - classifier (sklearn.linear_model._stochastic_gradient.SGDClassifier): Trained model.
    - x_train (pandas.core.frame.DataFrame): Independent variables from training dataset.
    - y_train (pandas.core.frame.DataFrame): Target variables from training dataset.
    """
    metrics = {
        'accuracy': make_scorer(accuracy_score),
        'precision': make_scorer(precision_score, average='macro'),
        'recall': make_scorer(recall_score, average='macro'),
        'f1': make_scorer(f1_score, average='macro')
    }
    results = cross_validate(classifier, x_train, y_train, scoring=metrics, cv=4)   # Applies CV
    for metric in metrics:
        scores = results['test_' + metric]
        print(f'{metric[0].upper()}{metric[1:]}: Mean = {scores.mean():.3f}, Std = {scores.std():.3f}')

    # Displays the learning curve of the model

    train_sizes, train_scores, test_scores = learning_curve(classifier, x_train, y_train, cv=4, scoring='accuracy',
                                                            n_jobs=-1, train_sizes=np.linspace(0.1, 1.0, 10))
    train_scores_mean = np.mean(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    plt.figure(figsize=(6, 4))
    plt.plot(train_sizes, train_scores_mean, 'o-', label='Training', color='#bbbbbb')
    plt.plot(train_sizes, test_scores_mean, 'o-', label='Validation', color='#3f48cc')
    plt.xlabel('Training set size')
    plt.ylabel('Accuracy')
    plt.title('Learning curve')
    plt.legend()
    plt.grid(True)
    plt.show()

def get_best_hyperparameters(x_train, y_train):
    """
    Get the best hyperparameters of the model using a Grid Search.

    Param:

    - x_train (pandas.core.frame.DataFrame): Independent variables from training dataset.
    - y_train (pandas.core.frame.DataFrame): Target variables from training dataset.
    """
    pipeline = Pipeline([
        ('sgd', SGDClassifier(random_state=42))  # Clasificador
    ])
    param_grid = {
        'sgd__loss': ['hinge', 'log_loss', 'modified_huber'],
        'sgd__penalty': ['l2', 'l1', 'elasticnet'],
        'sgd__alpha': [1e-4, 1e-3, 1e-2],
        'sgd__learning_rate': ['constant', 'optimal', 'adaptive'],
        'sgd__eta0': [0.001, 0.01, 0.1],  # solo si learning_rate='constant'
    }
    grid_search = GridSearchCV(pipeline, param_grid, cv=3, scoring='accuracy', n_jobs=-1)
    grid_search.fit(x_train, y_train)
    print(grid_search.best_params_)