import ast
import sys
import pandas as pd

data = []
float_min = -1.797693e+292
float_max = 1.797693e+292

def scan(source_code):
    """
    Scans the source code and returns the test dataset.

    Param:

    - source_code (str): The whole source code.

    Return:

    - test_data (pandas.core.frame.DataFrame): The whole test dataset.
    """
    tree = ast.parse(source_code) # Obtaining the root node to traverse the syntax tree.
    walk(tree, '', False, False)
    labels = ['Name', 'Type', 'From', 'To', 'IsAnArgument', 'IsAMethod', 'IsAReturnValue']
    for i in range(1, 11):
        labels.append('ArgumentName' + str(i))
        labels.append('ArgumentType' + str(i))
    for i in range(1, 11):
        labels.append('ReturnValueName' + str(i))
        labels.append('ReturnValueType' + str(i))
    labels.append('DefaultValue')
    labels.append('PossibleValues')
    labels.append('BelongsTo')
    labels.append('ClassName')
    labels.append('UsedByView')
    test_data = pd.DataFrame(data, columns=labels)
    return test_data

def walk(node, name, is_a_class, is_not_a_model):
    """
    Traverses the syntax tree recursively.

    Param:

    - node (ast.Module): A node of the syntax tree.
    - name (str): The name of the class in which the current node is located.
    - is_a_class (bool): Indicates whether the current node is inside a class or not.
    - is_not_a_model (bool): Indicates if the class in which the current node is located is not a Model.
    """
    if "FunctionDef" in str(node) and is_a_class:   # If it is a method and it is inside a class, we get its sample
        data.append(get_method_sample(node, name, is_not_a_model))  # Adds the sample to the main dataset
    else:   # Otherwise, traverse the tree until it finds a function within a class
        children = list(ast.iter_child_nodes(node))
        for child in children:

            # If one of the children is a class, saves its name, indicates that it is and checks that it is not a Model.

            if "ClassDef" in str(child):
                walk(child, child.__dict__['name'], True, check(child))
            else:
                walk(child, name, is_a_class, is_not_a_model)

def check(node):
    """
    Checks if the current node that is a class is not a Model.

    Param:

    - node (ast.Module): A node of the syntax tree.

    Return:

    - found (bool): Indicate if it is not a Model (otherwise False).
    """
    i = 0
    function = None
    found = False

    # First, the function definition is obtained within the grammar by traversing the body of the class.

    while i < len(node.__dict__['body']) and not found:
        if node.__dict__['body'][i].__dict__['name'] == '__init__':
            function = node.__dict__['body'][i]
            found = True
        else:
            i += 1
    found = True

    # Once it is obtained, checks that the data types of the arguments correspond to those indicated below.

    while i < len(function.__dict__['args'].__dict__['args']) and found:
        if function.__dict__['args'].__dict__['args'][i].__dict__['arg'] != 'self':
            match function.__dict__['args'].__dict__['args'][i].__dict__['annotation'].__dict__['id']:
                case 'int' | 'float' | 'bool' | 'str' | 'complex' | 'list' | 'tuple' | 'set' | 'dict':
                    found = False
                case _:
                    i += 1
        else:
            i += 1
    return found

