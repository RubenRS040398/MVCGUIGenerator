import langid
from collections import Counter

def refine(data, main_controller_name, view_threshold=3, window_threshold=5):
    refined_data = merge_arguments(data)
    refined_data = merge_return_values(refined_data)
    refined_data = set_languages(refined_data)
    refined_data = set_methods_as_menu_buttons(refined_data, main_controller_name, view_threshold, window_threshold)
    refined_data = set_window_methods(refined_data, main_controller_name, window_threshold)
    refined_data = set_widget_label(refined_data)
    refined_data = set_widget_description(refined_data)
    return refined_data

def merge_arguments(data):
    merged_arguments = data
    arguments = data[data['IsAnArgument'] == True].drop(columns=['IsAnArgument', 'IsAMethod', 'IsAReturnValue', 'BelongsTo', 'UsedByView'])
    for i in range(1, 11):
        arguments = arguments.drop(columns=['ArgumentName' + str(i), 'ArgumentType' + str(i), 'ReturnValueName' + str(i), 'ReturnValueType' + str(i)])
    arguments_list = arguments['Name'].unique()
    for argument in arguments_list:
        filtered_arguments = arguments[arguments['Name'] == argument]
        filtered_arguments = filtered_arguments[filtered_arguments.duplicated(keep=False)]
        argument_indexs = filtered_arguments.index.to_list()
        for j in range(1, len(argument_indexs)):
            merged_arguments.loc[argument_indexs[0], 'BelongsTo'] += ',' + merged_arguments.loc[argument_indexs[j], 'BelongsTo']
            merged_arguments = merged_arguments.drop(index=argument_indexs[j])
    merged_arguments = merged_arguments.reset_index(drop=True)
    return merged_arguments

def merge_return_values(data):
    merged_arguments = data
    return_values = data[data['IsAReturnValue'] == True].drop(columns=['From', 'To', 'IsAnArgument', 'IsAMethod', 'IsAReturnValue', 'BelongsTo', 'DefaultValue', 'PossibleValues', 'UsedByView'])
    for i in range(1, 11):
        return_values = return_values.drop(columns=['ArgumentName' + str(i), 'ArgumentType' + str(i), 'ReturnValueName' + str(i), 'ReturnValueType' + str(i)])
    return_values_list = return_values['Name'].unique()
    for return_value in return_values_list:
        filtered_return_values = return_values[return_values['Name'] == return_value]
        filtered_return_values = filtered_return_values[filtered_return_values.duplicated(keep=False)]
        return_value_indexs = filtered_return_values.index.to_list()
        for j in range(1, len(return_value_indexs)):
            merged_arguments.loc[return_value_indexs[0], 'BelongsTo'] += ',' + merged_arguments.loc[return_value_indexs[j], 'BelongsTo']
            merged_arguments = merged_arguments.drop(index=return_value_indexs[j])
    merged_arguments = merged_arguments.reset_index(drop=True)
    return merged_arguments

def set_languages(data):
    language_data = data
    languages = []
    for name in data['Name']:
        refined_name = ''
        if '_' in name:
            refined_name = name.replace('_', ' ')
        languages.append(langid.classify(refined_name)[0])
    language = Counter(languages).most_common(1)[0][0]
    if language not in ['ca', 'es']:
        language = 'en'
    language_data['LanguageID'] = language
    return language_data

def set_methods_as_menu_buttons(data, main_controller_name, view_threshold, window_threshold):
    new_data = data
    new_data['Window'] = False
    method_data = data[data['IsAMethod'] == True]
    #method_data = method_data[method_data['UsedByView'] == False]
    if len(method_data['ClassName'].unique().tolist()) > view_threshold:
        method_data = method_data[method_data['ClassName'] == main_controller_name]
    for row in method_data.itertuples():
        arguments = []
        return_values = []
        _type = row.Type
        i = 0
        stop = False
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
        possible_values = len(row.PossibleValues.split(','))
        if _type == 'None' and i == 0 and j == 0:
            new_data.at[row.Index, 'Widget'] = 'Menubutton'
        #elif _type != 'None' and i == 1 and j == 1:
            #if method_data.loc[row.Index, 'ArgumentType1'] == 'bool' and method_data.loc[row.Index, 'ReturnValueType1'] == 'bool':
                #new_data.at[row.Index, 'Widget'] = 'Menubutton'
            #elif method_data.loc[row.Index, 'ArgumentType1'] == 'str' and method_data.loc[row.Index, 'ReturnValueType1'] == 'str' and possible_values == 3:
                #new_data.at[row.Index, 'Widget'] = 'Menubutton'
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
                #new_data.loc[row.Index, 'Window'] = True
    return new_data

def set_widget_label(data):
    #TBD
    new_data = data
    new_data['WidgetLabel'] = new_data.groupby('Widget').cumcount()
    new_data['WidgetLabel'] = new_data['Widget'] + '_' + new_data['WidgetLabel'].astype(str)
    return new_data

def set_widget_description(data):
    #TBD
    new_data = data
    new_data['WidgetDescription'] = 'Description_' + new_data.index.astype(str) + ':'
    return new_data

def set_window_methods(data, main_controller_name, window_threshold):
    new_data = data
    #new_data['Window'] = False
    method_data = data[data['IsAMethod'] == True]
    #method_data = method_data[method_data['UsedByView'] == False]
    method_data = method_data[method_data['ClassName'] != main_controller_name]
    method_data = method_data[method_data['Widget'] != 'Menubutton']
    for row in method_data.itertuples():
        arguments = []
        return_values = []
        _type = row.Type
        i = 0
        stop = False
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
        possible_values = len(row.PossibleValues.split(','))
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
    return new_data