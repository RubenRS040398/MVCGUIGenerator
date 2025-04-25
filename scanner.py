import ast
import sys
import pandas as pd

data = []
float_min = 2.225074e-292
float_max = 1.797693e+292

def scan(source_code):
    tree = ast.parse(source_code)
    #print(ast.dump(tree, indent=4))
    _ = walk(tree, '', False, '')
    labels = ['Name', 'Type', 'From', 'To', 'IsAnArgument', 'IsAMethod', 'IsAReturnValue']
    for i in range(1, 11):
        labels.append('ArgumentName' + str(i))
        labels.append('ArgumentType' + str(i))
    for i in range(1, 11):
        labels.append('ReturnValueName' + str(i))
        labels.append('ReturnValueType' + str(i))
    labels.append('DefaultValue')
    labels.append('BelongsTo')
    labels.append('UseSmartView')
    test = pd.DataFrame(data, columns=labels)
    return test

def walk(node, name, is_a_class, smart_view_attr_name):
    smart_view_attr = smart_view_attr_name
    if "FunctionDef" in str(node) and is_a_class:
        if node.__dict__['name'] != '__init__':
            data.append(get_function_sample(node, name, smart_view_attr_name))
        else:
            i = 0
            found = False
            while i < len(node.__dict__['args'].__dict__['args']) and not found:
                if node.__dict__['args'].__dict__['args'][i].__dict__['annotation']:
                    if node.__dict__['args'].__dict__['args'][i].__dict__['annotation'].__dict__['id'] == 'SmartView':
                        smart_view_attr = node.__dict__['args'].__dict__['args'][i].__dict__['arg']
                        found = True
                    else:
                        i += 1
                else:
                    i += 1
    else:
        children = list(ast.iter_child_nodes(node))
        for child in children:
            #print(smart_view_attr)
            if "ClassDef" in str(child) and is_not_a_model(child):
                smart_view_attr = walk(child, child.__dict__['name'], True, '')
            else:
                smart_view_attr = walk(child, name, is_a_class, smart_view_attr)
    return smart_view_attr

def is_not_a_model(node):
    i = 0
    function = None
    found = False
    while i < len(node.__dict__['body']) and not found:
        if node.__dict__['body'][i].__dict__['name'] == '__init__':
            function = node.__dict__['body'][i]
            found = True
        else:
            i += 1
    found = True
    while i < len(function.__dict__['args'].__dict__['args']) and found:
        if function.__dict__['args'].__dict__['args'][i].__dict__['arg'] != 'self':
            match function.__dict__['args'].__dict__['args'][i].__dict__['annotation'].__dict__['id']:
                case 'int' | 'float' | 'complex' | 'str' | 'list' | 'tuple' | 'set' | 'dict':
                    found = False
                case _:
                    i += 1
        else:
            i += 1
    return found