def get_method_sample(node, class_name, is_not_a_model):
    """
    Adds the sample of the method which current node corresponds.

    Param:

    - node (ast.Module): A node of the syntax tree.
    - class_name (str): The name of the class in which the current node is located.
    - is_not_a_model (bool): Indicates if the class in which the current node is located is not a Model.

    Return:

    - function_sample (list): List of sample characteristics of the corresponding method.
    """
    function_sample = [node.__dict__['name']]   # Name

    # If it is a method that returns more than one value, the data type referring to the tuple of return values
    # is obtained.

    if node.__dict__['returns']:
        if 'slice' in node.__dict__['returns'].__dict__:
            function_sample.append(node.__dict__['returns'].__dict__['value'].__dict__['id'])
        else:
            function_sample.append(node.__dict__['returns'].__dict__['id'])
    else:   # If no value is returned, it defaults to None.
        function_sample.append(str(node.__dict__['returns']))

    function_sample.append(float_min)   # From.
    function_sample.append(float_max)   # To.
    function_sample.append(False)       # IsAnArgument.
    function_sample.append(True)        # IsAMethod.
    function_sample.append(False)       # IsAReturnValue.

    # Save the argument names to a list

    arguments = []
    for argument in node.__dict__['args'].__dict__['args']:
        if argument.__dict__['arg'] != 'self':  # Except self argument.
            arguments.append(argument)
    while len(arguments) < 10:  # The remaining features that are not associated with any argument are None.
        arguments.append(None)

    # The list of default values is obtained (if applicable to its argument).

    defaults = []
    default_index = 0
    for default in node.__dict__['args'].__dict__['defaults']:
        defaults.append(default.__dict__['value'])

    # The list of assertions found is obtained through the following method.

    asserts = look_for_asserts(node)
    for argument in arguments:  # For each argument the name and associated type are saved.
        if not argument:    # If there is no information, leave it blank.
            function_sample.append('')
            function_sample.append('None')
        else:   # Otherwise checks whether this is an argument with a default value or not.
            function_sample.append(argument.__dict__['arg'])
            if argument.__dict__['annotation']:
                function_sample.append(argument.__dict__['annotation'].__dict__['id'])
                if node.__dict__['name'] != '__init__':
                    data.append(get_argument_sample(argument, class_name,None, asserts,
                                                    node.__dict__['name'], is_not_a_model))
            else:
                function_sample.append(type(defaults[default_index]).__name__)
                if node.__dict__['name'] != '__init__':
                    data.append(get_argument_sample(argument, class_name, defaults[default_index], asserts,
                                                    node.__dict__['name'], is_not_a_model))
                default_index += 1

    # If the method has return values, saves the name and data type for each one.

    if node.__dict__['returns']:
        if 'slice' in node.__dict__['returns'].__dict__:

            # If it returns more than single value, iterates over each one.

            j = 0
            for return_value in node.__dict__['body'][-1].__dict__['value'].__dict__['elts']:
                if "Name" in str(return_value): # Variable name?
                    function_sample.append(str(return_value.__dict__['id']))
                    function_sample.append(node.__dict__['returns'].__dict__['slice'].__dict__['elts'][j].__dict__['id'])
                    data.append(get_return_value_sample(str(return_value.__dict__['id']),
                                                        class_name,
                                                  node.__dict__['returns'].__dict__['slice'].__dict__['elts'][j].__dict__['id'],
                                                        node.__dict__['name'], is_not_a_model))
                elif "Call" in str(return_value):   # Calls to a Model method?
                    aux_name = return_value.__dict__['func'].__dict__['value'].__dict__['value'].__dict__['id']
                    aux_name += '.' + return_value.__dict__['func'].__dict__['value'].__dict__['attr']
                    aux_name += '.' + return_value.__dict__['func'].__dict__['attr']
                    function_sample.append(aux_name)
                    function_sample.append(node.__dict__['returns'].__dict__['slice'].__dict__['elts'][j].__dict__['id'])
                    data.append(get_return_value_sample(aux_name, class_name,
                    node.__dict__['returns'].__dict__['slice'].__dict__['elts'][j].__dict__['id'], node.__dict__['name'],
                                                        is_not_a_model))
                elif "Constant" in str(return_value):   # Constant value?
                    function_sample.append("unnamed_" + str(return_value.__dict__['value']))
                    function_sample.append(type(return_value.__dict__['value']).__name__)
                    data.append(get_return_value_sample("unnamed_" + str(return_value.__dict__['value']), class_name,
                                                  type(return_value.__dict__['value']).__name__, node.__dict__['name'],
                                                        is_not_a_model))
                j += 1
            for i in range(j, 10):  # The remaining features that are not associated with any return value are None
                function_sample.append('')
                function_sample.append('None')
        else:
            aux_return = node.__dict__['body'][-1]
            if "Name" in str(aux_return.__dict__['value']): # Variable name?
                function_sample.append(str(aux_return.__dict__['value'].__dict__['id']))
                data.append(get_return_value_sample(str(aux_return.__dict__['value'].__dict__['id']), class_name,
                                              node.__dict__['returns'].__dict__['id'], node.__dict__['name'],
                                                    is_not_a_model))
            elif "Call" in str(aux_return.__dict__['value']):   # Calls to a Model method?
                aux_name = aux_return.__dict__['value'].__dict__['func'].__dict__['value'].__dict__['value'].__dict__['id']
                aux_name += '.' + aux_return.__dict__['value'].__dict__['func'].__dict__['value'].__dict__['attr']
                aux_name += '.' + aux_return.__dict__['value'].__dict__['func'].__dict__['attr']
                function_sample.append(aux_name)
                data.append(get_return_value_sample(aux_name, class_name, node.__dict__['returns'].__dict__['id'],
                                                    node.__dict__['name'], is_not_a_model))
            elif "Constant" in str(aux_return.__dict__['value']):   # Constant value?
                function_sample.append("unnamed_" + str(aux_return.__dict__['value'].__dict__['value']))
                data.append(get_return_value_sample("unnamed_" + str(aux_return.__dict__['value'].__dict__['value']),
                                                    class_name, node.__dict__['returns'].__dict__['id'], node.__dict__['name'],
                                                    is_not_a_model))
            elif "Attribute" in str(aux_return.__dict__['value']):  # Attribute?
                aux_name = aux_return.__dict__['value'].__dict__['value'].__dict__['id']
                aux_name += '.' + aux_return.__dict__['value'].__dict__['attr']
                function_sample.append(aux_name)
                data.append(get_return_value_sample(aux_name, class_name, node.__dict__['returns'].__dict__['id'],
                                                    node.__dict__['name'], is_not_a_model))
            function_sample.append(node.__dict__['returns'].__dict__['id'])
            for i in range(1, 10):  # The remaining features that are not associated with any return value are None
                function_sample.append('')
                function_sample.append('None')
    else:
        for i in range(10):
            function_sample.append('')
            function_sample.append('None')

    function_sample.append('')  # DefaultValue.
    function_sample.append('')  # PossibleValues.
    function_sample.append('')  # BelongsTo.
    function_sample.append(class_name)  # ClassName.
    function_sample.append(is_not_a_model)  # UsedByView.
    return function_sample

