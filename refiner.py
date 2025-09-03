import langid
from collections import Counter
import pandas as pd

def refine(main_data, init_data, model_data, main_controller_name, show_model_attr, hide_model_attr, view_threshold=3, window_threshold=5):
    """
    Runs the refinement process.

    Param:

    - main_data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - init_data (pandas.core.frame.DataFrame): Model and Controller constructors data from the test dataset (methods only).
    - model_data (pandas.core.frame.DataFrame): Model data from the test dataset.
    - main_controller_name (str): The name of the main Controller.
    - show_model_attr (bool): Indicates whether the attributes of Models are displayed in the view.
    - hide_model_attr (bool): Indicates whether to hide Controller methods which return Model attributes.
    - view_threshold (int): The minimum number of Controllers to split the View into multiple Views. Default value is 3.
    - window_threshold (int): The minimum number of arguments/return values to display methods in a separate window. Default value is 5.

    Return:

    - refined_data (pandas.core.frame.DataFrame): The refined Controller data from the test dataset.
    - refined_model_data (pandas.core.frame.DataFrame): The refined Model data from the test dataset.
    """
    refined_data = set_languages(main_data)
    refined_data = set_methods_as_menu_buttons(refined_data, main_controller_name, view_threshold, window_threshold)
    refined_data = set_window_methods(refined_data, main_controller_name, window_threshold)
    refined_data = merge_arguments(refined_data)
    refined_data = merge_return_values(refined_data)
    refined_data = set_widget_label(refined_data, init_data, model_data)
    refined_data = set_widget_description(refined_data, init_data, model_data)
    refined_data, refined_model_data = set_hide_show_model_attr(refined_data, init_data, model_data, show_model_attr, hide_model_attr)
    refined_model_data = set_attr_description(refined_model_data)
    return refined_data, refined_model_data

def merge_arguments(data):
    """
    Joins samples of arguments that have the same name, data type, minimum and maximum values, default value,
    possible values, widget and where the method it belongs to is within the same Controller.

    Param:

    - data (pandas.core.frame.DataFrame): Controller data from the test dataset.

    Return:

    - merged_arguments (pandas.core.frame.DataFrame): Controller data from the test dataset with merged arguments.
    """
    merged_arguments = data

    # Do not join method arguments where the first ones are displayed in another window.

    arguments = data[data['Window'] == False]

    # Excludes IsAnArgument, IsAMethod, IsAReturnValue, BelongsTo and UsedByView columns (not essential to the argument
    # joining process).

    arguments = arguments[arguments['IsAnArgument'] == True].drop(columns=['IsAnArgument', 'IsAMethod', 'IsAReturnValue',
                                                                           'BelongsTo', 'UsedByView'])
    for i in range(1, 11):  # Also excludes ArgumentName<N> and ArgumentType<N> columns.
        arguments = arguments.drop(columns=['ArgumentName' + str(i), 'ArgumentType' + str(i), 'ReturnValueName' + str(i),
                                            'ReturnValueType' + str(i)])

    # Transform all rows into a single str to avoid ambiguity.

    aux_arguments = arguments.apply(lambda row: ','.join(row.astype(str)), axis=1)
    arguments_list = aux_arguments.unique()
    for argument in arguments_list: #For each unique set of arguments check for its duplicates.
        filtered_arguments = aux_arguments[aux_arguments == argument]
        filtered_arguments = filtered_arguments[filtered_arguments.duplicated(keep=False)]
        argument_indexs = filtered_arguments.index.to_list()

        # Merges both arguments by joining the names of the methods that use the same argument.

        for j in range(1, len(argument_indexs)):
            merged_arguments.loc[argument_indexs[0], 'BelongsTo'] += ',' + merged_arguments.loc[argument_indexs[j],
            'BelongsTo']
            merged_arguments = merged_arguments.drop(index=argument_indexs[j])
    merged_arguments = merged_arguments.reset_index(drop=True)
    return merged_arguments

