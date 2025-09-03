import os
import pandas as pd
import re
import shutil

def generate(main_data, init_data, model_data, main_controller_name, title, about, view_threshold=3):
    """
    Generates the graphical interface.

    Param:

    - main_data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - init_data (pandas.core.frame.DataFrame): Model and Controller constructors data from the test dataset (methods only).
    - model_data (pandas.core.frame.DataFrame): Model data from the test dataset.
    - main_controller_name (str): The name of the main Controller.
    - title (str): The title of the application displayed in the main window.
    - about (str): Description of the application displayed in the About... window.
    - view_threshold (int): The minimum number of Controllers to split the View into multiple Views. Default value is 3.
    """

    # If these exist, remove the following files.

    if os.path.exists('code/main.py'):
        os.remove('code/main.py')
    if os.path.exists('code/utilities.py'):
        os.remove('code/utilities.py')
    if os.path.exists('code/view.py'):
        os.remove('code/view.py')
    if os.path.exists('code/icons'):
        shutil.rmtree('code/icons')

    # Create a folder for auxiliary icons.

    os.mkdir('code/icons')
    shutil.copy('media/GUIMVCLogo48px.png', 'code/icons/icon.png')
    shutil.copy('media/GUIMVCLogo32px.png', 'code/icons/default.png')
    shutil.copy('media/GUIMVCError32px.png', 'code/icons/error.png')
    shutil.copy('media/GUIMVCWarning32px.png', 'code/icons/warning.png')
    shutil.copy('media/GUIMVCEdit16px.png', 'code/icons/edit.png')
    shutil.copy('media/GUIMVCOthers16px.png', 'code/icons/others.png')
    shutil.copy('media/GUIMVCView16px.png', 'code/icons/view.png')
    views = create_main_file(init_data, model_data, main_controller_name, view_threshold)
    create_utilities_file()
    create_view_file(main_data, init_data, model_data, main_controller_name, title, about, views, view_threshold)

def create_main_file(init_data, model_data, main_controller_name, view_threshold=3):
    """
    Create the main.py file in the /code folder, which includes the declarations of the Models, Controllers, and Views
    necessary for the overall operation of the MVC architecture.

    Param:

    - init_data (pandas.core.frame.DataFrame): Model and Controller constructors data from the test dataset (methods only).
    - model_data (pandas.core.frame.DataFrame): Model data from the test dataset.
    - main_controller_name (str): The name of the main Controller.
    - view_threshold (int): The minimum number of Controllers to split the View into multiple Views. Default value is 3.

    Return:
    - views (dict): A dictionary with the Views keys and values as argument lists for each one.
    """
    folder = os.path.join(os.getcwd(), 'code')
    file_names = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    file_path = os.path.join('code', 'main.py')
    models = {}
    for index, row in init_data[init_data['UsedByView'] == True].iterrows():    # For each Controller constructor.
        i = 0
        while i < 10 and row['ArgumentName' + str(i + 1)] != '': # For each argument declare the required Models.
            aux_model_data = init_data[init_data['UsedByView'] == False]
            model_index = aux_model_data[aux_model_data['ClassName'] == row['ArgumentType' + str(i + 1)]].index.to_list()[0]
            model_key = row['ArgumentName' + str(i + 1)] + ',' + row['ArgumentType' + str(i + 1)]
            models[model_key] = []
            j = 0
            while j < 10 and init_data.loc[model_index, 'ArgumentName' + str(j + 1)] != '':

                # According to its type, declare a default value.

                match init_data.loc[model_index, 'ArgumentType' + str(j + 1)]:
                    case 'int':
                        models[model_key].append("0")
                    case 'float':
                        models[model_key].append("0.0")
                    case 'bool':
                        models[model_key].append("False")
                    case 'str':
                        models[model_key].append("''")
                    case 'complex':
                        models[model_key].append("complex()")
                    case 'list':
                        models[model_key].append("[]")
                    case 'tuple':
                        models[model_key].append("tuple()")
                    case 'set':
                        models[model_key].append("set()")
                    case 'dict':
                        models[model_key].append("{}")
                j += 1
            i += 1

    # For each Controller constructor, assign the declared models as arguments to each one.

    controllers = {}
    for index, row in init_data[init_data['UsedByView'] == True].iterrows():
        controllers[row['ClassName']] = []
        i = 0
        while i < 10 and row['ArgumentName' + str(i + 1)] != '':
            controllers[row['ClassName']].append(row['ArgumentName' + str(i + 1)])
            i += 1
    views = {}
    model_getters_data = model_data[model_data['IsAMethod'] == True]
    if len(controllers) <= view_threshold:  # If the minimum threshold of Controllers is not exceeded, these aredisplayed in the main window.
        views['View'] = [convert_to_camel_case(controller).lower().replace(' ', '_') for controller in controllers.keys()]

        # If the Models are set to be displayed in the GUI, their declaration must be included as arguments to the Controller constructor.

        if not model_getters_data[model_getters_data['Type'] != 'None'].empty:
            views['View'] += controllers[main_controller_name]
    else:   # Otherwise these are displayed across multiple windows.
        i = 66
        views['View'] = []

        # The remaining Views must be declared separately.

        for key in controllers:
            if key != main_controller_name:
                views['View' + chr(i)] = [convert_to_camel_case(key).lower().replace(' ', '_')]
                if not model_getters_data[model_getters_data['Type'] != 'None'].empty:
                    views['View' + chr(i)] += controllers[key]
                views['View'].append('view_' + chr(i).lower())
                i += 1
        views['View'].append(convert_to_camel_case(main_controller_name).lower().replace(' ', '_'))
        if not model_getters_data[model_getters_data['Type'] != 'None'].empty:
            views['View'] += controllers[main_controller_name]
    with open(file_path, 'w', encoding='utf-8') as file:
        for file_name in file_names:    # The main.py file imports source code files and the view.py file.
            if '.py' in file_name:
                file.write("from " + str(file_name.replace('.py', '')) + " import *\n")
        file.write("from view import *\n\n")

        # Write the declaration of the Models, Controllers and Views (following the previous order).

        for key, value in models.items():
            file.write(convert_to_camel_case(key.split(',')[0]).lower().replace(' ', '_') + " = " + key.split(',')[1] + "(" + ', '.join(value) + ")\n")
        for key, value in controllers.items():
            file.write(convert_to_camel_case(key).lower().replace(' ', '_') + " = " + key + "(" + ', '.join(value) + ")\n")
        for i in range(66, len(views) + 65):
            file.write("view_" + chr(i).lower() + " = View" + chr(i) + "(" + ', '.join(views['View' + chr(i)]).lower() + ")\n")
        file.write("view = View(" + ', '.join(views['View']) + ")\n")
    return views

def create_utilities_file():
    """
    Creates the utilities.py file in the /code folder, which includes auxiliary functions.
    """
    file_path = os.path.join('code', 'utilities.py')
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write("def convert_str(value):\n")
        file.write("\tvalue = value.strip()\n")
        file.write("\tif value in ['True', 'False']:\n")
        file.write("\t\treturn value == 'True'\n")
        file.write("\ttry:\n")
        file.write("\t\treturn int(value)\n")
        file.write("\texcept ValueError:\n")
        file.write("\t\tpass\n")
        file.write("\ttry:\n")
        file.write("\t\treturn float(value)\n")
        file.write("\texcept ValueError:\n")
        file.write("\t\tpass\n")
        file.write("\ttry:\n")
        file.write("\t\tresult = complex(value)\n")
        file.write("\t\treturn result\n")
        file.write("\texcept ValueError:\n")
        file.write("\t\tpass\n")
        file.write("\treturn value\n\n")
        file.write("def get_treeview_items_rec(treeview, parent='', is_in_dict=False):\n")
        file.write("\titems = []\n")
        file.write("\tdict_items = {}\n")
        file.write("\tfor item_id in treeview.get_children(parent):\n")
        file.write("\t\tnum_children = len(treeview.get_children(item_id))\n")
        file.write("\t\titem = treeview.item(item_id)\n")
        file.write("\t\tif num_children == 0:\n")
        file.write("\t\t\tif item['text'] in ['<Empty>', '<Vacío>', '<Buit>']:\n")
        file.write("\t\t\t\titems.append('')\n")
        file.write("\t\t\telse:\n")
        file.write("\t\t\t\titems.append(convert_str(item['text']))\n")
        file.write("\t\telse:\n")
        file.write("\t\t\tif item['text'] == '[0]' or item['text'] == '[0..' + str(num_children - 1) + ']':\n")
        file.write("\t\t\t\titems.append(get_treeview_items_rec(treeview, item_id)[0])\n")
        file.write("\t\t\telse:\n")
        file.write("\t\t\t\tdict_items[item['text']] = get_treeview_items_rec(treeview, item_id, True)[0]\n")
        file.write("\tif dict_items:\n")
        file.write("\t\titems.append(dict_items)\n")
        file.write("\tif len(items) == 1 and isinstance(items, list) and is_in_dict:\n")
        file.write("\t\treturn items[0], True\n")
        file.write("\telse:\n")
        file.write("\t\treturn items, False\n\n")
        file.write("def get_treeview_items(treeview, _type):\n")
        file.write("\titems, is_one_item = get_treeview_items_rec(treeview)\n")
        file.write("\n")
        file.write("\tdef convert_lists_and_dicts_to_strings(obj):\n")
        file.write("\t\tif isinstance(obj, list) or isinstance(obj, dict):\n")
        file.write("\t\t\treturn str(obj)\n")
        file.write("\t\treturn obj\n")
        file.write("\n")
        file.write("\tif 'list' in str(type(items)) and not is_one_item:\n")
        file.write("\t\tmatch _type:\n")
        file.write("\t\t\tcase 'tuple':\n")
        file.write("\t\t\t\titems = tuple(items)\n")
        file.write("\t\t\tcase 'set':\n")
        file.write("\t\t\t\titems = set(convert_lists_and_dicts_to_strings(i) for i in items)\n")
        file.write("\t\t\tcase 'dict':\n")
        file.write("\t\t\t\titems = {'': items}\n")
        file.write("\telif is_one_item:\n")
        file.write("\t\tmatch _type:\n")
        file.write("\t\t\tcase 'list':\n")
        file.write("\t\t\t\titems = [items]\n")
        file.write("\t\t\tcase 'tuple':\n")
        file.write("\t\t\t\titems = (items,)\n")
        file.write("\t\t\tcase 'set':\n")
        file.write("\t\t\t\tif isinstance(items, dict):\n")
        file.write("\t\t\t\t\titems = {str(items)}\n")
        file.write("\t\t\t\telse:\n")
        file.write("\t\t\t\t\titems = {items}\n")
        file.write("\t\t\tcase 'dict':\n")
        file.write("\t\t\t\tif not isinstance(items, dict):\n")
        file.write("\t\t\t\t\titems = {'': items}\n")
        file.write("\treturn items\n\n")
        file.write("def get_boolean_str(value, language):\n")
        file.write("\tboolean_str = ''\n")
        file.write("\tif value:\n")
        file.write("\t\tmatch language:\n")
        file.write("\t\t\tcase 'en':\n")
        file.write("\t\t\t\tboolean_str = 'True'\n")
        file.write("\t\t\tcase 'es':\n")
        file.write("\t\t\t\tboolean_str = 'Verdadero'\n")
        file.write("\t\t\tcase 'ca':\n")
        file.write("\t\t\t\tboolean_str = 'Vertader'\n")
        file.write("\telse:\n")
        file.write("\t\tmatch language:\n")
        file.write("\t\t\tcase 'en':\n")
        file.write("\t\t\t\tboolean_str = 'False'\n")
        file.write("\t\t\tcase 'es':\n")
        file.write("\t\t\t\tboolean_str = 'Falso'\n")
        file.write("\t\t\tcase 'ca':\n")
        file.write("\t\t\t\tboolean_str = 'Fals'\n")
        file.write("\treturn boolean_str\n\n")
        file.write("def get_boolean_fg(value):\n")
        file.write("\tboolean_fg = ''\n")
        file.write("\tif value:\n")
        file.write("\t\tboolean_fg = 'green'\n")
        file.write("\telse:\n")
        file.write("\t\tboolean_fg = 'red'\n")
        file.write("\treturn boolean_fg\n\n")
        file.write("def set_treeview_items_rec(treeview, return_value, empty_str, parent='', is_the_root=False):\n")
        file.write("\tif isinstance(return_value, dict):\n")
        file.write("\t\tfor key in list(return_value.keys()):\n")
        file.write("\t\t\titem_id = treeview.insert(parent, 'end', text=key)\n")
        file.write("\t\t\tif isinstance(return_value[key], (list, tuple, set)):\n")
        file.write("\t\t\t\tif len(return_value[key]) == 1:\n")
        file.write("\t\t\t\t\tset_treeview_items_rec(treeview, return_value[key], empty_str, item_id, is_the_root)\n")
        file.write("\t\t\t\telse:\n")
        file.write("\t\t\t\t\tfor item in return_value[key]:\n")
        file.write("\t\t\t\t\t\tset_treeview_items_rec(treeview, item, empty_str, item_id, is_the_root)\n")
        file.write("\t\t\telse:\n")
        file.write("\t\t\t\tset_treeview_items_rec(treeview, return_value[key], empty_str, item_id, is_the_root)\n")
        file.write("\telif isinstance(return_value, (list, tuple, set)):\n")
        file.write("\t\tif not is_the_root:\n")
        file.write("\t\t\tif len(return_value) == 1:\n")
        file.write("\t\t\t\titem_id = treeview.insert(parent, 'end', text='[0]')\n")
        file.write("\t\t\telse:\n")
        file.write("\t\t\t\titem_id = treeview.insert(parent, 'end', text='[0..' + str(len(return_value) - 1) + ']')\n")
        file.write("\t\telse:\n")
        file.write("\t\t\titem_id = parent\n")
        file.write("\t\tfor item in return_value:\n")
        file.write("\t\t\tset_treeview_items_rec(treeview, item, empty_str, item_id)\n")
        file.write("\telse:\n")
        file.write("\t\tif return_value == '':\n")
        file.write("\t\t\ttreeview.insert(parent, 'end', text=empty_str)\n")
        file.write("\t\telse:\n")
        file.write("\t\t\ttreeview.insert(parent, 'end', text=str(return_value))\n\n")
        file.write("def set_treeview_items(treeview, return_value, language):\n")
        file.write("\tempty_str = ''\n")
        file.write("\tmatch language:\n")
        file.write("\t\tcase 'en':\n")
        file.write("\t\t\tempty_str = '<Empty>'\n")
        file.write("\t\tcase 'es':\n")
        file.write("\t\t\tempty_str  = '<Vacío>'\n")
        file.write("\t\tcase 'ca':\n")
        file.write("\t\t\tempty_str = '<Buit>'\n")
        file.write("\tfor item in treeview.get_children():\n")
        file.write("\t\ttreeview.delete(item)\n")
        file.write("\tif isinstance(return_value, dict):\n")
        file.write("\t\tset_treeview_items_rec(treeview, [return_value], empty_str, is_the_root=True)\n")
        file.write("\telse:\n")
        file.write("\t\tset_treeview_items_rec(treeview, return_value, empty_str, is_the_root=True)\n")