def get_function_sample(node, class_name, smart_view_attr_name):
    function_sample = [node.__dict__['name']]
    if node.__dict__['returns']:
        if 'slice' in node.__dict__['returns'].__dict__:
            function_sample.append(node.__dict__['returns'].__dict__['value'].__dict__['id'])
        else:
            function_sample.append(node.__dict__['returns'].__dict__['id'])
    else:
        function_sample.append(str(node.__dict__['returns']))
    function_sample.append(float_min)
    function_sample.append(float_max)
    function_sample.append(False)
    function_sample.append(True)
    function_sample.append(False)
    arguments = []
    for argument in node.__dict__['args'].__dict__['args']:
        if argument.__dict__['arg'] != 'self':
            arguments.append(argument)
    while len(arguments) < 10:
        arguments.append(None)
    defaults = []
    default_index = 0
    for default in node.__dict__['args'].__dict__['defaults']:
        defaults.append(default.__dict__['value'])
    asserts = look_for_asserts(node)
    for argument in arguments:
        if not argument:
            function_sample.append('')
            function_sample.append('None')
        else:
            function_sample.append(argument.__dict__['arg'])
            if argument.__dict__['annotation']:
                function_sample.append(argument.__dict__['annotation'].__dict__['id'])
                data.append(get_argument_sample(argument, None, asserts, node.__dict__['name']))
            else:
                function_sample.append(type(defaults[default_index]).__name__)
                data.append(get_argument_sample(argument, defaults[default_index], asserts, node.__dict__['name']))
                default_index += 1
    if node.__dict__['returns']:
        if 'slice' in node.__dict__['returns'].__dict__:
            j = 0
            for return_value in node.__dict__['body'][-1].__dict__['value'].__dict__['elts']:
                if "Name" in str(return_value):
                    function_sample.append(str(return_value.__dict__['id']))
                    function_sample.append(node.__dict__['returns'].__dict__['slice'].__dict__['elts'][j].__dict__['id'])
                    data.append(get_return_sample(str(return_value.__dict__['id']),
                                                  node.__dict__['returns'].__dict__['slice'].__dict__['elts'][j].__dict__['id'], node.__dict__['name']))
                elif "Call" in str(return_value):
                    aux_name = return_value.__dict__['func'].__dict__['value'].__dict__['value'].__dict__['id']
                    aux_name += '.' + return_value.__dict__['func'].__dict__['value'].__dict__['attr']
                    aux_name += '.' + return_value.__dict__['func'].__dict__['attr']
                    function_sample.append(aux_name)
                    function_sample.append(node.__dict__['returns'].__dict__['slice'].__dict__['elts'][j].__dict__['id'])
                    data.append(get_return_sample(aux_name,
                                                  node.__dict__['returns'].__dict__['slice'].__dict__['elts'][j].__dict__['id'], node.__dict__['name']))
                elif "Constant" in str(return_value):
                    function_sample.append("unnamed_" + str(return_value.__dict__['value']))
                    function_sample.append(type(return_value.__dict__['value']).__name__)
                    data.append(get_return_sample("unnamed_" + str(return_value.__dict__['value']),
                                                  type(return_value.__dict__['value']).__name__, node.__dict__['name']))
                j += 1
            for i in range(j, 10):
                function_sample.append('')
                function_sample.append('None')
        else:
            aux_return = node.__dict__['body'][-1]
            if "Name" in str(aux_return.__dict__['value']):
                function_sample.append(str(aux_return.__dict__['value'].__dict__['id']))
                data.append(get_return_sample(str(aux_return.__dict__['value'].__dict__['id']),
                                              node.__dict__['returns'].__dict__['id'], node.__dict__['name']))
            elif "Call" in str(aux_return.__dict__['value']):
                aux_name = aux_return.__dict__['value'].__dict__['func'].__dict__['value'].__dict__['value'].__dict__['id']
                aux_name += '.' + aux_return.__dict__['value'].__dict__['func'].__dict__['value'].__dict__['attr']
                aux_name += '.' + aux_return.__dict__['value'].__dict__['func'].__dict__['attr']
                function_sample.append(aux_name)
                data.append(get_return_sample(aux_name, node.__dict__['returns'].__dict__['id'], node.__dict__['name']))
            elif "Constant" in str(aux_return.__dict__['value']):
                function_sample.append("unnamed_" + str(aux_return.__dict__['value'].__dict__['value']))
                data.append(get_return_sample("unnamed_" + str(aux_return.__dict__['value'].__dict__['value']),
                                              node.__dict__['returns'].__dict__['id'], node.__dict__['name']))
            function_sample.append(node.__dict__['returns'].__dict__['id'])
            for i in range(1, 10):
                function_sample.append('')
                function_sample.append('None')
    else:
        for i in range(10):
            function_sample.append('')
            function_sample.append('None')
    function_sample.append('')
    function_sample.append(class_name)
    function_sample.append(use_smart_view(node, smart_view_attr_name))
    return function_sample

def get_argument_sample(node, default_value, asserts, function_name):
    argument_sample = [node.__dict__['arg']]
    if default_value:
        argument_sample.append(type(default_value).__name__)
    else:
        argument_sample.append(node.__dict__['annotation'].__dict__['id'])
    _assert = None
    i = 0
    found = False
    while i < len(asserts) and not found:
        if node.__dict__['arg'] in asserts[i]:
            if "Gt" in asserts[i][1] or "Lt" in asserts[i][1]:
                _assert = asserts[i]
                found = True
        else:
            i += 1
    if _assert is None:
        argument_sample.append(float_min)
        argument_sample.append(float_max)
    elif len(_assert) == 3:
        if _assert.index(node.__dict__['arg']) == 0:
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
    elif len(_assert) == 5:
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
    argument_sample.append(True)
    argument_sample.append(False)
    argument_sample.append(False)
    for i in range (20):
        argument_sample.append('')
        argument_sample.append('None')
    if default_value is None:
        argument_sample.append('')
    else:
        argument_sample.append(default_value)
    argument_sample.append(function_name)
    argument_sample.append(False)
    return argument_sample

def get_return_sample(name, _type, function_name):
    return_sample = [name, _type, float_min, float_max, False, False, True]
    for i in range(20):
        return_sample.append('')
        return_sample.append('None')
    return_sample.append('')
    return_sample.append(function_name)
    return_sample.append(False)
    return return_sample

def look_for_asserts(node):
    asserts = []
    for _object in node.__dict__['body']:
        if "Assert" in str(_object):
            _assert = None
            if "Name" in str(_object.__dict__['test'].__dict__['left']):
                _assert = [_object.__dict__['test'].__dict__['left'].__dict__['id']]
            elif "Constant" in str(_object.__dict__['test'].__dict__['left']):
                _assert = [_object.__dict__['test'].__dict__['left'].__dict__['value']]
            for ops in _object.__dict__['test'].__dict__['ops']:
                _assert.append(str(ops))
            for comparator in _object.__dict__['test'].__dict__['comparators']:
                if "Name" in str(comparator):
                    _assert.append(comparator.__dict__['id'])
                elif "Constant" in str(comparator):
                    _assert.append(comparator.__dict__['value'])
            asserts.append(_assert)
    return asserts

def min_value(_type):
    if "int" in str(_type):
        return 1.0
    elif "float" in str(_type):
        return sys.float_info.epsilon

def use_smart_view(node, smart_view_attr_name):
    found = False
    for line in node.__dict__['body']:
        if line.__dict__['value']:
            if "Call" in str(line.__dict__['value']):
                if line.__dict__['value'].__dict__['func'].__dict__['value'].__dict__['attr'] == smart_view_attr_name:
                    found = True
    return found