def merge_return_values(data):
    """
    Joins samples of return values that have the same name, data type, widget and where the method it belongs to is
    within the same Controller.

    Param:

    - data (pandas.core.frame.DataFrame): Controller data from the test dataset.

    Return:

    - merged_return_values (pandas.core.frame.DataFrame): Controller data from the test dataset with merged return values.
    """
    merged_return_values = data

    # Do not join method return values where the first ones are displayed in another window.

    return_values = data[data['Window'] == False]

    # Excludes From, To, IsAnArgument, IsAMethod, IsAReturnValue, BelongsTo, DefaultValue, PossibleValues and UsedByView
    # columns (not essential to the argument joining process).

    return_values = return_values[return_values['IsAReturnValue'] == True].drop(columns=['From', 'To', 'IsAnArgument',
                            'IsAMethod', 'IsAReturnValue', 'BelongsTo', 'DefaultValue', 'PossibleValues', 'UsedByView'])
    for i in range(1, 11):  # Also excludes ReturnValueName<N> and ReturnValueType<N> columns.
        return_values = return_values.drop(columns=['ArgumentName' + str(i), 'ArgumentType' + str(i), 'ReturnValueName'
                                                    + str(i), 'ReturnValueType' + str(i)])

    # Transform all rows into a single str to avoid ambiguity.

    aux_return_values = return_values.apply(lambda row: ','.join(row.astype(str)), axis=1)
    return_values_list = aux_return_values.unique()
    for return_value in return_values_list:
        filtered_return_values = aux_return_values[aux_return_values == return_value]
        filtered_return_values = filtered_return_values[filtered_return_values.duplicated(keep=False)]
        return_value_indexs = filtered_return_values.index.to_list()

        # Merges both return values by joining the names of the methods that use the same return value.

        for j in range(1, len(return_value_indexs)):
            merged_return_values.loc[return_value_indexs[0], 'BelongsTo'] += ',' + merged_return_values.loc[return_value_indexs[j],
            'BelongsTo']
            merged_return_values = merged_return_values.drop(index=return_value_indexs[j])
    merged_return_values = merged_return_values.reset_index(drop=True)
    return merged_return_values

def set_languages(data):
    """
    Detects which language the method nomenclature corresponds to.
    The language is a code based on ISO 639-1.

    Param:

    - data (pandas.core.frame.DataFrame): Controller data from the test dataset.

    Return:

    - language_data (pandas.core.frame.DataFrame): Controller data from the test dataset with the assigned language.
    """
    language_data = data
    languages = []
    for name in data[data['IsAMethod'] == True]['Name']:    # For each method name
        refined_name = ''
        if '_' in name: # The underscore symbols are replaced by blank spaces.
            refined_name = name.replace('_', ' ')
        languages.append(langid.classify(refined_name)[0])
    language = Counter(languages).most_common(1)[0][0]  # Count which of the occurrences has been the majority.
    if language not in ['ca', 'es']:    # If it has been written in another language, it will default to English (en).
        language = 'en'
    language_data['LanguageID'] = language
    return language_data

def set_methods_as_menu_buttons(data, main_controller_name, view_threshold=3, window_threshold=5):
    """
    Sets whether methods found in the main window are defined as Menubutton whenever the number of arguments and/or
    return values exceeds the set threshold. It also defines access to the window of each Controller for each View
    through the menu.

    Param:

    - data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - main_controller_name (str): The name of the main Controller.
    - view_threshold (int): The minimum number of Controllers to split the View into multiple Views. Default value is 3.
    - window_threshold (int): The minimum number of arguments/return values to display methods in a separate window. Default value is 5.

    Return:

    - new_data (pandas.core.frame.DataFrame): Controller data from the test dataset with the new configuration.
    """
    new_data = data
    new_data['Window'] = False  # Create a new column called Window.
    method_data = data[data['IsAMethod'] == True]

    # In case there is more than one View per Controller, we only take the data from the main Controller.

    if len(method_data['ClassName'].unique().tolist()) > view_threshold:
        method_data = method_data[method_data['ClassName'] == main_controller_name]
    for row in method_data.itertuples():    # For each method
        arguments = []
        return_values = []
        _type = row.Type
        i = 0
        stop = False

        # Checks if the number of arguments/return values is greater than the threshold value (window_threshold)

        while i < 10 and not stop:
            if method_data.loc[row.Index, 'ArgumentName' + str(i + 1)] == '':
                stop = True
            else:
                arguments.append(method_data.loc[row.Index, 'ArgumentName' + str(i + 1)])
                i += 1
        j = 0
        stop = False
        while j < 10 and not stop:
            if method_data.loc[row.Index, 'ReturnValueName' + str(j + 1)] == '':
                stop = True
            else:
                return_values.append(method_data.loc[row.Index, 'ReturnValueName' + str(j + 1)])
                j += 1

        # If it does not require any arguments/return values, it is automatically a Menubutton.
        # Otherwise, it assigns when it exceeds the threshold restrictions.

        if _type == 'None' and i == 0 and j == 0:
            new_data.at[row.Index, 'Widget'] = 'Menubutton'
        elif i > window_threshold or j > window_threshold:
            found_in_arguments = False
            k = 0
            while k < len(arguments) and not found_in_arguments:
                if len(data[data['Name'] == arguments[k]]['BelongsTo'].iloc[0].split(',')) > 1:
                    found_in_arguments = True
                else:
                    k += 1
            found_in_return_values = False
            k = 0
            while k < len(return_values) and not found_in_return_values:
                if len(data[data['Name'] == return_values[k]]['BelongsTo'].iloc[0].split(',')) > 1:
                    found_in_return_values = True
                else:
                    k += 1
            if not found_in_arguments and not found_in_return_values:
                new_data.loc[row.Index, 'Widget'] = 'Menubutton'
                new_data.loc[new_data['BelongsTo'] == row.Name, 'Window'] = True
    return new_data