def create_view_file(main_data, init_data, model_data, main_controller_name, title, about, views, view_threshold=3):
    """
    Create the view.py file in the /code folder, where the classes for each View are defined. The Tk() object is
    declared to begin the construction of the GUI.

    Param:

    - main_data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - init_data (pandas.core.frame.DataFrame): Model and Controller constructors data from the test dataset (methods only).
    - model_data (pandas.core.frame.DataFrame): Model data from the test dataset.
    - main_controller_name (str): The name of the main Controller.
    - title (str): The title of the application displayed in the main window.
    - about (str): Description of the application displayed in the About... window.
    - views (dict): A dictionary with the Views keys and values as argument lists for each one.
    - view_threshold (int): The minimum number of Controllers to split the View into multiple Views. Default value is 3.
    """
    file_path = os.path.join('code', 'view.py')
    with (open(file_path, 'w', encoding='utf-8') as file):

        # Imports the required libraries.

        file.write("from tkinter import *\n")
        file.write("from tkinter import ttk\n")
        file.write("from tkinter import font\n")
        file.write("from ctypes import windll\n")
        file.write("from collections import defaultdict\n")
        file.write("from utilities import *\n")
        file.write("import re\n\n")

        # Declare the root objects of each window (to prevent multiple windows from showing up when one is already open).

        for k in range(1, len(views)):
            file.write("root_" + str(k) + " = None\n")
        for row in main_data[main_data['Widget'] == "Menubutton"].itertuples():
            if row.ArgumentName1 != '' or row.ReturnValueName1 != '':
                file.write("root_menu_" + str(row.Index) + " = None\n")
        method_data = main_data[main_data['IsAMethod'] == True]
        for row in method_data[method_data['Window'] == True].itertuples():
            file.write("root_window_" + str(row.Index) + " = None\n")
        file.write("root_message_box = None\n\n")

        # Declare the View class (main controller).

        i = 0  # LabelFrame counter.
        x = 0  # Grid X position.
        y = 0  # Grid Y position.
        file.write("class View:\n")
        file.write("\tdef __init__(self, " + ', '.join(views['View']).lower() + "):\n")
        for value in views['View']:
            file.write("\t\tself." + value + " = " + value + "\n")
        file.write("\t\twindll.shcore.SetProcessDpiAwareness(1)\n") # Prevents the interface from looking blurry.
        file.write("\t\tself.root = Tk()\n")    # Sets main window root variable as Tk() object.
        file.write("\t\tself.root.title('" + title + "')\n")    # Title.
        file.write("\t\tself.root.resizable(False, False)\n")   # Not resizable.
        file.write("\t\tself.root.minsize(320, 0)\n")   # Minimum width size.
        file.write("\t\tself.root.columnconfigure(0, weight=1)\n")
        file.write("\t\tself.root.columnconfigure(1, weight=1)\n")
        file.write("\t\tself.root.columnconfigure(2, weight=1)\n")
        file.write("\t\tw = (self.root.winfo_screenwidth() - self.root.winfo_reqwidth()) // 2\n")
        file.write("\t\th = (self.root.winfo_screenheight() - self.root.winfo_reqheight()) // 8\n")
        file.write("\t\tself.root.geometry(f'+{w}+{h}')\n") # Sets window position.
        file.write("\t\ticon = PhotoImage(file='icons/icon.png')\n")
        file.write("\t\tself.root.iconphoto(False, icon)\n")    # Icon.
        file.write("\t\tbold_font = font.nametofont('TkDefaultFont').copy()\n") # Sets bold font style.
        file.write("\t\tbold_font.configure(weight='bold')\n")
        file.write("\t\tstyle = ttk.Style()\n")
        file.write("\t\tstyle.configure('Bold.TLabelframe.Label', font=bold_font)\n")

        # Sets the Model attributes to be displayed in the main window (main Controller).

        model_attr, i, x, y = set_model_attr_labels(file, main_data, init_data, model_data, main_controller_name, i, x, y, "self.root")
        create_menu(file, main_data, model_data, main_controller_name, about, views, model_attr)    # Creates the main window menu.

        # Main controller LabelFrame.

        x = 0   # Grid X position.
        y = 0   # Grid Y position.
        file.write("\t\tcont_" + str(i) + " = ttk.LabelFrame(self.root, text='" +
                   convert_to_camel_case(main_controller_name) + "', style='Bold.TLabelframe')\n")
        file.write("\t\tcont_" + str(i) + ".grid(row=" + str(i) + ", column=0, padx=4, pady=4, sticky='we', columnspan=3)\n")
        file.write("\t\tcont_" + str(i) + ".columnconfigure(0, weight=1)\n")
        file.write("\t\tcont_" + str(i) + ".columnconfigure(1, weight=1)\n")
        file.write("\t\tcont_" + str(i) + ".columnconfigure(2, weight=1)\n")

        # Sets merged arguments first (main controller).

        i, x, y = set_merged_arguments(file, main_data, main_controller_name, 0, i, x, y, "cont_" + str(i))
        method_data = main_data[main_data['ClassName'] == main_controller_name]

        # Create the main Controller widgets.

        x, y = create_widgets(file, method_data[method_data['Widget'] != 'Menubutton'], model_data, main_controller_name, model_attr, 0, x, y,
                             "cont_" + str(i), "\t\t", True, True)

        # Sets merged return values (main controller).

        i, x, y = set_merged_return_values(file, main_data, main_controller_name, i, x, y, "cont_" + str(i))

        # Grabs the rest of the controllers.

        remaining_controllers = list(main_data[main_data['ClassName'] != main_controller_name]['ClassName'].unique())
        if len(remaining_controllers) + 1 <= view_threshold:    # If it does not exceed the threshold, writing continues on the same class.
            for actual_view in range(len(remaining_controllers)):   # For each remaining Controller.
                i += 1  # LabelFrame counter.
                x = 0   # Grid X position.
                y = 0   # Grid Y position.
                file.write("\t\tcont_" + str(i) + " = ttk.LabelFrame(self.root, text='" +
                           convert_to_camel_case(remaining_controllers[actual_view]) + "', style='Bold.TLabelframe')\n")
                file.write("\t\tcont_" + str(i) + ".grid(row=" + str(i) + ", column=0, padx=4, pady=4, sticky='we', columnspan=3)\n")
                file.write("\t\tcont_" + str(i) + ".columnconfigure(0, weight=1)\n")
                file.write("\t\tcont_" + str(i) + ".columnconfigure(1, weight=1)\n")
                file.write("\t\tcont_" + str(i) + ".columnconfigure(2, weight=1)\n")

                # Sets merged arguments first.

                i, x, y = set_merged_arguments(file, main_data, remaining_controllers[actual_view], 0, i, x, y, "cont_" + str(i))
                method_data = main_data[main_data['ClassName'] == remaining_controllers[actual_view]]

                # Create the current Controller widgets.

                x, y = create_widgets(file, method_data[method_data['Widget'] != 'Menubutton'], model_data, main_controller_name,
                                      model_attr, 0, x, y, "cont_" + str(i), "\t\t", True, True)

                # Sets merged return values (main controller).

                i, x, y = set_merged_return_values(file, main_data, remaining_controllers[actual_view], i, x, y, "cont_" + str(i))
            file.write("\t\tself.root.mainloop()\n\n")

            # Definition of message_box() method (View class).

            define_message_box(file)

            # If the content of the model attributes needs to be displayed, then the update() method is defined.

            if model_attr:
                define_update(file, main_data, model_data, model_attr)
        else:   # If it is above the threshold, each Controller is displayed in separate Views.
            file.write("\t\tself.root.mainloop()\n\n")

            # Definition of message_box() method (View class).

            define_message_box(file)

            # If the content of the model attributes needs to be displayed, then the update() method is defined.

            if model_attr:
                define_update(file, main_data, model_data, model_attr)
            for actual_view in range(len(views.keys()) - 1):    # For each remaining View.

                # Declares the remaining classes.

                file.write("class View" + chr(66 + actual_view) + ":\n")
                file.write("\tdef __init__(self, " + ', '.join(views['View' + chr(66 + actual_view)]) + "):\n")
                for value in views['View' + chr(66 + actual_view)]:
                    file.write("\t\tself." + value + " = " + value + "\n")
                file.write("\t\tself." + convert_to_camel_case(views['View' + chr(66 + actual_view)][0]).lower().replace(' ', '_')
                           + " = " + convert_to_camel_case(views['View' + chr(66 + actual_view)][0]).lower().replace(' ', '_') + "\n")
                for k in range(1, len(views['View' + chr(66 + actual_view)])):
                    file.write("\t\tself." + views['View' + chr(66 + actual_view)][k] + " = " + views['View' + chr(66 + actual_view)][k] + "\n")

                # Defines the show() method for the current class.

                i = 0   # LabelFrame counter.
                x = 0   # Grid X position.
                y = 0   # Grid Y position.
                file.write("\n\tdef show(self, view, bold_font, icon_image):\n")
                file.write("\t\tglobal root_" + str(actual_view + 1) + "\n")
                file.write("\t\tif root_" + str(actual_view + 1) + " and root_" + str(actual_view + 1) + ".winfo_exists():\n")
                file.write("\t\t\troot_" + str(actual_view + 1) + ".lift()\n")
                file.write("\t\t\treturn\n")
                file.write("\t\troot_" + str(actual_view + 1) + " = Toplevel(view.root)\n") # Sets window root variable as Toplevel() object.
                file.write("\t\troot_" + str(actual_view + 1) + ".title('" +
                           views['View' + chr(66 + actual_view)][0][0].upper() +
                           views['View' + chr(66 + actual_view)][0][1:].replace('_', ' ') + "...')\n")  # Title.
                file.write("\t\troot_" + str(actual_view + 1) + ".resizable(False, False)\n")   # Not resizable.
                file.write("\t\troot_" + str(actual_view + 1) + ".minsize(320, 0)\n")   # Minimum width size.
                file.write("\t\troot_" + str(actual_view + 1) + ".columnconfigure(0, weight=1)\n")
                file.write("\t\troot_" + str(actual_view + 1) + ".columnconfigure(1, weight=1)\n")
                file.write("\t\troot_" + str(actual_view + 1) + ".columnconfigure(2, weight=1)\n")
                file.write("\t\tw_" + str(actual_view + 1) + " = (root_" + str(actual_view + 1) + ".winfo_screenwidth() - ")
                file.write("root_" + str(actual_view + 1) + ".winfo_reqwidth()) // 2\n")
                file.write("\t\th_" + str(actual_view + 1) + " = (root_" + str(actual_view + 1) + ".winfo_screenheight() - ")
                file.write("root_" + str(actual_view + 1) + ".winfo_reqheight()) // 8\n")
                file.write("\t\troot_" + str(actual_view + 1) + ".geometry(f'+{w_" + str(actual_view + 1)
                           + "}+{h_" + str(actual_view + 1) + "}')\n")  # Sets window position.
                file.write("\t\ticon_" + str(actual_view + 1) + " = PhotoImage(file=icon_image)\n") # Icon.
                file.write("\t\troot_" + str(actual_view + 1) + ".iconphoto(False, icon_" + str(actual_view + 1) + ")\n")

                # Sets the Model attributes to be displayed in the actual window.

                model_attr, i, x, y = set_model_attr_labels(file, main_data, init_data, model_data,
                                                            ''.join(word.capitalize() for word in views['View' + chr(66 + actual_view)][0].split('_')),
                                                            i, x, y, "root_" + str(actual_view + 1))

                # Current controller LabelFrame.

                x = 0   # Grid X position.
                y = 0   # Grid Y position.
                frame_title = views['View' + chr(66 + actual_view)][0][0].upper() + views['View' + chr(66 + actual_view)][0][1:].replace('_', ' ')
                file.write("\t\tcont_" + str(i) + " = ttk.LabelFrame(root_" + str(actual_view + 1) + ", ")
                file.write("text='" + frame_title + "', style='Bold.TLabelframe')\n")
                file.write("\t\tcont_" + str(i) + ".grid(row=" + str(i) + ", column=0, padx=4, pady=4, sticky='we', columnspan=3)\n")
                file.write("\t\tcont_" + str(i) + ".columnconfigure(0, weight=1)\n")
                file.write("\t\tcont_" + str(i) + ".columnconfigure(1, weight=1)\n")
                file.write("\t\tcont_" + str(i) + ".columnconfigure(2, weight=1)\n")

                # Sets merged arguments first.

                i, x, y = set_merged_arguments(file, main_data, ''.join(
                    word.capitalize() for word in views['View' + chr(66 + actual_view)][0].split('_')), actual_view + 1, i, x, y,
                                               "cont_" + str(i))
                method_data = main_data[main_data['ClassName'] == ''.join(word.capitalize() for word in views['View' + chr(66 + actual_view)][0].split('_'))]
                method_data = method_data[method_data['Window'] == False]

                # Create the current Controller widgets.

                x, y = create_widgets(file, method_data[method_data['Widget'] != 'Menubutton'], model_data, main_controller_name,
                                      model_attr, actual_view + 1, x, y, "cont_" + str(i), "\t\t", True,
                                      True)

                # Sets merged return values (main controller).

                i, x, y = set_merged_return_values(file, main_data,
                                                   ''.join(word.capitalize() for word in views['View' + chr(66 + actual_view)][0].split('_')),
                                                   i, x, y, "cont_" + str(i))
                i += 1
                file.write("\t\tframe_" + str(actual_view) + " = Frame(root_" + str(actual_view + 1) + ")\n\t\tframe_"
                           + str(actual_view) + ".grid(row=" + str(i) + ", column=0, columnspan=3, sticky='we')\n")
                file.write("\t\tframe_" + str(actual_view) + ".columnconfigure(0, weight=1)\n")

                # If there are methods that should be displayed in a separate window, the buttons that open the
                # respective windows are established.

                window_data = main_data[main_data['ClassName'] == ''.join(word.capitalize() for word in views['View' + chr(66 + actual_view)][0].split('_'))]
                window_data = window_data[window_data['Window'] == True]
                window_data = window_data[window_data['IsAMethod'] == True]
                if not window_data.empty:
                    aux_x = x - 1
                    for index, row in window_data.iterrows():
                        set_window_widgets(file, main_data, model_data, main_controller_name, actual_view, model_attr, row, index)
                        file.write("\n\t\twidget_" + str(index) + " = ttk.Button(cont_" + str(i - 1) + ", text='" + row['WidgetLabel'] + "', command=lambda:trigger_window_" + str(index) + "())\n")
                        file.write("\t\twidget_" + str(index) + ".grid(row=" + str(aux_x) + ", column=0, padx=4, pady=4, sticky='', columnspan=3)\n")
                        aux_x += 1
                file.write("\t\tclose = ttk.Button(frame_" + str(actual_view) + ", text='") # Sets close button.
                match main_data['LanguageID'].mode()[0]:
                    case 'en':
                        file.write("Close")
                    case 'es':
                        file.write("Cerrar")
                    case 'ca':
                        file.write("Tancar")
                file.write("', command=root_" + str(actual_view + 1) + ".destroy, width=12)\n")
                file.write("\t\tclose.grid(row=0, column=0, padx=4, pady=4)\n\n")
                file.write("\t\tdef on_close_" + str(actual_view + 1) + "():\n")
                file.write("\t\t\tglobal root_" + str(actual_view + 1) + "\n")
                file.write("\t\t\troot_" + str(actual_view + 1) + ".destroy()\n")
                file.write("\t\t\troot_" + str(actual_view + 1) + " = None\n\n")
                file.write("\t\troot_" + str(actual_view + 1) + ".protocol('WM_DELETE_WINDOW', on_close_" + str(actual_view + 1) + ")\n")
                file.write("\n")