def look_for_asserts(node):
    """
    Returns a specific list of assertions to determine the maximum/minimum values
    of an int or float type argument, or the possible values that an str type argument can take.

    Param:

    - node (ast.Module): A node of the syntax tree.

    Return:

    - asserts (list): The list of assertions found inside a method.
    """
    asserts = []
    for _object in node.__dict__['body']:
        if "Assert" in str(_object):    # Is an assert?
            _assert = []
            if 'op' in _object.__dict__['test'].__dict__:   # If its an 'op' object then...
                for value in _object.__dict__['test'].__dict__['values']:
                    if 'left' in value.__dict__:
                        if "Name" in str(value.__dict__['left']):   # Variable name?
                            _assert.append(value.__dict__['left'].__dict__['id'])
                        elif "Constant" in str(value.__dict__['left']): # Constant value?
                            _assert.append(value.__dict__['left'].__dict__['value'])
                        for ops in value.__dict__['ops']:   # Assign the involved operators
                            _assert.append(str(ops))
                        for comparator in value.__dict__['comparators']:    # For the rest of comparators
                            if "Name" in str(comparator):   # Variable name?
                                _assert.append(comparator.__dict__['id'])
                            elif "Constant" in str(comparator): # Constant value?
                                _assert.append(comparator.__dict__['value'])
            elif 'left' in _object.__dict__['test'].__dict__: # If its an 'left' object then...
                if "Name" in str(_object.__dict__['test'].__dict__['left']):    # Variable name?
                    _assert.append(_object.__dict__['test'].__dict__['left'].__dict__['id'])
                elif "Constant" in str(_object.__dict__['test'].__dict__['left']):  # Constant value?
                    _assert.append(_object.__dict__['test'].__dict__['left'].__dict__['value'])
                elif "UnaryOp" in str(_object.__dict__['test'].__dict__['left']):
                    if "USub" in str(_object.__dict__['test'].__dict__['left'].__dict__['op']): # Is it negative?
                        # Constant value?
                        if "Constant" in str(_object.__dict__['test'].__dict__['left'].__dict__['operand']):
                            _assert.append(-_object.__dict__['test'].__dict__['left'].__dict__['operand'].__dict__['value'])
                for ops in _object.__dict__['test'].__dict__['ops']:
                    _assert.append(str(ops))
                for comparator in _object.__dict__['test'].__dict__['comparators']: # For the rest of comparators
                    if "Name" in str(comparator):   # Variable name?
                        _assert.append(comparator.__dict__['id'])
                    elif "Constant" in str(comparator): # Constant value?
                        _assert.append(comparator.__dict__['value'])
                    elif "List" in str(comparator): # Does it use a list of strings to check for equality?
                        for constant in _object.__dict__['test'].__dict__['comparators'][0].__dict__['elts']:
                            _assert.append(constant.__dict__['value'])
                    elif "UnaryOp" in str(comparator):
                        if "USub" in str(comparator.__dict__['op']):    # Is it negative?
                            if "Constant" in str(comparator.__dict__['operand']):
                                _assert.append(-comparator.__dict__['operand'].__dict__['value'])
            asserts.append(_assert)
    return asserts