def set_widget_label(data, init_data, model_data):
    """
    Creates a new column labeled WidgetLabel that corresponds to the nomenclature used by the developer in the
    implementation, but without special characters.

    Param:

    - data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - init_data (pandas.core.frame.DataFrame): Model and Controller constructors data from the test dataset (methods only).
    - model_data (pandas.core.frame.DataFrame): Model data from the test dataset.

    Return:

    - new_data (pandas.core.frame.DataFrame): Controller data from the test dataset with the new configuration.
    """
    new_data = data
    new_data['WidgetLabel'] = new_data['Name']  # Create a new column called WidgetLabel.

    # If the WidgetLabel column contains 'self.', it is left with the name of the Model attribute that the method within
    # the Controller returns.

    for row in new_data[new_data['WidgetLabel'].str.contains("self.")].itertuples():
        index = init_data[init_data['ClassName'] == row.ClassName].index.to_list()[0]
        i = 0
        found = False
        while init_data.loc[index, 'ArgumentName' + str(i + 1)] != '' and i < 10 and not found:
            if init_data.loc[index, 'ArgumentName' + str(i + 1)] == row.Name.split('.')[1]:
                found = True
            else:
                i += 1
        if found:
            index = model_data[model_data['Name'] == row.Name.split('.')[2]].index.to_list()[0]
            new_data.loc[row.Index, 'WidgetLabel'] = model_data.loc[index, 'ReturnValueName1'].replace('self.', '')

    # If the WidgetLabel column contains 'unnamed'.

    for row in new_data[new_data['WidgetLabel'].str.contains("unnamed")].itertuples():

        # Depending on the data type, a personalized label will be assigned.

        if row.Type in ['int', 'float', 'complex']:
            match data['LanguageID'].mode()[0]:
                case 'en':
                    new_data.loc[row.Index, 'WidgetLabel'] = "Result of "
                case 'es':
                    new_data.loc[row.Index, 'WidgetLabel'] = "Resultado de "
                case 'ca':
                    new_data.loc[row.Index, 'WidgetLabel'] = "Resultat de "
        elif row.Type == "bool":
            match data['LanguageID'].mode()[0]:
                case 'en':
                    new_data.loc[row.Index, 'WidgetLabel'] = "State of "
                case 'es':
                    new_data.loc[row.Index, 'WidgetLabel'] = "Estado de "
                case 'ca':
                    new_data.loc[row.Index, 'WidgetLabel'] = "Estat de "
        elif row.Type == "str":
            match data['LanguageID'].mode()[0]:
                case 'en':
                    new_data.loc[row.Index, 'WidgetLabel'] = "Message of "
                case 'es':
                    new_data.loc[row.Index, 'WidgetLabel'] = "Mensaje de "
                case 'ca':
                    new_data.loc[row.Index, 'WidgetLabel'] = "Missatge de "
        elif row.Type in ['list', 'tuple', 'set']:
            match data['LanguageID'].mode()[0]:
                case 'en':
                    new_data.loc[row.Index, 'WidgetLabel'] = "List of "
                case 'es':
                    new_data.loc[row.Index, 'WidgetLabel'] = "Lista de "
                case 'ca':
                    new_data.loc[row.Index, 'WidgetLabel'] = "Llista de "
        elif row.Type == "dict":
            match data['LanguageID'].mode()[0]:
                case 'en':
                    new_data.loc[row.Index, 'WidgetLabel'] = "Dictionary of "
                case 'es':
                    new_data.loc[row.Index, 'WidgetLabel'] = "Diccionario de "
                case 'ca':
                    new_data.loc[row.Index, 'WidgetLabel'] = "Diccionari de "
        new_data.loc[row.Index, 'WidgetLabel'] += new_data.loc[row.Index, 'BelongsTo']

    # The underscore symbols are replaced by blank spaces.
    # Then the first letter is converted to uppercase.

    new_data['WidgetLabel'] = new_data['WidgetLabel'].str.replace('_', ' ')
    new_data['WidgetLabel'] = new_data['WidgetLabel'].str[0].str.upper() + new_data['WidgetLabel'].str[1:]
    return new_data