def create_menu(file, main_data, model_data, main_controller_name, about, views, model_attr):
    """
    Sets the main window menu to View class.

    Param:

    - file (_io.TextIOWrapper): File input/output reference.
    - main_data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - model_data (pandas.core.frame.DataFrame): Model data from the test dataset.
    - main_controller_name (str): The name of the main Controller.
    - about (str): Description of the application displayed in the About... window.
    - views (dict): A dictionary with the Views keys and values as argument lists for each one.
    - model_attr (list): List of indexs from Model attribute getters.
    """
    file.write("\t\tmenu = Menu(self.root)\n")  # Sets the menu root as Menu() object from main root.
    file.write("\t\tself.root.config(menu=menu)\n")
    file.write("\t\tfile = Menu(menu, tearoff=0)\n")
    file.write("\t\tmenu.add_cascade(label='")

    # Sets File menu button.

    match main_data['LanguageID'].mode()[0]:
        case 'en':
            file.write("File")
        case 'es':
            file.write("Archivo")
        case 'ca':
            file.write("Fitxer")
    file.write("', menu=file)\n")

    # If methods with no arguments/return values exist in the main Controller, they are added as File menu buttons.

    menubutton_data = main_data[main_data['Widget'] == 'Menubutton']
    menubutton_data = menubutton_data[menubutton_data['ArgumentName1'] == '']
    for index, row in menubutton_data[menubutton_data['ReturnValueName1'] == ''].iterrows():
        file.write("\t\tfile.add_command(label='" + row['WidgetLabel'] + "', command=lambda:self." +
                   convert_to_camel_case(row['ClassName']).lower().replace(' ', '_') + "." + row['Name'] + "())\n")
    if not menubutton_data[menubutton_data['ReturnValueName1'] == ''].empty:
        file.write("\t\tfile.add_separator()\n")
    file.write("\t\tfile.add_command(label='") # Exit button is added to File menu.
    match main_data['LanguageID'].mode()[0]:
        case 'en':
            file.write("Exit")
        case 'es':
            file.write("Salir")
        case 'ca':
            file.write("Sortir")
    file.write("', command=self.root.quit)\n")
    menubutton_data = main_data[main_data['Widget'] == 'Menubutton']
    menubutton_data = menubutton_data[menubutton_data['ArgumentName1'] != '']

    # Sets Edit menu button.

    view_char = []

    # If more than one view exists and all Controller methods do not return values, it is added to the Edit menu.

    if len(views) > 1:
        for i in range(len(views) - 1):
            aux_data = main_data[main_data['ClassName'] == ''.join(word.capitalize() for word in views['View' + chr(66 + i)][0].split('_'))]
            if aux_data[aux_data['ReturnValueName1'] != ''].empty:
                view_char.append(i)

    # If there are methods in the main Controller that do not return any value, they are added to the Edit menu.

    if not menubutton_data[menubutton_data['ReturnValueName1'] == ''].empty or view_char:
        file.write("\t\tedit = Menu(menu, tearoff=0)\n")
        file.write("\t\tmenu.add_cascade(label='")
        match main_data['LanguageID'].mode()[0]:
            case 'en':
                file.write("Edit")
            case 'es' | 'ca':
                file.write("Editar")
        file.write("', menu=edit)\n")

        # For each method that does not return a value, a window is created.

        for index, row in menubutton_data[menubutton_data['ReturnValueName1'] == ''].iterrows():
            set_window_widgets(file, main_data, model_data, main_controller_name, 0, model_attr, row, index, True)
            file.write("\n\t\tedit.add_command(label='" + row['WidgetLabel'] + "', command=lambda:trigger_menu_" + str(index) + "())\n")
        if view_char:
            if not menubutton_data[menubutton_data['ReturnValueName1'] == ''].empty:
                file.write("\t\tedit.add_separator()\n")
            for char in view_char:  # Adds the Controller view buttons.
                file.write("\t\tedit.add_command(label='" + views['View' + chr(66 + char)][0][0].upper()
                           + views['View' + chr(66 + char)][0][1:].replace('_', ' ') +
                           "...', command=lambda:view_" + chr(66 + char).lower() + ".show(self, bold_font, 'icons/edit.png'))\n")
    menubutton_data = main_data[main_data['Widget'] == 'Menubutton']
    menubutton_data = menubutton_data[menubutton_data['ReturnValueName1'] != '']

    # Sets View menu button.

    view_char = []

    # If more than one view exists and all Controller methods do not have arguments, it is added to the View menu.

    if len(views) > 1:
        for i in range(len(views) - 1):
            aux_data = main_data[main_data['ClassName'] == ''.join(word.capitalize() for word in views['View' + chr(66 + i)][0].split('_'))]
            if aux_data[aux_data['ArgumentName1'] != ''].empty:
                view_char.append(i)

    # If there are methods in the main Controller that do not have any arguments, they are added to the View menu.

    if not menubutton_data[menubutton_data['ArgumentName1'] == ''].empty or view_char:
        file.write("\t\tview = Menu(menu, tearoff=0)\n\t\tmenu.add_cascade(label='")
        match main_data['LanguageID'].mode()[0]:
            case 'en':
                file.write("View")
            case 'es':
                file.write("Ver")
            case 'ca':
                file.write("Veure")
        file.write("', menu=view)\n")

        # For each method that does not have arguments, a window is created.

        for index, row in menubutton_data[menubutton_data['ArgumentName1'] == ''].iterrows():
            set_window_widgets(file, main_data, model_data, main_controller_name, 0, model_attr, row, index, True)
            file.write("\n\t\tview.add_command(label='" + row['WidgetLabel'] + "', command=lambda:trigger_menu_" + str(index) + "())\n")
        if view_char:
            if not menubutton_data[menubutton_data['ArgumentName1'] == ''].empty:
                file.write("\t\tview.add_separator()\n")
            for char in view_char:
                file.write("\t\tview.add_command(label='" + views['View' + chr(66 + char)][0][0].upper()
                           + views['View' + chr(66 + char)][0][1:].replace('_', ' ') +
                           "...', command=lambda:view_" + chr(66 + char).lower() + ".show(self, bold_font, 'icons/view.png'))\n")
    menubutton_data = main_data[main_data['Widget'] == 'Menubutton']
    menubutton_data = menubutton_data[menubutton_data['ArgumentName1'] != '']

    # Sets Others menu button.

    view_char = []

    # If more than one view exists and all Controller methods have arguments/return values, it is added to the Others menu.

    if len(views) > 1:
        for i in range(len(views) - 1):
            aux_data = main_data[main_data['ClassName'] == ''.join(word.capitalize() for word in views['View' + chr(66 + i)][0].split('_'))]
            if not aux_data[aux_data['ArgumentName1'] != ''].empty and not aux_data[aux_data['ReturnValueName1'] != ''].empty:
                view_char.append(i)

    # If there are methods in the main Controller that have arguments/return values, they are added to the Others menu.

    if not menubutton_data[menubutton_data['ReturnValueName1'] != ''].empty or view_char:
        file.write("\t\tothers = Menu(menu, tearoff=0)\n\t\tmenu.add_cascade(label='")
        match main_data['LanguageID'].mode()[0]:
            case 'en':
                file.write("Others")
            case 'es':
                file.write("Otros")
            case 'ca':
                file.write("Altres")
        file.write("', menu=others)\n")

        # For each method that has arguments/return values, a window is created.

        for index, row in menubutton_data[menubutton_data['ReturnValueName1'] != ''].iterrows():
            set_window_widgets(file, main_data, model_data, main_controller_name, 0, model_attr, row, index, True)
            file.write("\n\t\tothers.add_command(label='" + row['WidgetLabel'] + "', command=lambda:trigger_menu_" + str(index) + "())\n")
        if view_char:
            if not menubutton_data[menubutton_data['ReturnValueName1'] != ''].empty:
                file.write("\t\tothers.add_separator()\n")
            for char in view_char:
                file.write("\t\tothers.add_command(label='" + views['View' + chr(66 + char)][0][0].upper()
                           + views['View' + chr(66 + char)][0][1:].replace('_', ' ') +
                           "...', command=lambda:view_" + chr(66 + char).lower() + ".show(self, bold_font, 'icons/others.png'))\n")
    file.write("\t\t_help = Menu(menu, tearoff=0)\n\t\tmenu.add_cascade(label='")

    # Sets Help menu button.

    match main_data['LanguageID'].mode()[0]:
        case 'en':
            file.write("Help")
        case 'es':
            file.write("Ayuda")
        case 'ca':
            file.write("Ajuda")
    file.write("', menu=_help)\n\t\t_help.add_command(label='")
    match main_data['LanguageID'].mode()[0]:
        case 'en':
            file.write("About...', command=lambda:self.message_box(self.root, 'About...', '" + about + "', 'en'))\n")
        case 'es':
            file.write("Acerca de...', command=lambda:self.message_box(self.root, 'Acerca de...', '" + about + "', 'es'))\n")
        case 'ca':
            file.write("Sobre...', command=lambda:self.message_box(self.root, 'Sobre...', '" + about + "', 'ca'))\n")

def set_model_attr_labels(file, main_data, init_data, model_data, controller, i, x, y, root):
    """
    Sets the Model attributes to display in each View, as long as they exist as sample return values in model_data.

    Param:

    - file (_io.TextIOWrapper): File input/output reference.
    - main_data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - init_data (pandas.core.frame.DataFrame): Model and Controller constructors data from the test dataset (methods only).
    - model_data (pandas.core.frame.DataFrame): Model data from the test dataset.
    - controller (str): The name of the current Controller.
    - i (int): LabelFrame counter.
    - x (int): Grid X position.
    - y (int): Grid Y position.
    - root (str): Root name.

    Return:

    - model_attr (list): List of indexs from Model attribute getters.
    - i (int): LabelFrame counter.
    - x (int): Grid X position.
    - y (int): Grid Y position.
    """
    model_attr = []
    aux_data = init_data.loc[init_data['ClassName'] == controller]
    init_aux_data = aux_data.loc[aux_data.index.tolist()[0]]

    # For each argument of the Controller constructor, we find the getters of the Models it uses.

    k = 0
    while init_aux_data['ArgumentName' + str(k + 1)] != '' and k < 10:
        aux_data = model_data[model_data['ClassName'] == init_aux_data['ArgumentType' + str(k + 1)]]
        aux_data = aux_data[aux_data['UsedByController'] == controller]
        aux_data = aux_data[aux_data['ModelName'] == init_aux_data['ArgumentName' + str(k + 1)]]

        # A LabelFrame is created if return values exist for the Model attributes.

        if not aux_data[aux_data['Name'].isin(list(aux_data[aux_data['IsAReturnValue']]['BelongsTo']))].empty:
            x = 0   # Grid X position.
            y = 0   # Grid Y position.
            frame_title = init_aux_data['ArgumentName' + str(k + 1)][0].upper() + init_aux_data['ArgumentName' + str(k + 1)][1:].replace('_', ' ')
            file.write("\t\tcont_" + str(i) + " = ttk.LabelFrame(" + root + ", text='" + frame_title + "', style='Bold.TLabelframe')\n")
            file.write("\t\tcont_" + str(i) + ".grid(row=" + str(i) + ", column=0, padx=4, pady=4, sticky='we', columnspan=3)\n")
            file.write("\t\tcont_" + str(i) + ".columnconfigure(0, weight=1)\n")
            file.write("\t\tcont_" + str(i) + ".columnconfigure(1, weight=1)\n")
            file.write("\t\tcont_" + str(i) + ".columnconfigure(2, weight=1)\n")

        # For each return value found in model_data we check the data type.
        # Then the most appropriate widget is used.

        for index, row in aux_data[aux_data['IsAReturnValue']].iterrows():
            if not aux_data[aux_data['Name'] == row['BelongsTo']].empty:
                model_attr.append(index)
                if row['Type'] in ['int', 'float', 'bool', 'str', 'complex']:
                    is_a_password = any(sub_str in row['BelongsTo'].lower() for sub_str in ["password", "contrasena", "contrasenya"]) and row['Type'] == "str"
                    file.write("\t\tattr_desc_" + str(index) + " = ttk.Label(cont_" + str(i) + ", text='" + row['AttrDescription'] + "')\n")
                    file.write("\t\tattr_desc_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e')\n")
                    y += 1
                    file.write("\t\t")
                    if root == "self.root":
                        file.write("self.")
                    file.write("attr_" + str(index) + " = ttk.Label(cont_" + str(i) + ", text=")
                    if row['Type'] == "bool":
                        file.write("get_boolean_str(self." + init_aux_data['ArgumentName' + str(k + 1)] + "." + row['BelongsTo'] + "(), '" + main_data['LanguageID'].mode()[0] + "'), foreground=get_boolean_fg(self." + init_aux_data['ArgumentName' + str(k + 1)] +  "." + row['BelongsTo'] + "()), font=bold_font")
                    elif is_a_password:
                        file.write("'•' * len(self." + init_aux_data['ArgumentName' + str(k + 1)] + "." + row['BelongsTo'] + "())")
                    else:
                        file.write("self." + init_aux_data['ArgumentName' + str(k + 1)] + "." + row['BelongsTo'] + "()")
                    file.write(")\n")
                    file.write("\t\t")
                    if root == "self.root":
                        file.write("self.")
                    file.write("attr_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='w', columnspan=2)\n")
                    x += 1
                else:   # If data type is list, tuple, set or dict, Treeview is used as widget.
                    file.write("\t\t")
                    if root == "self.root":
                        file.write("self.")
                    file.write("attr_" + str(index) + " = ttk.Treeview(cont_" + str(i) + ", height=3)\n")
                    file.write("\t\t")
                    if root == "self.root":
                        file.write("self.")
                    file.write("attr_" + str(index) + ".heading('#0', text='" + row['AttrDescription'].replace(':', '') + "')\n")
                    file.write("\t\t")
                    if root == "self.root":
                        file.write("self.")
                    file.write("attr_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we', columnspan=3)\n")
                    file.write("\t\tset_treeview_items(")
                    if root == "self.root":
                        file.write("self.")
                    file.write("attr_" + str(index) + ", self." + init_aux_data['ArgumentName' + str(k + 1)] + "." + row['BelongsTo'] + "(), '" +main_data['LanguageID'].mode()[0] + "')\n")
                    x += 1
                y = 0
        k += 1
        i += 1
    return model_attr, i, x, y