def get_argument_sample(node, class_name, default_value, asserts, method_name, is_not_a_model):
    """
    Adds the sample of the argument which current node corresponds.

    Param:

    - node (ast.Module): A node of the syntax tree.
    - class_name (str): The name of the class in which the current node is located.
    - default_value (int/float/bool/complex/str/list/tuple/set/dict): The default value of the argument.
    - asserts (list): The list of assertions found in the method which the argument is passed as a parameter.
    - method_name (str): The name of the method which the argument is passed as a parameter.
    - is_not_a_model (bool): Indicates if the class in which the current node is located is not a Model.

    Return:

    - argument_sample (list): List of sample characteristics of the corresponding argument.
    """
    argument_sample = [node.__dict__['arg']]    # Name

    # If it is an argument that includes a default value, the data type of the default value must be obtained without
    # considering type hints.

    if default_value:
        argument_sample.append(type(default_value).__name__)
    else:
        argument_sample.append(node.__dict__['annotation'].__dict__['id'])

    # Finds the assertion where one of its comparators corresponds to the argument.

    _assert = []
    i = 0
    found = False
    while i < len(asserts) and not found:
        if node.__dict__['arg'] in asserts[i]:
            if (("Gt" in asserts[i][1] or "Lt" in asserts[i][1])
                    and node.__dict__['arg'] in asserts[i]): # Has at least >, >=, <, <= operands in both sides?
                _assert = asserts[i]
                found = True
            elif ("Eq" in asserts[i][1] and node.__dict__['arg'] == asserts[i][0] # Has == operand?
                  and (node.__dict__['arg'] == asserts[i][0] or node.__dict__['arg'] == asserts[i][1]
                       or node.__dict__['arg'] == asserts[i][2])):
                _assert = asserts[i]
                found = True
            elif "In" in asserts[i][1] and node.__dict__['arg'] == asserts[i][0]: # Has in operand?
                _assert = asserts[i]
                found = True
            else:
                i += 1
        else:
            i += 1
    possible_values = ''
    if len(_assert) == 0:   # If there is no assertion or association with any argument, it keeps From and To default values.
        argument_sample.append(float_min)
        argument_sample.append(float_max)
    elif len(_assert) == 3:
        if _assert.index(node.__dict__['arg']) == 0:    # If uses one operand (int, float).
            if "Gt " in _assert[1]:
                argument_sample.append(float(_assert[2]) + min_value(type(_assert[2])))
                argument_sample.append(float_max)
            elif "GtE " in _assert[1]:
                argument_sample.append(float(_assert[2]))
                argument_sample.append(float_max)
            elif "Lt " in _assert[1]:
                argument_sample.append(float_min)
                argument_sample.append(float(_assert[2]) - min_value(type(_assert[2])))
            elif "LtE " in _assert[1]:
                argument_sample.append(float_min)
                argument_sample.append(float(_assert[2]))
        else:
            if "Gt " in _assert[1]:
                argument_sample.append(float_min)
                argument_sample.append(float(_assert[0]) - min_value(type(_assert[0])))
            elif "GtE " in _assert[1]:
                argument_sample.append(float_min)
                argument_sample.append(float(_assert[0]))
            elif "Lt " in _assert[1]:
                argument_sample.append(float(_assert[0]) + min_value(type(_assert[0])))
                argument_sample.append(float_max)
            elif "LtE " in _assert[1]:
                argument_sample.append(float(_assert[0]))
                argument_sample.append(float_max)
    elif len(_assert) >= 4:
        if "Gt" in _assert[1] or "Lt" in _assert[1]:    # If uses two operands (int, float).
            if "Gt " in _assert[1] and "Gt " in _assert[2]:
                argument_sample.append(float(_assert[-1]) + min_value(type(_assert[-1])))
                argument_sample.append(float(_assert[0]) - min_value(type(_assert[0])))
            elif "Gt " in _assert[1] and "GtE " in _assert[2]:
                argument_sample.append(float(_assert[-1]))
                argument_sample.append(float(_assert[0]) - min_value(type(_assert[0])))
            elif "GtE " in _assert[1] and "Gt " in _assert[2]:
                argument_sample.append(float(_assert[-1]) + min_value(type(_assert[-1])))
                argument_sample.append(float(_assert[0]))
            elif "GtE " in _assert[1] and "GtE " in _assert[2]:
                argument_sample.append(float(_assert[-1]))
                argument_sample.append(float(_assert[0]))
            elif "Lt " in _assert[1] and "Lt " in _assert[2]:
                argument_sample.append(float(_assert[0]) + min_value(type(_assert[0])))
                argument_sample.append(float(_assert[-1]) - min_value(type(_assert[-1])))
            elif "Lt " in _assert[1] and "LtE " in _assert[2]:
                argument_sample.append(float(_assert[0]) + min_value(type(_assert[0])))
                argument_sample.append(float(_assert[-1]))
            elif "LtE " in _assert[1] and "Lt " in _assert[2]:
                argument_sample.append(float(_assert[0]))
                argument_sample.append(float(_assert[-1]) - min_value(type(_assert[-1])))
            elif "LtE " in _assert[1] and "LtE " in _assert[2]:
                argument_sample.append(float(_assert[0]))
                argument_sample.append(float(_assert[-1]))
        elif "Eq" in _assert[1]:    # If uses equal operand (str).
            argument_sample.append(float(0))
            argument_sample.append(float(_assert.count(node.__dict__['arg'])))
            for i in range(2, len(_assert), 3):
                possible_values += str(_assert[i])
                if i < len(_assert) - 1:
                    possible_values += ','
        elif "In" in _assert[1]:    # If uses in operand (str).
            argument_sample.append(float(0))
            argument_sample.append(float(len(_assert) - 2))
            for i in range(2, len(_assert)):
                possible_values += str(_assert[i])
                if i < len(_assert) - 1:
                    possible_values += ','

    argument_sample.append(True)    # IsAnArgument.
    argument_sample.append(False)   # IsAMethod.
    argument_sample.append(False)   # IsAReturnValue.

    # Argument/Return value names and types are assigned as blank.

    for i in range(20):
        argument_sample.append('')
        argument_sample.append('None')

    # If a default value exists, it is assigned to DefaultValue.

    if default_value is None:
        argument_sample.append('')
    else:
        argument_sample.append(default_value)

    argument_sample.append(possible_values) # PossibleValues.
    argument_sample.append(method_name) # BelongsTo.
    argument_sample.append(class_name)  # ClassName.
    argument_sample.append(is_not_a_model)  # UsedByView.
    return argument_sample