def set_widget_description(data, init_data, model_data):
    """
    Creates a new column labeled WidgetDescription that corresponds to the nomenclature used by the developer in the
    implementation, but without special characters.

    Param:

    - data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - init_data (pandas.core.frame.DataFrame): Model and Controller constructors data from the test dataset (methods only).
    - model_data (pandas.core.frame.DataFrame): Model data from the test dataset.

    Return:

    - new_data (pandas.core.frame.DataFrame): Controller data from the test dataset with the new configuration.
    """
    new_data = data
    new_data['WidgetDescription'] = new_data['Name']

    # If the WidgetDescription column contains 'self.', it is left with the name of the Model attribute that the method within
    # the Controller returns.

    for row in new_data[new_data['WidgetDescription'].str.contains("self.")].itertuples():
        index = init_data[init_data['ClassName'] == row.ClassName].index.to_list()[0]
        i = 0
        found = False
        while init_data.loc[index, 'ArgumentName' + str(i + 1)] != '' and i < 10 and not found:
            if init_data.loc[index, 'ArgumentName' + str(i + 1)] == row.Name.split('.')[1]:
                found = True
            else:
                i += 1
        if found:
            index = model_data[model_data['Name'] == row.Name.split('.')[2]].index.to_list()[0]
            new_data.loc[row.Index, 'WidgetDescription'] = model_data.loc[index, 'ReturnValueName1'].replace('self.', '')

    # If the WidgetDescription column contains 'unnamed'.

    for row in new_data[new_data['WidgetDescription'].str.contains("unnamed")].itertuples():

        # Depending on the data type, a personalized description will be assigned.

        if row.Type in ['int', 'float', 'complex']:
            match data['LanguageID'].mode()[0]:
                case 'en':
                    new_data.loc[row.Index, 'WidgetDescription'] = "Result of "
                case 'es':
                    new_data.loc[row.Index, 'WidgetDescription'] = "Resultado de "
                case 'ca':
                    new_data.loc[row.Index, 'WidgetDescription'] = "Resultat de "
        elif row.Type == "bool":
            match data['LanguageID'].mode()[0]:
                case 'en':
                    new_data.loc[row.Index, 'WidgetDescription'] = "State of "
                case 'es':
                    new_data.loc[row.Index, 'WidgetDescription'] = "Estado de "
                case 'ca':
                    new_data.loc[row.Index, 'WidgetDescription'] = "Estat de "
        elif row.Type == "str":
            match data['LanguageID'].mode()[0]:
                case 'en':
                    new_data.loc[row.Index, 'WidgetDescription'] = "Message of "
                case 'es':
                    new_data.loc[row.Index, 'WidgetDescription'] = "Mensaje de "
                case 'ca':
                    new_data.loc[row.Index, 'WidgetDescription'] = "Missatge de "
        elif row.Type in ['list', 'tuple', 'set']:
            match data['LanguageID'].mode()[0]:
                case 'en':
                    new_data.loc[row.Index, 'WidgetDescription'] = "List of "
                case 'es':
                    new_data.loc[row.Index, 'WidgetDescription'] = "Lista de "
                case 'ca':
                    new_data.loc[row.Index, 'WidgetDescription'] = "Llista de "
        elif row.Type == "dict":
            match data['LanguageID'].mode()[0]:
                case 'en':
                    new_data.loc[row.Index, 'WidgetDescription'] = "Dictionary of "
                case 'es':
                    new_data.loc[row.Index, 'WidgetDescription'] = "Diccionario de "
                case 'ca':
                    new_data.loc[row.Index, 'WidgetDescription'] = "Diccionari de "
        new_data.loc[row.Index, 'WidgetDescription'] += new_data.loc[row.Index, 'BelongsTo']

    # The underscore symbols are replaced by blank spaces.
    # Then the first letter is converted to uppercase (adds ':' at the end of description).

    new_data['WidgetDescription'] = new_data['WidgetDescription'].str.replace('_', ' ')
    new_data['WidgetDescription'] = new_data['WidgetDescription'].str[0].str.upper() + new_data['WidgetDescription'].str[1:] + ':'
    return new_data