def set_merged_arguments(file, main_data, controller, actual_view, i, x, y, root):
    """
    It sets the arguments that have been merged from the same Controller at the top of the window, checking that they
    belong to more than one method (BelongsTo).

    Param:

    - file (_io.TextIOWrapper): File input/output reference.
    - main_data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - controller (str): The name of the current Controller.
    - actual_view (int): Indicates the current View.
    - i (int): LabelFrame counter.
    - x (int): Grid X position.
    - y (int): Grid Y position.
    - root (str): Root name.

    Return:

    - i (int): LabelFrame counter.
    - x (int): Grid X position.
    - y (int): Grid Y position.
    """
    argument_data = main_data[main_data['IsAnArgument'] == True]
    argument_data = argument_data[argument_data['ClassName'] == controller]

    # For each merged argument, the corresponding widget is placed according to its label (Widget).

    for index, row in argument_data[argument_data['BelongsTo'].str.contains(',')].iterrows():
        if row['Widget'] == "Entry":
            is_a_password = any(sub_str in row['Name'].lower() for sub_str in ["password", "contrasena", "contrasenya"]) and row['Type'] == "str"
            file.write("\t\tdesc_" + str(index) + " = ttk.Label(" + root + ", text='" + row['WidgetDescription'] + "')\n")
            file.write("\t\tdesc_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e')\n")
            y += 1
            file.write("\t\twidget_" + str(index) + " = ttk.Entry(" + root)
            if is_a_password:
                file.write(", show='•'")
            else:
                file.write(", show=''")
            file.write(")\n")
            file.write("\t\twidget_" + str(index) + ".insert(0, '" + row['DefaultValue'] + "')\n")
            file.write("\t\twidget_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we'")
            if not is_a_password:
                file.write(", columnspan = 2)\n")
                x += 1
            else:
                file.write(")\n")
            if is_a_password:
                y += 1
                file.write("\n\t\tdef toggle_password_" + str(index) + "():\n")
                file.write("\t\t\tif widget_" + str(index) + ".cget('show') == '':\n")
                file.write("\t\t\t\twidget_" + str(index) + ".config(show='•')\n")
                file.write("\t\t\telse:\n")
                file.write("\t\t\t\twidget_" + str(index) + ".config(show='')\n\n")
                file.write("\t\tvar_" + str(index) + " = BooleanVar(value=False)\n")
                file.write("\t\tshow_hide_" + str(index) + " = ttk.Checkbutton(" + root + ", text='")
                match main_data['LanguageID'].mode()[0]:
                    case 'en':
                        file.write("Show password")
                    case 'es':
                        file.write("Mostrar contraseña")
                    case 'ca':
                        file.write("Mostrar contrasenya")
                file.write("', variable=var_" + str(index) + ", command=toggle_password_" + str(index) + ")\n")
                file.write("\t\tshow_hide_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='')\n")
                x += 1
        elif row['Widget'] == "Checkbutton":
            file.write("\t\tvar_" + str(index) + " = BooleanVar(")
            if row['DefaultValue'] != '':
                file.write("value=" + str(row['DefaultValue']))
            file.write(")\n")
            file.write("\t\twidget_" + str(index) + " = ttk.Checkbutton(" + root + ", text='" + row['WidgetLabel'] + "', variable=var_" + str(index) + ")\n")
            file.write("\t\twidget_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='', columnspan=3)\n")
            x += 1
        elif row['Widget'] == "Radiobutton":
            file.write("\t\tvar_" + str(index) + " = StringVar(")
            if row['DefaultValue'] != '':
                file.write("value='" + str(row['DefaultValue']) + "'")
            file.write(")\n")
            possible_values = row['PossibleValues'].split(',')
            file.write("\t\tdesc_" + str(index) + " = ttk.Label(" + root + ", text='" + row['WidgetDescription'] + "')\n")
            file.write("\t\tdesc_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e', rowspan=" +
                       str(len(possible_values)) + ")\n")
            y += 1
            for k in range(len(possible_values)):
                file.write("\t\twidget_" + str(index) + str(k) + " = ttk.Radiobutton(" + root + ", text='" + possible_values[k][0].upper() +
                           possible_values[k][1:] + "', variable=var_" + str(index) + ", value='" + possible_values[k] + "')\n")
                file.write("\t\twidget_" + str(index) + str(k) + ".grid(row=" + str(x) + ", column=" + str(y) +
                           ", padx=4, pady=4, sticky='we', columnspan=3)\n")
                x += 1
        elif row['Widget'] == "Scale":
            file.write("\t\tvar_" + str(index) + " = ")
            if row['Type'] == 'int':
                file.write("IntVar")
            else:
                file.write("DoubleVar")
            file.write("(")
            if row['DefaultValue'] != '':
                file.write("value=" + str(row['DefaultValue']))
            file.write(")\n\n")
            file.write("\t\tdef update_desc_" + str(index) + "(event):\n")
            file.write("\t\t\tdesc_" + str(index) + ".config(text='" + row['WidgetDescription'] + "\t' + ")
            if row['Type'] == 'int':
                file.write("str(var_" + str(index) + ".get())")
            else:
                file.write("f'{var_" + str(index) + ".get():.")
                if row['DefaultValue'] != '':
                    file.write(str(count_decimals(row['DefaultValue'])))
                else:
                    file.write("2")
                file.write("f}'")
            file.write(")\n\n")
            file.write("\t\tdesc_" + str(index) + " = ttk.Label(" + root + ", text='" + row['WidgetDescription'] + "\t' + ")
            if row['Type'] == 'int':
                file.write("str(var_" + str(index) + ".get())")
            else:
                file.write("f'{var_" + str(index) + ".get():.")
                if row['DefaultValue'] != '':
                    file.write(str(count_decimals(row['DefaultValue'])))
                else:
                    file.write("2")
                file.write("f}'")
            file.write(")\n")
            file.write("\t\tdesc_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e')\n")
            y += 1
            file.write("\t\twidget_" + str(index) + " = ttk.Scale(" + root + ", variable=var_" + str(index) + ", ")
            if row['Type'] == 'int':
                file.write("from_=" + str(int(row['From'])) + ", to=" + str(int(row['To'])))
            else:
                file.write("from_=" + str(row['From']) + ", to=" + str(row['To']))
            file.write(", command=update_desc_" + str(index) + ")\n")
            file.write("\t\twidget_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we', columnspan=3)\n")
            x += 1
        elif row['Widget'] == "Spinbox":
            file.write("\t\tvar_" + str(index) + " = ")
            if row['Type'] == 'int':
                file.write("IntVar")
            else:
                file.write("DoubleVar")
            file.write("(")
            if row['DefaultValue'] != '':
                file.write("value=" + str(row['DefaultValue']))
            file.write(")\n")
            file.write("\t\tdesc_" + str(index) + " = ttk.Label(" + root + ", text='" + row['WidgetDescription'] + "')\n")
            file.write("\t\tdesc_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e')\n")
            y += 1
            file.write("\t\twidget_" + str(index) + " = ttk.Spinbox(" + root + ", textvariable=var_" + str(index) + ", ")
            if row['Type'] == 'int':
                file.write("from_=" + str(int(row['From'])) + ", to=" + str(int(row['To'])) + ")\n")
            else:
                file.write("from_=" + str(row['From']) + ", to=" + str(row['To']) + ", increment=")
                if row['DefaultValue'] != '':
                    file.write(f"0.{'1'.rjust(count_decimals(row['DefaultValue']), '0')}")
                else:
                    file.write("0.01")
                file.write(")\n")
            file.write("\t\twidget_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we')\n")
            x += 1
        elif row['Widget'] == "Treeview":
            file.write("\n\t\tdef trigger_add_" + str(index) + "():\n")
            file.write("\t\t\tselected = widget_" + str(index) + ".selection()\n")
            file.write("\t\t\tif selected:\n")
            file.write("\t\t\t\tfor select in selected:\n")
            file.write("\t\t\t\t\tif widget_" + str(index) + ".item(select, 'text') == '<")
            match main_data['LanguageID'].mode()[0]:
                case 'en':
                    file.write("Empty")
                case 'es':
                    file.write("Vacío")
                case 'ca':
                    file.write("Buit")
            file.write(">':\n")
            file.write("\t\t\t\t\t\twidget_" + str(index) + ".item(select, text='[0]')\n")
            file.write("\t\t\t\t\telif widget_" + str(index) + ".item(select, 'text') == '[0]' or widget_" + str(index) +
                       ".item(select, 'text') == '[0..' + str(len(widget_" + str(index) + ".get_children(select)) - 1) + ']':\n")
            file.write("\t\t\t\t\t\twidget_" + str(index) + ".item(select, text='[0..' + str(len(widget_" + str(index) +
                       ".get_children(select))) + ']')\n")
            file.write("\t\t\t\t\tif var_" + str(index) + ".get() == '':\n")
            file.write("\t\t\t\t\t\twidget_" + str(index) + ".insert(select, 'end', text='<")
            match main_data['LanguageID'].mode()[0]:
                case 'en':
                    file.write("Empty")
                case 'es':
                    file.write("Vacío")
                case 'ca':
                    file.write("Buit")
            file.write(">')\n")
            file.write("\t\t\t\t\telse:\n")
            file.write("\t\t\t\t\t\tif 'complex' in str(type(convert_str(var_" + str(index) + ".get()))):\n")
            file.write("\t\t\t\t\t\t\twidget_" + str(index) + ".insert(select, 'end', text=str(convert_str(var_" + str(index) + ".get())))\n")
            file.write("\t\t\t\t\t\telse:\n")
            file.write("\t\t\t\t\t\t\twidget_" + str(index) + ".insert(select, 'end', text=var_" + str(index) + ".get())\n")
            file.write("\t\t\telse:\n")
            file.write("\t\t\t\tif var_" + str(index) + ".get() == '':\n")
            file.write("\t\t\t\t\twidget_" + str(index) + ".insert('', 'end', text='<")
            match main_data['LanguageID'].mode()[0]:
                case 'en':
                    file.write("Empty")
                case 'es':
                    file.write("Vacío")
                case 'ca':
                    file.write("Buit")
            file.write(">')\n")
            file.write("\t\t\t\telse:\n")
            file.write("\t\t\t\t\tif 'complex' in str(type(convert_str(var_" + str(index) + ".get()))):\n")
            file.write("\t\t\t\t\t\twidget_" + str(index) + ".insert('', 'end', text=str(convert_str(var_" + str(index) + ".get())))\n")
            file.write("\t\t\t\t\telse:\n")
            file.write("\t\t\t\t\t\twidget_" + str(index) + ".insert('', 'end', text=var_" + str(index) + ".get())\n")
            file.write("\n\t\tdef trigger_remove_" + str(index) + "():\n")
            file.write("\t\t\tselected = widget_" + str(index) + ".selection()\n")
            file.write("\t\t\tif selected:\n")
            file.write("\t\t\t\tparent_to_children = defaultdict(list)\n")
            file.write("\t\t\t\tfor item in selected:\n")
            file.write("\t\t\t\t\tparent = widget_" + str(index) + ".parent(item)\n")
            file.write("\t\t\t\t\tparent_to_children[parent].append(item)\n")
            file.write("\t\t\t\tfor items in parent_to_children.values():\n")
            file.write("\t\t\t\t\tfor item in items:\n")
            file.write("\t\t\t\t\t\tif widget_" + str(index) + ".exists(item):\n")
            file.write("\t\t\t\t\t\t\twidget_" + str(index) + ".delete(item)\n")
            file.write("\t\t\t\tpattern_array = re.compile(r'^\\[0(?:\\.\\.\\d+)?\\]$|^<")
            match main_data['LanguageID'].mode()[0]:
                case 'en':
                    file.write("Empty")
                case 'es':
                    file.write("Vacío")
                case 'ca':
                    file.write("Buit")
            file.write(">$')\n")
            file.write("\t\t\t\tfor parent in parent_to_children:\n")
            file.write("\t\t\t\t\tif widget_" + str(index) + ".exists(parent):\n")
            file.write("\t\t\t\t\t\tactual_item = widget_" + str(index) + ".item(parent, 'text')\n")
            file.write("\t\t\t\t\t\tif pattern_array.match(actual_item):\n")
            file.write("\t\t\t\t\t\t\tchildren = widget_" + str(index) + ".get_children(parent)\n")
            file.write("\t\t\t\t\t\t\tnum_children = len(children)\n")
            file.write("\t\t\t\t\t\t\tif num_children > 1:\n")
            file.write("\t\t\t\t\t\t\t\twidget_" + str(index) + ".item(parent, text=f'[0..{num_children - 1}]')\n")
            file.write("\t\t\t\t\t\t\telif num_children == 1:\n")
            file.write("\t\t\t\t\t\t\t\twidget_" + str(index) + ".item(parent, text='[0]')\n")
            file.write("\t\t\t\t\t\t\telse:\n")
            file.write("\t\t\t\t\t\t\t\twidget_" + str(index) + ".item(parent, text='<")
            match main_data['LanguageID'].mode()[0]:
                case 'en':
                    file.write("Empty")
                case 'es':
                    file.write("Vacío")
                case 'ca':
                    file.write("Buit")
            file.write(">')\n")
            file.write("\t\t\telse:\n")
            file.write("\t\t\t\t")
            if actual_view == 0:
                file.write("self")
            else:
                file.write("view")
            file.write(".message_box(" + root + ", 'warning', '")
            match main_data['LanguageID'].mode()[0]:
                case 'en':
                    file.write("No item has been selected.")
                case 'es':
                    file.write("No se ha seleccionado ningún elemento.")
                case 'ca':
                    file.write("No s\\'ha seleccionat cap element.")
            file.write("', '" + main_data['LanguageID'].mode()[0] + "')\n\n")
            file.write("\t\twidget_" + str(index) + " = ttk.Treeview(" + root + ", height=3)\n")
            file.write("\t\twidget_" + str(index) + ".heading('#0', text='" + row['WidgetLabel'] + "')\n")
            file.write("\t\twidget_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we', columnspan=2, rowspan=3)\n")
            y += 2
            file.write("\t\tvar_" + str(index) + " = ttk.Entry(" + root + ")\n")
            file.write("\t\tvar_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we')\n")
            x += 1
            file.write("\t\tadd_" + str(index) + " = ttk.Button(" + root + ", text='")
            match main_data['LanguageID'].mode()[0]:
                case 'en':
                    file.write("Add")
                case 'es':
                    file.write("Añadir")
                case 'ca':
                    file.write("Afegir")
            file.write("', command=lambda:trigger_add_" + str(index) + "(), width=12)\n")
            file.write("\t\tadd_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='')\n")
            x += 1
            file.write("\t\tremove_" + str(index) + " = ttk.Button(" + root + ", text='")
            match main_data['LanguageID'].mode()[0]:
                case 'en':
                    file.write("Remove")
                case 'es':
                    file.write("Eliminar")
                case 'ca':
                    file.write("Treure")
            file.write("', command=lambda:trigger_remove_" + str(index) + "(), width=12)\n")
            file.write("\t\tremove_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='')\n")
            x += 1
        elif row['Widget'] == "Combobox":
            possible_values = row['PossibleValues'].split(',')
            file.write("\t\tdesc_" + str(index) + " = ttk.Label(" + root + ", text='" + row['WidgetDescription'] + "')\n")
            file.write("\t\tdesc_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e')\n")
            y += 1
            file.write("\t\twidget_" + str(index) + " = ttk.Combobox(" + root + ", values=['")
            for k in range(len(possible_values)):
                file.write(possible_values[k])
                if k < len(possible_values) - 1:
                    file.write("', '")
            file.write("'])\n")
            file.write("\t\twidget_" + str(index) + ".set('" + row['DefaultValue'] + "')\n")
            file.write("\t\twidget_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we', columnspan=2)\n")
            x += 1
        y = 0
    return i, x, y