def min_value(_type):
    """
    Returns a minimum value associated with an int or float.

    Param:

    - _type (¿?): The data type of the associated value.

    Return:

    - value (float):  A small positive value based on the type.
    """
    value = 0.0
    if "int" in str(_type):
        value = 1.0
    elif "float" in str(_type):
        value = sys.float_info.epsilon
    return value

def get_return_value_sample(name, class_name, _type, method_name, is_not_a_model):
    """
    Adds the sample of the return value which current node corresponds.

    Param:

    - name (str): The name of the return value.
    - class_name (str): The name of the class in which the current node is located.
    - _type (¿?): The data type of the associated value.
    - method_name (str): The name of the method which the argument is passed as a parameter.
    - is_not_a_model (bool): Indicates if the class in which the current node is located is not a Model.

    Return:

    - return_sample (list): List of sample characteristics of the corresponding return value.
    """

    # Name, Type, From, To, IsAnArgument, IsAMethod, IsAReturnValue.

    return_sample = [name, _type, float_min, float_max, False, False, True]

    # Argument/Return value names and types are assigned as blank.

    for i in range(20):
        return_sample.append('')
        return_sample.append('None')

    return_sample.append('')    # DefaultValue.
    return_sample.append('')    # PossibleValues.
    return_sample.append(method_name)   # BelongsTo.
    return_sample.append(class_name)    # ClassName.
    return_sample.append(is_not_a_model)    # UsedByView.
    return return_sample