def set_window_methods(data, main_controller_name, window_threshold=5):
    """
    Sets whether methods found in a window corresponding to any View different than the main one can be accessed through
    a new window.

    Param:

    - data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - main_controller_name (str): The name of the main Controller.
    - window_threshold (int): The minimum number of arguments/return values to display methods in a separate window. Default value is 5.

    Return:

    - new_data (pandas.core.frame.DataFrame): Controller data from the test dataset with the new configuration.
    """
    new_data = data
    method_data = data[data['IsAMethod'] == True]
    method_data = method_data[method_data['ClassName'] != main_controller_name]
    method_data = method_data[method_data['Widget'] != 'Menubutton']
    for row in method_data.itertuples():
        arguments = []
        return_values = []
        _type = row.Type
        i = 0
        stop = False

        # Checks if the number of arguments/return values is greater than the threshold value (window_threshold)

        while i < 10 and not stop:
            if method_data.loc[row.Index, 'ArgumentName' + str(i + 1)] == '':
                stop = True
            else:
                arguments.append(method_data.loc[row.Index, 'ArgumentName' + str(i + 1)])
                i += 1
        j = 0
        stop = False
        while j < 10 and not stop:
            if method_data.loc[row.Index, 'ReturnValueName' + str(j + 1)] == '':
                stop = True
            else:
                return_values.append(method_data.loc[row.Index, 'ReturnValueName' + str(j + 1)])
                j += 1

        # It assigns as a Window when it exceeds the threshold restrictions.

        if i > window_threshold or j > window_threshold:
            found_in_arguments = False
            k = 0
            while k < len(arguments) and not found_in_arguments:
                if len(data[data['Name'] == arguments[k]]['BelongsTo'].iloc[0].split(',')) > 1:
                    found_in_arguments = True
                else:
                    k += 1
            found_in_return_values = False
            k = 0
            while k < len(return_values) and not found_in_return_values:
                if len(data[data['Name'] == return_values[k]]['BelongsTo'].iloc[0].split(',')) > 1:
                    found_in_return_values = True
                else:
                    k += 1
            if not found_in_arguments and not found_in_return_values:
                new_data.loc[row.Index, 'Window'] = True
                new_data.loc[new_data['BelongsTo'] == row.Name, 'Window'] = True
    return new_data