def create_widgets(file, main_data, model_data, main_controller_name, model_attr, actual_view, x, y, root, tabulation, it_destroys, allow_button):
    """
    Creates the main body of the window, assigning each widget to arguments, methods, and return values (in that order)
    for each method defined in a specific Controller.

    Param:

    - file (_io.TextIOWrapper): File input/output reference.
    - main_data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - model_data (pandas.core.frame.DataFrame): Model data from the test dataset.
    - main_controller_name (str): The name of the main Controller.
    - model_attr (list): List of indexs from Model attribute getters.
    - actual_view (int): Indicates the current View.
    - x (int): Grid X position.
    - y (int): Grid Y position.
    - root (str): Root name.
    - tabulation (str): Tabulation of the written code.
    - it_destroys (bool): Indicates whether the window where the method is called is destroyed.
    - allow_button (bool): Indicates whether the button that allows calling the method appears or not.

    Return:

    - x (int): Grid X position.
    - y (int): Grid Y position.
    """
    argument_data = main_data[main_data['IsAnArgument'] == True]
    return_value_data = main_data[main_data['IsAReturnValue'] == True]

    # For each method, set the configuration of the arguments, the button that starts it, and the return values
    # corresponding to the current window.

    for index, row in main_data[main_data['IsAMethod'] == True].iterrows():
        aux_x = x   # Save the X row position at the beginning.
        aux_row = aux_x # Used when a Treeview is displayed.
        aux_rowspan = -1 # Rows that the widget (Button) will occupy.

        # For each argument, the corresponding widget is placed according to its label (Widget).

        for index_arg, row_arg in argument_data[argument_data['BelongsTo'] == row['Name']].iterrows():
            if row_arg['Widget'] == "Entry":
                is_a_password = any(sub_str in row_arg['Name'].lower() for sub_str in ["password", "contrasena", "contrasenya"]) and row_arg['Type'] == "str"
                file.write(tabulation + "desc_" + str(index_arg) + " = ttk.Label(" + root + ", text='" + row_arg['WidgetDescription'] + "')\n")
                file.write(tabulation + "desc_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e')\n")
                y += 1
                file.write(tabulation + "widget_" + str(index_arg) + " = ttk.Entry(" + root)
                if is_a_password:
                    file.write(", show='•'")
                else:
                    file.write(", show=''")
                file.write(")\n")
                file.write(tabulation + "widget_" + str(index_arg) + ".insert(0, '" + row_arg['DefaultValue'] + "')\n")
                file.write(tabulation + "widget_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we'")
                if tabulation != "\t\t" and not allow_button:
                    file.write(", columnspan=2")
                file.write(")\n")
                x += 1
                if is_a_password:
                    file.write("\n" + tabulation + "def toggle_password_" + str(index_arg) + "():\n")
                    file.write(tabulation + "\tif widget_" + str(index_arg) + ".cget('show') == '':\n")
                    file.write(tabulation + "\t\twidget_" + str(index_arg) + ".config(show='•')\n")
                    file.write(tabulation + "\telse:\n")
                    file.write(tabulation + "\t\twidget_" + str(index_arg) + ".config(show='')\n\n")
                    file.write(tabulation + "var_" + str(index_arg) + " = BooleanVar(value=False)\n")
                    file.write(tabulation + "show_hide_" + str(index_arg) + " = ttk.Checkbutton(" + root + ", text='")
                    match main_data['LanguageID'].mode()[0]:
                        case 'en':
                            file.write("Show password")
                        case 'es':
                            file.write("Mostrar contraseña")
                        case 'ca':
                            file.write("Mostrar contrasenya")
                    file.write("', variable=var_" + str(index_arg) + ", command=toggle_password_" + str(index_arg) + ")\n")
                    file.write(tabulation + "show_hide_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky=''")
                    if tabulation != "\t\t" and not allow_button:
                        file.write(", columnspan=2")
                    file.write(")\n")
                    x += 1
            elif row_arg['Widget'] == "Checkbutton":
                file.write(tabulation + "var_" + str(index_arg) + " = BooleanVar(")
                if row_arg['DefaultValue'] != '':
                    file.write("value=" + str(row_arg['DefaultValue']))
                file.write(")\n")
                file.write(tabulation + "widget_" + str(index_arg) + " = ttk.Checkbutton(" + root + ", text='" + row_arg['WidgetLabel'] +
                           "', variable=var_" + str(index_arg) + ")\n")
                file.write(tabulation + "widget_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky=''")
                if tabulation != "\t\t" and not allow_button:
                    file.write(", columnspan=3")
                else:
                    file.write(", columnspan=2")
                file.write(")\n")
                x += 1
            elif row_arg['Widget'] == "Radiobutton":
                file.write(tabulation + "var_" + str(index_arg) + " = StringVar(")
                if row_arg['DefaultValue'] != '':
                    file.write("value='" + str(row_arg['DefaultValue']) + "'")
                file.write(")\n")
                possible_values = row_arg['PossibleValues'].split(',')
                file.write(tabulation + "desc_" + str(index_arg) + " = ttk.Label(" + root + ", text='" + row_arg['WidgetDescription'] + "')\n")
                file.write(tabulation + "desc_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) +
                           ", padx=4, pady=4, sticky='e', rowspan=" + str(len(possible_values)) + ")\n")
                y += 1
                for k in range(len(possible_values)):
                    file.write(tabulation + "widget_" + str(index_arg) + str(k) + " = ttk.Radiobutton(" + root + ", text='" +
                               possible_values[k][0].upper() + possible_values[k][1:] + "', variable=var_" + str(index_arg) + ", value='"
                               + possible_values[k] + "')\n")
                    file.write(tabulation + "widget_" + str(index_arg) + str(k) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we'")
                    if tabulation != "\t\t" and not allow_button:
                        file.write(", columnspan=2")
                    file.write(")\n")
                    x += 1
            elif row_arg['Widget'] == "Scale":
                file.write(tabulation + "var_" + str(index_arg) + " = ")
                if row_arg['Type'] == 'int':
                    file.write("IntVar")
                else:
                    file.write("DoubleVar")
                file.write("(")
                if row_arg['DefaultValue'] != '':
                    file.write("value=" + str(row_arg['DefaultValue']))
                file.write(")\n\n")
                file.write(tabulation + "def update_desc_" + str(index_arg) + "(event):\n")
                file.write(tabulation + "\tdesc_" + str(index_arg) + ".config(text='" + row_arg['WidgetDescription'] + "\t' + ")
                if row_arg['Type'] == 'int':
                    file.write("str(var_" + str(index_arg) + ".get())")
                else:
                    file.write("f'{var_" + str(index_arg) + ".get():.")
                    if row_arg['DefaultValue'] != '':
                        file.write(str(count_decimals(row_arg['DefaultValue'])))
                    else:
                        file.write("2")
                    file.write("f}'")
                file.write(")\n\n")
                file.write(tabulation + "desc_" + str(index_arg) + " = ttk.Label(" + root + ", text='" + row_arg['WidgetDescription'] + "\t' + ")
                if row_arg['Type'] == 'int':
                    file.write("str(var_" + str(index_arg) + ".get())")
                else:
                    file.write("f'{var_" + str(index_arg) + ".get():.")
                    if row_arg['DefaultValue'] != '':
                        file.write(str(count_decimals(row_arg['DefaultValue'])))
                    else:
                        file.write("2")
                    file.write("f}'")
                file.write(")\n")
                file.write(tabulation + "desc_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e')\n")
                y += 1
                file.write(tabulation + "widget_" + str(index_arg) + " = ttk.Scale(" + root + ", variable=var_" + str(index_arg) + ", ")
                if row_arg['Type'] == 'int':
                    file.write("from_=" + str(int(row_arg['From'])) + ", to=" + str(int(row_arg['To'])))
                else:
                    file.write("from_=" + str(row_arg['From']) + ", to=" + str(row_arg['To']))
                file.write(", command=update_desc_" + str(index_arg) + ")\n")
                file.write(tabulation + "widget_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we'")
                if tabulation != "\t\t" and not allow_button:
                    file.write(", columnspan=2")
                file.write(")\n")
                x += 1
            elif row_arg['Widget'] == "Spinbox":
                file.write(tabulation + "var_" + str(index_arg) + " = ")
                if row_arg['Type'] == 'int':
                    file.write("IntVar")
                else:
                    file.write("DoubleVar")
                file.write("(")
                if row_arg['DefaultValue'] != '':
                    file.write("value=" + str(row_arg['DefaultValue']))
                file.write(")\n")
                file.write(tabulation + "desc_" + str(index_arg) + " = ttk.Label(" + root + ", text='" + row_arg['WidgetDescription'] + "')\n")
                file.write(tabulation + "desc_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e')\n")
                y += 1
                file.write(tabulation + "widget_" + str(index_arg) + " = ttk.Spinbox(" + root + ", textvariable=var_" + str(index_arg) + ", ")
                if row_arg['Type'] == 'int':
                    file.write("from_=" + str(int(row_arg['From'])) + ", to=" + str(int(row_arg['To'])) + ")\n")
                else:
                    file.write("from_=" + str(row_arg['From']) + ", to=" + str(row_arg['To']) + ", increment=")
                    if row_arg['DefaultValue'] != '':
                        file.write(f"0.{'1'.rjust(count_decimals(row_arg['DefaultValue']), '0')}")
                    else:
                        file.write("0.01")
                    file.write(")\n")
                file.write(tabulation + "widget_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we')\n")
                x += 1
            elif row_arg['Widget'] == "Treeview":
                aux_row = aux_x
                aux_rowspan = x - aux_x
                file.write("\n" + tabulation + "def trigger_add_" + str(index_arg) + "():\n")
                file.write(tabulation + "\tselected = widget_" + str(index_arg) + ".selection()\n")
                file.write(tabulation + "\tif selected:\n")
                file.write(tabulation + "\t\tfor select in selected:\n")
                file.write(tabulation + "\t\t\tif widget_" + str(index_arg) + ".item(select, 'text') == '<")
                match main_data['LanguageID'].mode()[0]:
                    case 'en':
                        file.write("Empty")
                    case 'es':
                        file.write("Vacío")
                    case 'ca':
                        file.write("Buit")
                file.write(">':\n")
                file.write(tabulation + "\t\t\t\twidget_" + str(index_arg) + ".item(select, text='[0]')\n")
                file.write(tabulation + "\t\t\telif widget_" + str(index_arg) + ".item(select, 'text') == '[0]' or widget_" +
                           str(index_arg) + ".item(select, 'text') == '[0..' + str(len(widget_" + str(index_arg) +
                           ".get_children(select)) - 1) + ']':\n")
                file.write(tabulation + "\t\t\t\twidget_" + str(index_arg) + ".item(select, text='[0..' + str(len(widget_" +
                           str(index_arg) + ".get_children(select))) + ']')\n")
                file.write(tabulation + "\t\t\tif var_" + str(index_arg) + ".get() == '':\n")
                file.write(tabulation + "\t\t\t\twidget_" + str(index_arg) + ".insert(select, 'end', text='<")
                match main_data['LanguageID'].mode()[0]:
                    case 'en':
                        file.write("Empty")
                    case 'es':
                        file.write("Vacío")
                    case 'ca':
                        file.write("Buit")
                file.write(">')\n")
                file.write(tabulation + "\t\t\telse:\n")
                file.write(tabulation + "\t\t\t\tif 'complex' in str(type(convert_str(var_" + str(index_arg) + ".get()))):\n")
                file.write(tabulation + "\t\t\t\t\twidget_" + str(index_arg) + ".insert(select, 'end', text=str(convert_str(var_" +
                           str(index_arg) + ".get())))\n")
                file.write(tabulation + "\t\t\t\telse:\n")
                file.write(tabulation + "\t\t\t\t\twidget_" + str(index_arg) + ".insert(select, 'end', text=var_" + str(index_arg) + ".get())\n")
                file.write(tabulation + "\telse:\n")
                file.write(tabulation + "\t\tif var_" + str(index_arg) + ".get() == '':\n")
                file.write(tabulation + "\t\t\twidget_" + str(index_arg) + ".insert('', 'end', text='<")
                match main_data['LanguageID'].mode()[0]:
                    case 'en':
                        file.write("Empty")
                    case 'es':
                        file.write("Vacío")
                    case 'ca':
                        file.write("Buit")
                file.write(">')\n")
                file.write(tabulation + "\t\telse:\n")
                file.write(tabulation + "\t\t\tif 'complex' in str(type(convert_str(var_" + str(index_arg) + ".get()))):\n")
                file.write(tabulation + "\t\t\t\twidget_" + str(index_arg) + ".insert('', 'end', text=str(convert_str(var_" + str(index_arg) + ".get())))\n")
                file.write(tabulation + "\t\t\telse:\n")
                file.write(tabulation + "\t\t\t\twidget_" + str(index_arg) + ".insert('', 'end', text=var_" + str(index_arg) + ".get())\n")
                file.write("\n" + tabulation + "def trigger_remove_" + str(index_arg) + "():\n")
                file.write(tabulation + "\tselected = widget_" + str(index_arg) + ".selection()\n")
                file.write(tabulation + "\tif selected:\n")
                file.write(tabulation + "\t\tparent_to_children = defaultdict(list)\n")
                file.write(tabulation + "\t\tfor item in selected:\n")
                file.write(tabulation + "\t\t\tparent = widget_" + str(index_arg) + ".parent(item)\n")
                file.write(tabulation + "\t\t\tparent_to_children[parent].append(item)\n")
                file.write(tabulation + "\t\tfor items in parent_to_children.values():\n")
                file.write(tabulation + "\t\t\tfor item in items:\n")
                file.write(tabulation + "\t\t\t\tif widget_" + str(index_arg) + ".exists(item):\n")
                file.write(tabulation + "\t\t\t\t\twidget_" + str(index_arg) + ".delete(item)\n")
                file.write(tabulation + "\t\tpattern_array = re.compile(r'^\\[0(?:\\.\\.\\d+)?\\]$|^<")
                match main_data['LanguageID'].mode()[0]:
                    case 'en':
                        file.write("Empty")
                    case 'es':
                        file.write("Vacío")
                    case 'ca':
                        file.write("Buit")
                file.write(">$')\n")
                file.write(tabulation + "\t\tfor parent in parent_to_children:\n")
                file.write(tabulation + "\t\t\tif widget_" + str(index_arg) + ".exists(parent):\n")
                file.write(tabulation + "\t\t\t\tactual_item = widget_" + str(index_arg) + ".item(parent, 'text')\n")
                file.write(tabulation + "\t\t\t\tif pattern_array.match(actual_item):\n")
                file.write(tabulation + "\t\t\t\t\tchildren = widget_" + str(index_arg) + ".get_children(parent)\n")
                file.write(tabulation + "\t\t\t\t\tnum_children = len(children)\n")
                file.write(tabulation + "\t\t\t\t\tif num_children > 1:\n")
                file.write(tabulation + "\t\t\t\t\t\twidget_" + str(index_arg) + ".item(parent, text=f'[0..{num_children - 1}]')\n")
                file.write(tabulation + "\t\t\t\t\telif num_children == 1:\n")
                file.write(tabulation + "\t\t\t\t\t\twidget_" + str(index_arg) + ".item(parent, text='[0]')\n")
                file.write(tabulation + "\t\t\t\t\telse:\n")
                file.write(tabulation + "\t\t\t\t\t\twidget_" + str(index_arg) + ".item(parent, text='<")
                match main_data['LanguageID'].mode()[0]:
                    case 'en':
                        file.write("Empty")
                    case 'es':
                        file.write("Vacío")
                    case 'ca':
                        file.write("Buit")
                file.write(">')\n")
                file.write(tabulation + "\telse:\n")
                file.write(tabulation + "\t\t")
                if actual_view == 0:
                    file.write("self")
                else:
                    file.write("view")
                file.write(".message_box(" + root + ", 'warning', ")
                match main_data['LanguageID'].mode()[0]:
                    case 'en':
                        file.write("'No item has been selected.'")
                    case 'es':
                        file.write("'No se ha seleccionado ningún elemento.'")
                    case 'ca':
                        file.write("'No s\\'ha seleccionat cap element.'")
                file.write(", '" + main_data['LanguageID'].mode()[0] + "')\n\n")
                file.write(tabulation + "widget_" + str(index_arg) + " = ttk.Treeview(" + root + ", height=3)\n")
                file.write(tabulation + "widget_" + str(index_arg) + ".heading('#0', text='" + row_arg['WidgetLabel'] + "')\n")
                file.write(tabulation + "widget_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) +
                           ", padx=4, pady=4, sticky='we', columnspan=2, rowspan=3)\n")
                y += 2
                file.write(tabulation + "var_" + str(index_arg) + " = ttk.Entry(" + root + ")\n")
                file.write(tabulation + "var_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we')\n")
                x += 1
                file.write(tabulation + "add_" + str(index_arg) + " = ttk.Button(" + root + ", text='")
                match main_data['LanguageID'].mode()[0]:
                    case 'en':
                        file.write("Add")
                    case 'es':
                        file.write("Añadir")
                    case 'ca':
                        file.write("Afegir")
                file.write("', command=lambda:trigger_add_" + str(index_arg) + "(), width=12)\n")
                file.write(tabulation + "add_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='')\n")
                x += 1
                file.write(tabulation + "remove_" + str(index_arg) + " = ttk.Button(" + root + ", text='")
                match main_data['LanguageID'].mode()[0]:
                    case 'en':
                        file.write("Remove")
                    case 'es':
                        file.write("Eliminar")
                    case 'ca':
                        file.write("Treure")
                file.write("', command=lambda:trigger_remove_" + str(index_arg) + "(), width=12)\n")
                file.write(tabulation + "remove_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='')\n")
                x += 1
                aux_x = x
            elif row_arg['Widget'] == "Combobox":
                possible_values = row_arg['PossibleValues'].split(',')
                file.write(tabulation + "desc_" + str(index_arg) + " = ttk.Label(" + root + ", text='" + row_arg['WidgetDescription'] + "')\n")
                file.write(tabulation + "desc_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e')\n")
                y += 1
                file.write(tabulation + "widget_" + str(index_arg) + " = ttk.Combobox(" + root + ", values=['")
                for k in range(len(possible_values)):
                    file.write(possible_values[k])
                    if k < len(possible_values) - 1:
                        file.write("', '")
                file.write("'])\n")
                file.write(tabulation + "widget_" + str(index_arg) + ".set('" + row_arg['DefaultValue'] + "')\n")
                file.write(tabulation + "widget_" + str(index_arg) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we'")
                if tabulation != "\t\t" and not allow_button:
                    file.write(", columnspan=2")
                file.write(")\n")
                x += 1
            y = 0

        # Writes the code for the function that calls a method of the Controller.

        file.write("\n" + tabulation + "def trigger_button_" + str(index) + "():\n")
        k = 0
        arguments = []
        mask = argument_data['BelongsTo'].apply(
            lambda z: row['Name'] in [item.strip() for item in z.split(',')]
        )

        # Saves the argument indices needed to call the method.

        aux_data = argument_data[mask]
        while row['ArgumentName' + str(k + 1)] != '' and k < 10:
            arguments.append(aux_data[aux_data['Name'] == row['ArgumentName' + str(k + 1)]].index.tolist()[0])
            k += 1
        if arguments:   # If it has arguments, checks that they fulfill the restrictions (written code).
            for k in range(len(arguments)):
                if main_data.loc[arguments[k], 'Type'] in ['int', 'float'] and argument_data.loc[arguments[k]]['Widget'] == "Spinbox":
                    file.write(tabulation + "\ttry:\n")
                    file.write(tabulation + "\t\tif not " + str(main_data.loc[arguments[k], 'From']) + " <= var_" + str(arguments[k]) +
                               ".get() <= " + str(main_data.loc[arguments[k], 'To']) + ":\n")
                    file.write(tabulation + "\t\t\t")
                    if actual_view == 0:
                        file.write("self")
                    else:
                        file.write("view")
                    file.write(".message_box(" + root + ", 'warning', '")
                    match main_data['LanguageID'].mode()[0]:
                        case 'en':
                            file.write("The value must be between " + str(main_data.loc[arguments[k], 'From']) + " and "
                                       + str(main_data.loc[arguments[k], 'To']) + ".")
                        case 'es':
                            file.write("El valor debe estar entre " + str(main_data.loc[arguments[k], 'From']) + " y "
                                       + str(main_data.loc[arguments[k], 'To']) + ".")
                        case 'ca':
                            file.write("El valor ha d\\'estar entre " + str(main_data.loc[arguments[k], 'From']) + " i "
                                       + str(main_data.loc[arguments[k], 'To']) + ".")
                    file.write("', '" + main_data['LanguageID'].mode()[0] + "')\n")
                    file.write(tabulation + "\t\t\treturn\n")
                    file.write(tabulation + "\texcept Exception as e:\n")
                    file.write(tabulation + "\t\t")
                    if actual_view == 0:
                        file.write("self")
                    else:
                        file.write("view")
                    file.write(".message_box(" + root + ", 'error', '")
                    match main_data['LanguageID'].mode()[0]:
                        case 'en':
                            file.write("Invalid value.")
                        case 'es':
                            file.write("Valor inválido.")
                        case 'ca':
                            file.write("Valor no vàlid.")
                    file.write("', '" + main_data['LanguageID'].mode()[0] + "')\n" + tabulation + "\t\treturn\n")
                elif main_data.loc[arguments[k], 'Type'] == "str":
                    if argument_data.loc[arguments[k]]['Widget'] == "Combobox":
                        file.write(tabulation + "\tif widget_" + str(arguments[k]) + ".get() not in widget_" + str(arguments[k]) + ".cget('values'):\n")
                        file.write(tabulation + "\t\t")
                        if actual_view == 0:
                            file.write("self")
                        else:
                            file.write("view")
                        file.write(".message_box(" + root + ", 'error', '")
                        match main_data['LanguageID'].mode()[0]:
                            case 'en':
                                file.write("Invalid value.")
                            case 'es':
                                file.write("Valor inválido.")
                            case 'ca':
                                file.write("Valor no vàlid.")
                        file.write("', '" + main_data['LanguageID'].mode()[0] + "')\n" + tabulation + "\t\treturn\n")
                    elif argument_data.loc[arguments[k]]['Widget'] == "Radiobutton":
                        file.write(tabulation + "\tif var_" + str(arguments[k]) + ".get() not in " +
                                   str(argument_data.loc[arguments[k]]['PossibleValues'].split(',')) + ":\n")
                        file.write(tabulation + "\t\t")
                        if actual_view == 0:
                            file.write("self")
                        else:
                            file.write("view")
                        file.write(".message_box(" + root + ", 'error', '")
                        match main_data['LanguageID'].mode()[0]:
                            case 'en':
                                file.write("Invalid value.")
                            case 'es':
                                file.write("Valor inválido.")
                            case 'ca':
                                file.write("Valor no vàlid.")
                        file.write("', '" + main_data['LanguageID'].mode()[0] + "')\n" + tabulation + "\t\treturn\n")
                    elif argument_data.loc[arguments[k]]['Widget'] == "Entry" and any(sub_str in argument_data.loc[arguments[k]]['Name'].lower() for sub_str in ["password", "contrasena", "contrasenya"]):
                        file.write(tabulation + "\tcapital_" + str(arguments[k]) + " = re.search(r'[A-Z]', widget_" + str(arguments[k]) + ".get())\n")
                        file.write(tabulation + "\tlowercase_" + str(arguments[k]) + " = re.search(r'[a-z]', widget_" + str(arguments[k]) + ".get())\n")
                        file.write(tabulation + "\tnumber_" + str(arguments[k]) + " = re.search(r'\\d', widget_" + str(arguments[k]) + ".get())\n")
                        file.write(tabulation + "\tsymbol_" + str(arguments[k]) + " = re.search(r'[^A-Za-z0-9]', widget_" + str(arguments[k]) + ".get())\n")
                        file.write(tabulation + "\tif len(widget_" + str(arguments[k]) + ".get()) < 14 or not all([capital_" + str(arguments[k]) +
                                   ", lowercase_" + str(arguments[k]) + ", number_" + str(arguments[k]) + ", symbol_" + str(arguments[k]) + "]):\n")
                        file.write(tabulation + "\t\tmessage_" + str(arguments[k]) + " = '")
                        match main_data['LanguageID'].mode()[0]:
                            case 'en':
                                file.write("The password must meet the following requirements:\\n")
                            case 'es':
                                file.write("La contraseña debe cumplir con los siguientes requisitos:\\n")
                            case 'ca':
                                file.write("La contrasenya ha de complir els requisits següents:\\n")
                        file.write("'\n")
                        file.write(tabulation + "\t\tif len(widget_" + str(arguments[k]) + ".get()) < 14:\n")
                        file.write(tabulation + "\t\t\tmessage_" + str(arguments[k]) + " += '\\n- ")
                        match main_data['LanguageID'].mode()[0]:
                            case 'en':
                                file.write("Must be at least 14 characters.")
                            case 'es':
                                file.write("Debe tener al menos 14 carácteres.")
                            case 'ca':
                                file.write("Ha de tenir com a mínim 14 caràcters.")
                        file.write("'\n")
                        file.write(tabulation + "\t\tif not re.search(r'[A-Z]', widget_" + str(arguments[k]) + ".get()):\n")
                        file.write(tabulation + "\t\t\tmessage_" + str(arguments[k]) + " += '\\n- ")
                        match main_data['LanguageID'].mode()[0]:
                            case 'en':
                                file.write("Must include at least one capital letter.")
                            case 'es':
                                file.write("Debe incluir al menos una letra mayúscula.")
                            case 'ca':
                                file.write("Ha d\\'incloure com a mínim una lletra majúscula.")
                        file.write("'\n")
                        file.write(tabulation + "\t\tif not re.search(r'[a-z]', widget_" + str(arguments[k]) + ".get()):\n")
                        file.write(tabulation + "\t\t\tmessage_" + str(arguments[k]) + " += '\\n- ")
                        match main_data['LanguageID'].mode()[0]:
                            case 'en':
                                file.write("Must include at least one lowercase letter.")
                            case 'es':
                                file.write("Debe incluir al menos una letra minúscula.")
                            case 'ca':
                                file.write("Ha d\\'incloure com a mínim una lletra minúscula.")
                        file.write("'\n")
                        file.write(tabulation + "\t\tif not re.search(r'\\d', widget_" + str(arguments[k]) + ".get()):\n")
                        file.write(tabulation + "\t\t\tmessage_" + str(arguments[k]) + " += '\\n- ")
                        match main_data['LanguageID'].mode()[0]:
                            case 'en':
                                file.write("Must include at least one number.")
                            case 'es':
                                file.write("Debe incluir al menos un número.")
                            case 'ca':
                                file.write("Ha d\\'incloure com a mínim un nombre.")
                        file.write("'\n")
                        file.write(tabulation + "\t\tif not re.search(r'[^A-Za-z0-9]', widget_" + str(arguments[k]) + ".get()):\n")
                        file.write(tabulation + "\t\t\tmessage_" + str(arguments[k]) + " += '\\n- ")
                        match main_data['LanguageID'].mode()[0]:
                            case 'en':
                                file.write("Must include at least one symbol.")
                            case 'es':
                                file.write("Debe incluir al menos un símbolo.")
                            case 'ca':
                                file.write("Ha d\\'incloure com a mínim un símbol.")
                        file.write("'\n")
                        file.write(tabulation + "\t\t")
                        if actual_view == 0:
                            file.write("self")
                        else:
                            file.write("view")
                        file.write(".message_box(" + root + ", 'warning', message_" + str(arguments[k]) + ", '" +
                                   main_data['LanguageID'].mode()[0] + "')\n" + tabulation + "\t\treturn\n")
                elif main_data.loc[arguments[k], 'Type'] == "complex" and argument_data.loc[arguments[k]]['Widget'] == "Entry":
                    file.write(tabulation + "\tif 'complex' not in str(type(convert_str(widget_" + str(arguments[k]) + ".get()))):\n")
                    file.write(tabulation + "\t\t")
                    if actual_view == 0:
                        file.write("self")
                    else:
                        file.write("view")
                    file.write(".message_box(" + root + ", 'error', '")
                    match main_data['LanguageID'].mode()[0]:
                        case 'en':
                            file.write("Invalid value.")
                        case 'es':
                            file.write("Valor inválido.")
                        case 'ca':
                            file.write("Valor no vàlid.")
                    file.write("', '" + main_data['LanguageID'].mode()[0] + "')\n" + tabulation + "\t\treturn\n")
        file.write(tabulation + "\t")
        k = 0
        return_values = []
        mask = return_value_data['BelongsTo'].apply(
            lambda z: row['Name'] in [item.strip() for item in z.split(',')]
        )

        # Saves the return value indices needed to call the method.

        aux_data = return_value_data[mask]
        while row['ReturnValueName' + str(k + 1)] != '' and k < 10:
            return_values.append(aux_data[aux_data['Name'] == row['ReturnValueName' + str(k + 1)]].index.tolist()[0])
            k += 1
        if return_values:   # The return variables are written first.
            for k in range(len(return_values)):
                file.write("ret_" + str(return_values[k]))
                if k < len(return_values) - 1:
                    file.write(", ")
            file.write(" = ")

        # Calls the Controller method.

        file.write("self." + convert_to_camel_case(row['ClassName']).lower().replace(' ', '_') + "." + row['Name'] + "(")

        # Then the arguments are written (depending on the widget type these will have to access the value as necessary).

        if arguments:
            for k in range(len(arguments)):
                if argument_data.loc[arguments[k]]['Widget'] in ['Entry', 'Combobox']:
                    if argument_data.loc[arguments[k]]['Type'] == "complex":
                        file.write("complex(widget_" + str(arguments[k]) + ".get())")
                    else:
                        file.write("widget_" + str(arguments[k]) + ".get()")
                elif argument_data.loc[arguments[k]]['Widget'] in ['Checkbutton', 'Radiobutton', 'Scale', 'Spinbox']:
                    file.write("var_" + str(arguments[k]) + ".get()")
                elif argument_data.loc[arguments[k]]['Widget'] == "Treeview":
                    file.write("get_treeview_items(widget_" + str(arguments[k]) + ", '" + argument_data.loc[arguments[k]]['Type'] + "')")
                if k < len(arguments) - 1:
                    file.write(", ")
        file.write(")\n")
        if not argument_data[argument_data['BelongsTo'] == row['Name']].empty and not return_value_data[return_value_data['BelongsTo'] == row['Name']].empty:
            x -= 1
        if return_values:   # Assign the return values to the corresponding widgets.
            for return_value in return_values:
                if return_value_data.loc[return_value]['Widget'] == "Label":
                    if return_value_data.loc[return_value]['Type'] == "bool":
                        file.write(tabulation + "\twidget_" + str(return_value) + ".config(text=get_boolean_str(ret_" +
                                   str(return_value) + ", '" + main_data['LanguageID'].mode()[0] +
                                   "'), foreground=get_boolean_fg(ret_" + str(return_value) + "))\n")
                    else:
                        file.write(tabulation + "\twidget_" + str(return_value) + ".config(text=ret_" + str(return_value) + ")\n")
                elif return_value_data.loc[return_value]['Widget'] == "Entry":
                    file.write(tabulation + "\twidget_" + str(return_value) + ".config(state='normal')\n")
                    file.write(tabulation + "\twidget_" + str(return_value) + ".delete(0, END)\n")
                    file.write(tabulation + "\twidget_" + str(return_value) + ".insert(0, ret_" + str(return_value) + ")\n")
                    file.write(tabulation + "\twidget_" + str(return_value) + ".config(state='readonly')\n")
                elif return_value_data.loc[return_value]['Widget'] == "Treeview":
                    file.write(tabulation + "\tset_treeview_items(widget_" + str(return_value) + ", ret_" + str(return_value)
                               + ", '" + main_data['LanguageID'].mode()[0] + "')\n")

        # If it is not a method of the main Controller, it updates the contents of the Models each time it is called.

        if actual_view != 0:
            for attr in model_attr:
                if model_data.loc[attr]['Type'] in ['int', 'float', 'bool', 'str', 'complex']:
                    file.write(tabulation + "\tattr_" + str(attr) + ".config(text=")
                    if model_data.loc[attr]['Type'] == "bool":
                        file.write("get_boolean_str(self." + model_data.loc[attr]['ModelName'] + "." +
                                   model_data.loc[attr]['BelongsTo'] + "(), '" + main_data['LanguageID'].mode()[0] +
                                   "'), foreground=get_boolean_fg(self." + model_data.loc[attr]['UsedByController'] +
                                   "." + model_data.loc[attr]['BelongsTo'] + "()), font=bold_font")
                    else:
                        file.write("self." + model_data.loc[attr]['ModelName'] + "." + model_data.loc[attr]['BelongsTo'] + "()")
                    file.write(")\n")
                else:
                    file.write(tabulation + "\tset_treeview_items(attr_" + str(attr) + ", self." +
                               model_data.loc[attr]['ModelName'] + "." + model_data.loc[attr]['BelongsTo'] + "(), '" +
                               main_data['LanguageID'].mode()[0] + "')\n")
        aux_data = model_data[model_data['UsedByController'] == main_controller_name]
        aux_data = aux_data[aux_data['IsAMethod'] == True]
        if not aux_data[aux_data['Type'] != 'None'].empty:

            # Updates the content of the models belonging to the main Controller.

            file.write(tabulation + "\t")
            if actual_view != 0:
                file.write("view")
            else:
                file.write("self")
            file.write(".update()\n")
        if tabulation != "\t\t":
            if it_destroys: # If True the current window is destroyed.
                file.write(tabulation + "\t" + root + ".destroy()\n")
            elif not it_destroys and not arguments:
                file.write("\n")
        if allow_button:    # If True the trigger button will appear on the right.
            file.write("\n" + tabulation + "widget_" + str(index) + " = ttk.Button(" + root + ", text='" +
                       row['WidgetLabel'] + "', command=lambda:trigger_button_" + str(index) + "())\n")
            if not argument_data[argument_data['BelongsTo'] == row['Name']].empty:
                if len(arguments) == 1 and argument_data.loc[arguments[0]]['Widget'] == "Treeview":
                    file.write(tabulation + "widget_" + str(index) + ".grid(row=" + str(x) + ", column=0, padx=4, pady=4, sticky='', columnspan=3)\n")
                else:
                    if aux_rowspan == -1 or argument_data.loc[arguments[-1]]['Widget'] != "Treeview":
                        aux_row = aux_x
                        aux_rowspan = x - aux_x + 1
                    file.write(tabulation + "widget_" + str(index) + ".grid(row=" + str(aux_row) + ", column=2, padx=4, pady=4, sticky=''")
                    if len(arguments) > 1 or aux_rowspan > 1:
                        file.write(", rowspan=" + str(aux_rowspan))
                    file.write(")\n")
            else:
                file.write(tabulation + "widget_" + str(index) + ".grid(row=" + str(x) + ", column=0, padx=4, pady=4, sticky='', columnspan=3)\n")
            x += 1

        # For each return value, the corresponding widget is placed according to its label (Widget).

        for index_retval, row_retval in return_value_data[return_value_data['BelongsTo'] == row['Name']].iterrows():
            if row_retval['Widget'] == "Label":
                file.write(tabulation + "desc_" + str(index_retval) + " = ttk.Label(" + root + ", text='" + row_retval['WidgetDescription'] + "')\n")
                file.write(tabulation + "desc_" + str(index_retval) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e')\n")
                y += 1
                file.write(tabulation + "widget_" + str(index_retval) + " = ttk.Label(" + root)
                if row_retval['Type'] == "bool":
                    file.write(", text='")
                    match main_data['LanguageID'].mode()[0]:
                        case 'en':
                            file.write("Empty")
                        case 'es':
                            file.write("Vacío")
                        case 'ca':
                            file.write("Buit")
                    file.write("', font=bold_font")
                elif row_retval['Type'] == "int":
                    file.write(", text=0")
                elif row_retval['Type'] == "float":
                    file.write(", text=0.0")
                elif row_retval['Type'] == "complex":
                    file.write(", text=0j")
                file.write(")\n")
                file.write(tabulation + "widget_" + str(index_retval) + ".grid(row=" + str(x) + ", column=" + str(y) +
                           ", padx=4, pady=4, sticky='w', columnspan=2)\n")
                x += 1
            elif row_retval['Widget'] == "Entry":
                is_a_password = any(sub_str in row_retval['Name'].lower() for sub_str in ["password", "contrasena", "contrasenya"]) and row_retval['Type'] == "str"
                file.write(tabulation + "desc_" + str(index_retval) + " = ttk.Label(" + root + ", text='" + row_retval['WidgetDescription'] + "')\n")
                file.write(tabulation + "desc_" + str(index_retval) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e')\n")
                y += 1
                file.write(tabulation + "widget_" + str(index_retval) + " = ttk.Entry(" + root)
                if is_a_password:
                    file.write(", show='•'")
                else:
                    file.write(", show=''")
                file.write(", state='readonly')\n")
                file.write(tabulation + "widget_" + str(index_retval) + ".grid(row=" + str(x) + ", column=" + str(y) +
                           ", padx=4, pady=4, sticky='we'")
                if is_a_password:
                    file.write(")\n\n")
                    y += 1
                    file.write(tabulation + "def toggle_password_" + str(index_retval) + "():\n")
                    file.write(tabulation + "\tif widget_" + str(index_retval) + ".cget('show') == '':\n")
                    file.write(tabulation + "\t\twidget_" + str(index_retval) + ".config(show='•')\n")
                    file.write(tabulation + "\telse:\n")
                    file.write(tabulation + "\t\twidget_" + str(index_retval) + ".config(show='')\n\n")
                    file.write(tabulation + "var_" + str(index_retval) + " = BooleanVar(value=False)\n")
                    file.write(tabulation + "show_hide_" + str(index_retval) + " = ttk.Checkbutton(" + root + ", text='")
                    match main_data['LanguageID'].mode()[0]:
                        case 'en':
                            file.write("Show password")
                        case 'es':
                            file.write("Mostrar contraseña")
                        case 'ca':
                            file.write("Mostrar contrasenya")
                    file.write("', variable=var_" + str(index_retval) + ", command=toggle_password_" + str(index_retval) + ")\n")
                    file.write(tabulation + "show_hide_" + str(index_retval) + ".grid(row=" + str(x) + ", column=" + str(y) +
                               ", padx=4, pady=4, sticky='')\n")
                else:
                    file.write(", columnspan=2)\n")
                x += 1
            elif row_retval['Widget'] == "Treeview":
                file.write(tabulation + "widget_" + str(index_retval) + " = ttk.Treeview(" + root + ", height=3)\n")
                file.write(tabulation + "widget_" + str(index_retval) + ".heading('#0', text='" + row_retval['WidgetLabel'] + "')\n")
                file.write(tabulation + "widget_" + str(index_retval) + ".grid(row=" + str(x) + ", column=" + str(y) +
                           ", padx=4, pady=4, sticky='we', columnspan=3)\n")
                x += 1
            y = 0
    return x, y

def set_merged_return_values(file, main_data, controller, i, x, y, root):
    """
    Sets the return values that have been merged from the same Controller at the top of the window by checking that
    they belong to more than one method (BelongsTo).

    Param:

    - file (_io.TextIOWrapper): File input/output reference.
    - main_data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - controller (str): The name of the current Controller.
    - i (int): LabelFrame counter.
    - x (int): Grid X position.
    - y (int): Grid Y position.
    - root (str): Root name.

    Return:

    - i (int): LabelFrame counter.
    - x (int): Grid X position.
    - y (int): Grid Y position.
    """
    return_value_data = main_data[main_data['IsAReturnValue'] == True]
    return_value_data = return_value_data[return_value_data['ClassName'] == controller]

    # For each merged return value, the corresponding widget is placed according to its label (Widget).

    for index, row in return_value_data[return_value_data['BelongsTo'].str.contains(',')].iterrows():
        if row['Widget'] == "Label":
            file.write("\t\tdesc_" + str(index) + " = ttk.Label(" + root + ", text='" + row['WidgetDescription'] + "')\n")
            file.write("\t\tdesc_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e')\n")
            y += 1
            file.write("\t\twidget_" + str(index) + " = ttk.Label(" + root)
            if row['Type'] == "bool":
                file.write(", text='")
                match main_data['LanguageID'].mode()[0]:
                    case 'en':
                        file.write("Empty")
                    case 'es':
                        file.write("Vacío")
                    case 'ca':
                        file.write("Buit")
                file.write("', font=bold_font")
            elif row['Type'] == "int":
                file.write(", text=0")
            elif row['Type'] == "float":
                file.write(", text=0.0")
            elif row['Type'] == "complex":
                file.write(", text=0j")
            file.write(")\n")
            file.write("\t\twidget_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='w', columnspan=2)\n")
            x += 1
        elif row['Widget'] == "Entry":
            is_a_password = any(sub_str in row['Name'].lower() for sub_str in ["password", "contrasena", "contrasenya"]) and row['Type'] == "str"
            file.write("\t\tdesc_" + str(index) + " = ttk.Label(" + root + ", text='" + row['WidgetDescription'] + "')\n")
            file.write("\t\tdesc_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='e')\n")
            y += 1
            file.write("\t\twidget_" + str(index) + " = ttk.Entry(" + root)
            if is_a_password:
                file.write(", show='•'")
            else:
                file.write(", show=''")
            file.write(", state='readonly')\n")
            file.write("\t\twidget_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we'")
            if is_a_password:
                file.write(")\n\n")
                y += 1
                file.write("\t\tdef toggle_password_" + str(index) + "():\n")
                file.write("\t\t\tif widget_" + str(index) + ".cget('show') == '':\n")
                file.write("\t\t\t\twidget_" + str(index) + ".config(show='•')\n")
                file.write("\t\t\telse:\n")
                file.write("\t\t\t\twidget_" + str(index) + ".config(show='')\n\n")
                file.write("\t\tvar_" + str(index) + " = BooleanVar(value=False)\n")
                file.write("\t\tshow_hide_" + str(index) + " = ttk.Checkbutton(" + root + ", text='")
                match main_data['LanguageID'].mode()[0]:
                    case 'en':
                        file.write("Show password")
                    case 'es':
                        file.write("Mostrar contraseña")
                    case 'ca':
                        file.write("Mostrar contrasenya")
                file.write(
                    "', variable=var_" + str(index) + ", command=toggle_password_" + str(index) + ")\n")
                file.write("\t\tshow_hide_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='')\n")
            else:
                file.write(", columnspan=2)\n")
            x += 1
        elif row['Widget'] == "Treeview":
            file.write("\t\twidget_" + str(index) + " = ttk.Treeview(" + root + ", height=3)\n")
            file.write("\t\twidget_" + str(index) + ".heading('#0', text='" + row['WidgetLabel'] + "')\n")
            file.write("\t\twidget_" + str(index) + ".grid(row=" + str(x) + ", column=" + str(y) + ", padx=4, pady=4, sticky='we', columnspan=3)\n")
            x += 1
        y = 0
    return i, x, y

def convert_to_camel_case(name):
    """
    Converts a name to camelCase format, separating the uppercase letters between characters with a space and then
    returning the rest as lowercase except for the first character.

    Param:

    - name (str): Name to be converted.

    Return:

    - new_name (str): Converted name.
    """
    new_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
    new_name = new_name[0] + new_name[1:].lower()
    return new_name

def count_decimals(num):
    """
    Determines how many significant decimal digits are present in a given number.

    Param:

    - num (float): Decimal number.

    Return:

    - digits (int): Number of significant decimal digits.
    """
    num_str = repr(num)
    if '.' in num_str:
        parte_decimal = num_str.split('.')[1].rstrip('0')
        return len(parte_decimal)
    else:
        return 0

def define_message_box(file):
    """
    Defines the message_box() method of the View class.

    Param:

    - file (_io.TextIOWrapper): File input/output reference.
    """
    file.write("\tdef message_box(self, _root, _type, _text, language):\n")
    file.write("\t\tglobal root_message_box\n")
    file.write("\t\tif root_message_box and root_message_box.winfo_exists():\n")
    file.write("\t\t\troot_message_box.lift()\n")
    file.write("\t\t\treturn\n")
    file.write("\t\troot_message_box = Toplevel(_root)\n")
    file.write("\t\troot_message_box.resizable(False, False)\n")
    file.write("\t\troot_message_box.columnconfigure(0, weight=1)\n")
    file.write("\t\troot_message_box.columnconfigure(1, weight=1)\n")
    file.write("\t\tw_message_box = (root_message_box.winfo_screenwidth() - root_message_box.winfo_reqwidth()) // 2\n")
    file.write(
        "\t\th_message_box = (root_message_box.winfo_screenheight() - root_message_box.winfo_reqheight()) // 2\n")
    file.write("\t\troot_message_box.geometry(f'+{w_message_box}+{h_message_box}')\n")
    file.write("\t\tif _type == 'warning':\n")
    file.write("\t\t\tmatch language:\n")
    file.write("\t\t\t\tcase 'en':\n")
    file.write("\t\t\t\t\troot_message_box.title('Warning')\n")
    file.write("\t\t\t\tcase 'es':\n")
    file.write("\t\t\t\t\troot_message_box.title('Aviso')\n")
    file.write("\t\t\t\tcase 'ca':\n")
    file.write("\t\t\t\t\troot_message_box.title('Avís')\n")
    file.write("\t\t\ticon_message_box = PhotoImage(file='icons/warning.png')\n")
    file.write("\t\telif _type == 'error':\n")
    file.write("\t\t\troot_message_box.title('Error')\n")
    file.write("\t\t\ticon_message_box = PhotoImage(file='icons/error.png')\n")
    file.write("\t\telse:\n")
    file.write("\t\t\troot_message_box.title(_type)\n")
    file.write("\t\t\ticon_message_box = PhotoImage(file='icons/default.png')\n")
    file.write("\t\t_icon = PhotoImage(file='icons/icon.png')\n")
    file.write("\t\troot_message_box.iconphoto(False, _icon)\n")
    file.write("\t\timage_message_box = ttk.Label(root_message_box, image=icon_message_box)\n")
    file.write("\t\timage_message_box.image = icon_message_box\n")
    file.write("\t\timage_message_box.grid(row=0, column=0, padx=4, pady=4, sticky='nswe')\n")
    file.write("\t\tlabel_message_box = ttk.Label(root_message_box, text=_text)\n")
    file.write("\t\tlabel_message_box.grid(row=0, column=1, padx=4, pady=4, sticky='we')\n")
    file.write("\t\tbutton_text = ''\n")
    file.write("\t\tmatch language:\n")
    file.write("\t\t\tcase 'en':\n")
    file.write("\t\t\t\tbutton_text = 'Accept'\n")
    file.write("\t\t\tcase 'es':\n")
    file.write("\t\t\t\tbutton_text = 'Aceptar'\n")
    file.write("\t\t\tcase 'ca':\n")
    file.write("\t\t\t\tbutton_text = 'Acceptar'\n")
    file.write(
        "\t\taccept_message_box = ttk.Button(root_message_box, text=button_text, command=root_message_box.destroy, width=12)\n")
    file.write("\t\taccept_message_box.grid(row=1, column=1, padx=4, pady=4, sticky='e')\n\n")
    file.write("\t\tdef on_close_message_box():\n")
    file.write("\t\t\tglobal root_message_box\n")
    file.write("\t\t\troot_message_box.destroy()\n")
    file.write("\t\t\troot_message_box = None\n\n")
    file.write("\t\troot_message_box.protocol('WM_DELETE_WINDOW', on_close_message_box)\n\n")

def define_update(file, main_data, model_data, model_attr):
    """
    Defines the update() method of the View class.

    Param:

    - file (_io.TextIOWrapper): File input/output reference.
    - main_data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - model_data (pandas.core.frame.DataFrame): Model data from the test dataset.
    - model_attr (list): List of indexs from Model attribute getters.
    """
    file.write("\tdef update(self):\n")
    for attr in model_attr:

        # Checks the type before writing the code.

        if model_data.loc[attr]['Type'] in ['int', 'float', 'bool', 'str', 'complex']:
            file.write("\t\tself.attr_" + str(attr) + ".config(text=")
            if model_data.loc[attr]['Type'] == "bool":
                file.write("get_boolean_str(self." + model_data.loc[attr]['ModelName'] + "." +
                           model_data.loc[attr]['BelongsTo'] + "(), '" + main_data['LanguageID'].mode()[0]
                           + "'), foreground=get_boolean_fg(self." + model_data.loc[attr]['ModelName'] + "."
                           + model_data.loc[attr]['BelongsTo'] + "()), font=bold_font")
            else:
                file.write("self." + model_data.loc[attr]['ModelName'] + "." + model_data.loc[attr]['BelongsTo'] + "()")
            file.write(")\n")
        else:
            file.write("\t\tset_treeview_items(self.attr_" + str(attr) + ", self." + model_data.loc[attr]['ModelName']
                       + "." + model_data.loc[attr]['BelongsTo'] + "(), '" + main_data['LanguageID'].mode()[0] + "')\n")
    file.write("\n")

def set_window_widgets(file, main_data, model_data, main_controller_name, actual_view, model_attr, row, index, is_triggered_from_menu=False):
    """
    Sets the widgets to be placed in the auxiliary window of a method.

    Param:

    - file (_io.TextIOWrapper): File input/output reference.
    - main_data (pandas.core.frame.DataFrame): Controller data from the test dataset.
    - model_data (pandas.core.frame.DataFrame): Model data from the test dataset.
    - main_controller_name (str): The name of the main Controller.
    - actual_view (int): Indicates the current View.
    - model_attr (list): List of indexs from Model attribute getters.
    - row (pandas.core.series.Series): Current method row.
    - index (int): Current method index.
    - is_triggered_from_menu (bool): Indicates whether the window is opened via a menu button or not.
    """
    _type = "window"
    if is_triggered_from_menu:  # If the window appears after pressing a menu button, changes the name of the root window.
        _type = "menu"
    file.write("\n\t\tdef trigger_" + _type + "_" + str(index) + "():\n")
    file.write("\t\t\tglobal root_" + _type + "_" + str(index) + "\n")
    file.write("\t\t\tif root_" + _type + "_" + str(index) + " and root_" + _type + "_" + str(index) + ".winfo_exists():\n")
    file.write("\t\t\t\troot_" + _type + "_" + str(index) + ".lift()\n")
    file.write("\t\t\t\treturn\n")
    file.write("\t\t\troot_" + _type + "_" + str(index) + " = Toplevel(")

    # If the window appears after pressing a button that appears in another view, the Toplevel should not be created
    # through the root of the main window.

    if not is_triggered_from_menu:
        file.write("root_" + str(actual_view + 1))
    else:
        file.write("self.root")
    file.write(")\n\t\t\troot_" + _type + "_" + str(index) + ".title('" + row['WidgetLabel'] + "')\n")  # Title.
    file.write("\t\t\troot_" + _type + "_" + str(index) + ".resizable(False, False)\n") # Not resizable.
    file.write("\t\t\troot_" + _type + "_" + str(index) + ".minsize(320, 0)\n") # Minimum width size.
    file.write("\t\t\troot_" + _type + "_" + str(index) + ".columnconfigure(0, weight=1)\n")
    file.write("\t\t\troot_" + _type + "_" + str(index) + ".columnconfigure(1, weight=1)\n")
    file.write("\t\t\troot_" + _type + "_" + str(index) + ".columnconfigure(2, weight=1)\n")
    file.write("\t\t\tw = (root_" + _type + "_" + str(index) + ".winfo_screenwidth() - root_" + _type + "_" +
               str(index) + ".winfo_reqwidth()) // 2\n")
    file.write("\t\t\th = (root_" + _type + "_" + str(index) + ".winfo_screenheight() - root_" + _type + "_" +
               str(index) + ".winfo_reqheight()) // 2\n")
    file.write("\t\t\troot_" + _type + "_" + str(index) + ".geometry(f'+{w}+{h}')\n")   # Sets window position.
    x = 0   # Grid X position.
    y = 0   # Grid Y position.
    aux_data = main_data[main_data['ClassName'] == row['ClassName']]
    method_data = aux_data[aux_data['Name'] == row['Name']]
    argument_and_return_value_data = aux_data[aux_data['BelongsTo'] == row['Name']]
    if row['ReturnValueName1'] == '':   # Configuration for those methods that do not return any value.
        file.write("\t\t\ticon_" + str(index) + " = PhotoImage(file='icons/edit.png')\n")  # Icon.
        file.write("\t\t\troot_" + _type + "_" + str(index) + ".iconphoto(False, icon_" + str(index) + ")\n")
        x, y = create_widgets(file, pd.concat([method_data, argument_and_return_value_data]).sort_index(), model_data,
                              main_controller_name,
                              model_attr, actual_view + 1, x, y, "root_" + _type + "_" + str(index), "\t\t\t", True,
                              False)
        file.write("\n")
        file.write("\t\t\tframe_" + _type + "_" + str(index) + " = Frame(root_" + _type + "_" + str(index) + ")\n")
        file.write("\t\t\tframe_" + _type + "_" + str(index) + ".grid(row=" + str(x) + ", column=0, columnspan=3, sticky='we')\n")
        file.write("\t\t\tframe_" + _type + "_" + str(index) + ".columnconfigure(0, weight=1)\n")
        file.write("\t\t\tframe_" + _type + "_" + str(index) + ".columnconfigure(1, weight=1)\n")
        file.write("\t\t\tcancel_" + str(index) + " = ttk.Button(frame_" + _type + "_" + str(index) + ", text='")
        match main_data['LanguageID'].mode()[0]:
            case 'en':
                file.write("Cancel")
            case 'es':
                file.write("Cancelar")
            case 'ca':
                file.write("Cancel·lar")
        file.write("', command=root_" + _type + "_" + str(index) + ".destroy, width=12)\n")
        file.write("\t\t\tcancel_" + str(index) + ".grid(row=0, column=1, padx=4, pady=4, sticky='w')\n")
        file.write("\t\t\taccept_" + str(index) + " = ttk.Button(frame_" + _type + "_" + str(index) + ", text='")
        match main_data['LanguageID'].mode()[0]:
            case 'en':
                file.write("Accept")
            case 'es':
                file.write("Aceptar")
            case 'ca':
                file.write("Acceptar")
        file.write("', command=lambda:trigger_button_" + str(index) + "(), width=12)\n")
        file.write("\t\t\taccept_" + str(index) + ".grid(row=0, column=0, padx=4, pady=4, sticky='e')\n\n")
        '''file.write("\t\t\tdef on_close_" + _type + "_" + str(index) + "():\n")
        file.write("\t\t\t\tglobal root_" + _type + "_" + str(index) + "\n")
        file.write("\t\t\t\troot_" + _type + "_" + str(index) + ".destroy()\n")
        file.write("\t\t\t\troot_" + _type + "_" + str(index) + " = None\n\n")
        file.write(
            "\t\t\troot_" + _type + "_" + str(index) + ".protocol('WM_DELETE_WINDOW', on_close_" + _type + "_" + str(index) + ")\n")'''
    elif row['ArgumentName1'] == '':    # Configuration for those methods that do not have any arguments.
        file.write("\t\t\ticon_" + str(index) + " = PhotoImage(file='icons/view.png')\n")  # Icon.
        file.write("\t\t\troot_" + _type + "_" + str(index) + ".iconphoto(False, icon_" + str(index) + ")\n")
        x, y = create_widgets(file, pd.concat([method_data, argument_and_return_value_data]).sort_index(), model_data,
                              main_controller_name,
                              model_attr, actual_view + 1, x, y, "root_" + _type + "_" + str(index), "\t\t\t", False,
                              False)
        file.write("\t\t\ttrigger_button_" + str(index) + "()\n")
        file.write("\t\t\tframe_" + _type + "_" + str(index) + " = Frame(root_" + _type + "_" + str(index) + ")\n")
        file.write("\t\t\tframe_" + _type + "_" + str(index) + ".grid(row=" + str(x) + ", column=0, columnspan=3, sticky='we')\n")
        file.write("\t\t\tframe_" + _type + "_" + str(index) + ".columnconfigure(0, weight=1)\n")
        file.write("\t\t\tclose_" + str(index) + " = ttk.Button(frame_" + _type + "_" + str(index) + ", text='")
        match main_data['LanguageID'].mode()[0]:
            case 'en':
                file.write("Close")
            case 'es':
                file.write("Cerrar")
            case 'ca':
                file.write("Tancar")
        file.write("', command=root_" + _type + "_" + str(index) + ".destroy, width=12)\n")
        file.write("\t\t\tclose_" + str(index) + ".grid(row=0, column=0, padx=4, pady=4, sticky='')\n\n")
        '''file.write("\t\t\tdef on_close_" + _type + "_" + str(index) + "():\n")
        file.write("\t\t\t\tglobal root_" + _type + "_" + str(index) + "\n")
        file.write("\t\t\t\troot_" + _type + "_" + str(index) + ".destroy()\n")
        file.write("\t\t\t\troot_" + _type + "_" + str(index) + " = None\n\n")
        file.write(
            "\t\t\troot_" + _type + "_" + str(index) + ".protocol('WM_DELETE_WINDOW', on_close_" + _type + "_" + str(index) + ")\n")'''
    else:   # Configuration for those methods that have arguments and return values.
        file.write("\t\t\ticon_" + str(index) + " = PhotoImage(file='icons/others.png')\n")  # Icon.
        file.write("\t\t\troot_" + _type + "_" + str(index) + ".iconphoto(False, icon_" + str(index) + ")\n")
        x, y = create_widgets(file, pd.concat([method_data, argument_and_return_value_data]).sort_index(), model_data,
                              main_controller_name,
                              model_attr, actual_view + 1, x, y, "root_" + _type + "_" + str(index), "\t\t\t", False,
                              True)
        file.write("\t\t\tframe_" + _type + "_" + str(index) + " = Frame(root_" + _type + "_" + str(index) + ")\n")
        file.write("\t\t\tframe_" + _type + "_" + str(index) + ".grid(row=" + str(x) + ", column=0, columnspan=3, sticky='we')\n")
        file.write("\t\t\tframe_" + _type + "_" + str(index) + ".columnconfigure(0, weight=1)\n")
        file.write("\t\t\tclose_" + str(index) + " = ttk.Button(frame_" + _type + "_" + str(index) + ", text='")
        match main_data['LanguageID'].mode()[0]:
            case 'en':
                file.write("Close")
            case 'es':
                file.write("Cerrar")
            case 'ca':
                file.write("Tancar")
        file.write("', command=root_" + _type + "_" + str(index) + ".destroy, width=12)\n")
        file.write("\t\t\tclose_" + str(index) + ".grid(row=0, column=0, padx=4, pady=4, sticky='')\n\n")
    file.write("\t\t\tdef on_close_" + _type + "_" + str(index) + "():\n")
    file.write("\t\t\t\tglobal root_" + _type + "_" + str(index) + "\n")
    file.write("\t\t\t\troot_" + _type + "_" + str(index) + ".destroy()\n")
    file.write("\t\t\t\troot_" + _type + "_" + str(index) + " = None\n\n")
    file.write("\t\t\troot_" + _type + "_" + str(index) + ".protocol('WM_DELETE_WINDOW', on_close_" + _type + "_" +
               str(index) + ")\n")