def set_hide_show_model_attr(data, init_data, model_data, show_model_attr, hide_model_attr):
    """
    Returns those sample return values from Models that will be displayed in the graphical user interface.

    Param:

    - data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - init_data (pandas.core.frame.DataFrame): Model and Controller constructors data from the test dataset (methods only).
    - model_data (pandas.core.frame.DataFrame): Model data from the test dataset.
    - show_model_attr (bool): Indicates whether the attributes of Models are displayed in the view.
    - hide_model_attr (bool): Indicates whether to hide Controller methods which return Model attributes.

    Return:

    - new_data (pandas.core.frame.DataFrame): Controller data from the test dataset with the new configuration.
    - new_model_data (pandas.core.frame.DataFrame): Model data from the test dataset with the new configuration.
    """
    new_data = data
    aux_model_data = pd.DataFrame()

    # For each Model that is passed as an argument to any Controller constructor, we duplicate the data corresponding
    # to the methods/arguments/return values of the Model so that it can be determined if a Controller calls a Model
    # with the same name that is passed as an argument to its constructor.

    for index, row in init_data[init_data['UsedByView'] == True].iterrows():
        i = 0
        aux_data = pd.DataFrame()
        while row['ArgumentName' + str(i + 1)] != '' and i < 10:
            temp_data = model_data[model_data['ClassName'] == row['ArgumentType' + str(i + 1)]].copy()

            # New column ModelName containing the name of the Model argument used by the Controller constructor.

            temp_data['ModelName'] = row['ArgumentName' + str(i + 1)]
            aux_data = pd.concat([aux_data, temp_data])
            i += 1

        # New column UsedByController that contains the name of the controller used by the Model along with ModelName.

        aux_data['UsedByController'] = row['ClassName']
        aux_model_data = pd.concat([aux_model_data, aux_data])
    aux_model_data = aux_model_data.reset_index(drop=True)
    new_model_data = aux_model_data
    if not show_model_attr: # If the Models attribute are set to not be displayed (False).
        for row in aux_model_data[aux_model_data['IsAReturnValue'] == True].itertuples():   # Hide everything
            new_model_data = new_model_data[new_model_data['Name'] != row.BelongsTo]
        if hide_model_attr: # If Controller methods which return Model attributes are set to hide (True).

            # Finds out which methods return only one attribute of the Models and delete them from the Controller data.

            for index, row in init_data[init_data['UsedByView'] == True].iterrows():
                i = 0
                while row['ArgumentName' + str(i + 1)] != '' and i < 10:
                    aux_data = aux_model_data[aux_model_data['ClassName'] == row['ArgumentType' + str(i + 1)]]
                    aux_data = aux_data[aux_data['UsedByController'] == row['ClassName']]
                    aux_data = aux_data[aux_data['ModelName'] == row['ArgumentName' + str(i + 1)]]
                    for row_aux in aux_data[aux_data['IsAReturnValue'] == True].itertuples():
                        aux_data_2 = data[data['Name'] == "self." + row['ArgumentName' + str(i + 1)] + "." + row_aux.BelongsTo]
                        aux_data_2 = aux_data_2[aux_data_2['ClassName'] == row['ClassName']]
                        if aux_data_2.index.tolist():
                            new_data = new_data[new_data['Name'] != aux_data_2.loc[aux_data_2.index.tolist()[0]]['BelongsTo']]
                    i += 1
    else:   # If the Models attribute are set to be displayed (True).
        for index, row in init_data[init_data['UsedByView'] == True].iterrows():
            i = 0
            while row['ArgumentName' + str(i + 1)] != '' and i < 10:
                aux_data = aux_model_data[aux_model_data['ClassName'] == row['ArgumentType' + str(i + 1)]]
                aux_data = aux_data[aux_data['IsAReturnValue'] == True]
                aux_data = aux_data[aux_data['UsedByController'] == row['ClassName']]
                aux_data = aux_data[aux_data['ModelName'] == row['ArgumentName' + str(i + 1)]]
                for row_aux in aux_data[aux_data['ClassName'] == row['ArgumentType' + str(i + 1)]].itertuples():
                    aux_data_2 = data[data['Name'] == "self." + row['ArgumentName' + str(i + 1)] + "." + row_aux.BelongsTo]
                    aux_data_2 = aux_data_2[aux_data_2['ClassName'] == row['ClassName']]
                    if aux_data_2.index.tolist():

                        # If Controller methods which return Model attributes are set to hide (True), finds out which
                        # methods return only one attribute of the Models and delete them from the Controller data.

                        if hide_model_attr:
                            new_data = new_data[new_data['Name'] != aux_data_2.loc[aux_data_2.index.tolist()[0]]['BelongsTo']]

                        # Deletes samples from return values of Models data if there is a Controller method which returns
                        # the value of an attribute of a Model, exclusively by the Controller itself (UsedByController) and
                        # with the nomenclature assigned as an argument to its constructor (ModelName).

                        new_model_data = new_model_data[~((new_model_data['Name'] == row_aux.BelongsTo) & (new_model_data['UsedByController'] == row['ClassName']) & (new_model_data['ModelName'] == row['ArgumentName' + str(i + 1)]))]
                i += 1
    return new_data, new_model_data

def set_attr_description(data):
    """
    Creates a new column labeled AttrDescription that corresponds to the nomenclature of the attributes of the Models
    displayed in the graphical user interface, but without special characters.

    Param:

    - data (pandas.core.frame.DataFrame): Model data from the test dataset.

    Return:

    - new_data (pandas.core.frame.DataFrame): Model data from the test dataset with the new configuration.
    """
    new_data = data

    # The underscore symbols are replaced by blank spaces.
    # Then the first letter is converted to uppercase (adds ':' at the end of description).

    new_data['AttrDescription'] = new_data['Name'].str.replace("self.", "")
    new_data['AttrDescription'] = new_data['AttrDescription'].str.replace('_', ' ')
    new_data['AttrDescription'] = new_data['AttrDescription'].str[0].str.upper() + new_data['AttrDescription'].str[1:] + ':'
    return new_data