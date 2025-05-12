import os

def generate(main_data, init_data, model_data, main_controller_name, title, about, view_threshold=3, window_threshold=5, show_model_attr=False, hide_model_attr=False):
    if os.path.exists('code/main.py'):
        os.remove('code/main.py')
    if os.path.exists('code/view.py'):
        os.remove('code/view.py')
    views = create_main_file(init_data, main_controller_name, view_threshold, show_model_attr)
    create_view_file(main_data, model_data, views, title, about, window_threshold, show_model_attr, hide_model_attr)

def create_main_file(init_data, main_controller_name, view_threshold, show_model_attr):
    folder = os.path.join(os.getcwd(), 'code')
    file_names = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    file_path = os.path.join('code', 'main.py')
    models = {}
    for index, row in init_data[init_data['UsedByView'] == False].iterrows():
        models[row['ClassName']] = []
        i = 0
        while i < 10 and row['ArgumentName' + str(i + 1)] != '':
            match row['ArgumentType' + str(i + 1)]:
                case 'int':
                    models[row['ClassName']].append("0")
                case 'float':
                    models[row['ClassName']].append("0.0")
                case 'bool':
                    models[row['ClassName']].append("False")
                case 'str':
                    models[row['ClassName']].append("''")
                case 'complex':
                    models[row['ClassName']].append("complex()")
                case 'list':
                    models[row['ClassName']].append("[]")
                case 'tuple':
                    models[row['ClassName']].append("tuple()")
                case 'set':
                    models[row['ClassName']].append("set()")
                case 'dict':
                    models[row['ClassName']].append("{}")
            i += 1
    controllers = {}
    for index, row in init_data[init_data['UsedByView'] == True].iterrows():
        controllers[row['ClassName']] = []
        i = 0
        while i < 10 and row['ArgumentName' + str(i + 1)] != '':
            controllers[row['ClassName']].append(row['ArgumentType' + str(i + 1)])
            i += 1
    views = {}
    if len(controllers) <= view_threshold:
        if show_model_attr:
            views['View'] = list(controllers.keys()) + list(models.keys())
        else:
            views['View'] = list(controllers.keys())
    else:
        #del views[main_controller_name]
        i = 66
        views['View'] = []
        for key in controllers:
            views['View_' + chr(i)] = [key]
            if show_model_attr:
                views['View_' + chr(i)] += controllers[key]
            #else:
                #views['View_' + chr(i)] = [key]
            views['View'].append('View_' + chr(i))
            i += 1
        views['View'].append(main_controller_name)
        if show_model_attr:
            views['View'] += controllers[main_controller_name]
    with open(file_path, 'w') as file:
        #file.write("from tkinter import *\n")
        #file.write("from tkinter import ttk\n")
        for file_name in file_names:
            file.write("from " + str(file_name.replace('.py', '')) + " import *\n")
        file.write("from view import *\n\n")
        for key, value in models.items():
            file.write(key.lower() + " = " + key + "(" + ', '.join(value) + ")\n")
        for key, value in controllers.items():
            file.write(key.lower() + " = " + key + "(" + ', '.join(value).lower() + ")\n")
        for key, value in views.items():
            file.write(key.lower() + " = " + key + "(" + ', '.join(value).lower() + ")\n")
    return views

def create_view_file(main_data, model_data, views, title, about, window_threshold, show_model_attr, hide_model_attr):
    file_path = os.path.join('code', 'view.py')
    with open(file_path, 'w') as file:
        file.write("from tkinter import *\nfrom tkinter import ttk\nfrom tkinter import messagebox\n\nclass View:\n\tdef __init__(self, " + ', '.join(views['View']).lower() + "):\n")
        for value in views['View']:
            file.write("\t\tself." + value.lower() + " = " + value.lower() + "\n")
        file.write("\t\troot = Tk()\n\t\troot.title('" + title + "')\n")
        windowed_methods = create_menu(file, main_data, views, about, window_threshold)
        #print(main_data)
        file.write("\t\troot.mainloop()")

def create_menu(file, main_data, views, about, window_threshold):
    windowed_methods = []
    file.write("\t\tmenu = Menu(root)\n\t\troot.config(menu=menu)\n\t\tfile = Menu(menu, tearoff=0)\n\t\tmenu.add_cascade(label='")
    match main_data['LanguageID'].mode()[0]:
        case 'en':
            file.write("File")
        case 'es':
            file.write("Archivo")
        case 'ca':
            file.write("Fitxer")
    file.write("', menu=file)\n")
    #menubutton_data = main_data[main_data['ClassName'] == views['View'][-1]]
    menubutton_data = main_data[main_data['Widget'] == 'Menubutton']
    menubutton_data = menubutton_data[menubutton_data['ArgumentName1'] == '']
    for index, row in menubutton_data[menubutton_data['ReturnValueName1'] == ''].iterrows():
        file.write("\t\tfile.add_command(label='" + row['WidgetLabel'] + "', command=lambda:" + row['ClassName'].lower() + "." + row['Name'] + "())\n")
    if not menubutton_data[menubutton_data['ReturnValueName1'] == ''].empty:
        file.write("\t\tfile.add_separator()\n")
    file.write("\t\tfile.add_command(label='")
    match main_data['LanguageID'].mode()[0]:
        case 'en':
            file.write("Exit")
        case 'es':
            file.write("Salir")
        case 'ca':
            file.write("Sortir")
    file.write("', command=root.quit)\n")
    #menubutton_data = main_data[main_data['ClassName'] == views['View'][-1]]
    menubutton_data = main_data[main_data['Widget'] == 'Menubutton']
    menubutton_data = menubutton_data[menubutton_data['ArgumentName1'] != '']
    if not menubutton_data[menubutton_data['ReturnValueName1'] == ''].empty or len(views) > 1:
        file.write("\t\tedit = Menu(menu, tearoff=0)\n\t\tmenu.add_cascade(label='")
        match main_data['LanguageID'].mode()[0]:
            case 'en':
                file.write("Edit")
            case 'es' | 'ca':
                file.write("Editar")
        file.write("', menu=edit)\n")
        for index, row in menubutton_data[menubutton_data['ReturnValueName1'] == ''].iterrows():
            #REPLACE: file.write("\t\tedit.add_command(label='" + row['WidgetLabel'] + "', command=lambda:" + row['ControllerName'].lower() + ".open_" + row['Name'] + "())\n")
            file.write("\t\tedit.add_command(label='" + row['WidgetLabel'] + "')\n")
            windowed_methods.append(row['Name'])
        if len(views) > 1:
            if not menubutton_data[menubutton_data['ReturnValueName1'] == ''].empty:
                file.write("\t\tedit.add_separator()\n")
            for i in range(len(views) - 1):
                menubutton_data = main_data[main_data['ClassName'] == views['View_' + chr(66 + 1)][0]]
                if menubutton_data[menubutton_data['ReturnValueName1'] != ''].empty:
                    #REPLACE: file.write("\t\tedit.add_command(label='" + views['View_' + chr(66 + 1)][0] + "...', command=lambda:View_" + chr(66 + 1) + "())\n")
                    file.write("\t\tedit.add_command(label='" + views['View_' + chr(66 + 1)][0] + "...')\n")
    #menubutton_data = main_data[main_data['ClassName'] == views['View'][-1]]
    menubutton_data = main_data[main_data['Widget'] == 'Menubutton']
    menubutton_data = menubutton_data[menubutton_data['ReturnValueName1'] != '']
    if not menubutton_data[menubutton_data['ArgumentName1'] == ''].empty or len(views) > 1:
        file.write("\t\tview = Menu(menu, tearoff=0)\n\t\tmenu.add_cascade(label='")
        match main_data['LanguageID'].mode()[0]:
            case 'en':
                file.write("View")
            case 'es':
                file.write("Ver")
            case 'ca':
                file.write("Veure")
        file.write("', menu=view)\n")
        for index, row in menubutton_data[menubutton_data['ArgumentName1'] == ''].iterrows():
            # REPLACE: file.write("\t\tedit.add_command(label='" + row['WidgetLabel'] + "', command=lambda:" + row['ControllerName'].lower() + ".open_" + row['Name'] + "())\n")
            file.write("\t\tview.add_command(label='" + row['WidgetLabel'] + "')\n")
            windowed_methods.append(row['Name'])
        if len(views) > 1:
            if not menubutton_data[menubutton_data['ArgumentName1'] == ''].empty:
                file.write("\t\tview.add_separator()\n")
            for i in range(len(views) - 1):
                menubutton_data = main_data[main_data['ClassName'] == views['View_' + chr(66 + 1)][0]]
                if menubutton_data[menubutton_data['ArgumentName1'] != ''].empty:
                    #REPLACE: file.write("\t\tedit.add_command(label='" + views['View_' + chr(66 + 1)][0] + "...', command=lambda:View_" + chr(66 + 1) + "())\n")
                    file.write("\t\tedit.add_command(label='" + views['View_' + chr(66 + 1)][0] + "...')\n")
    #menubutton_data = main_data[main_data['ClassName'] == views['View'][-1]]
    menubutton_data = main_data[main_data['Widget'] == 'Menubutton']
    menubutton_data = menubutton_data[menubutton_data['ArgumentName1'] != '']
    if not menubutton_data[menubutton_data['ReturnValueName1'] != ''].empty or len(views) > 1:
        file.write("\t\tothers = Menu(menu, tearoff=0)\n\t\tmenu.add_cascade(label='")
        match main_data['LanguageID'].mode()[0]:
            case 'en':
                file.write("Others")
            case 'es':
                file.write("Otros")
            case 'ca':
                file.write("Altres")
        file.write("', menu=others)\n")
        for index, row in menubutton_data[menubutton_data['ReturnValueName1'] != ''].iterrows():
            # REPLACE: file.write("\t\tothers.add_command(label='" + row['WidgetLabel'] + "', command=lambda:" + row['ControllerName'].lower() + ".open_" + row['Name'] + "())\n")
            file.write("\t\tothers.add_command(label='" + row['WidgetLabel'] + "')\n")
            windowed_methods.append(row['Name'])
        if len(views) > 1:
            if not menubutton_data[menubutton_data['ReturnValueName1'] != ''].empty:
                file.write("\t\tothers.add_separator()\n")
            for i in range(len(views) - 1):
                menubutton_data = main_data[main_data['ClassName'] == views['View_' + chr(66 + 1)][0]]
                if not menubutton_data[menubutton_data['ArgumentName1'] != ''].empty and not menubutton_data[menubutton_data['ReturnValueName1'] != ''].empty:
                    # REPLACE: file.write("\t\tothers.add_command(label='" + views['View_' + chr(66 + 1)][0] + "...', command=lambda:View_" + chr(66 + 1) + "())\n")
                    file.write("\t\tothers.add_command(label='" + views['View_' + chr(66 + 1)][0] + "...')\n")
    file.write("\t\t_help = Menu(menu, tearoff=0)\n\t\tmenu.add_cascade(label='")
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
            file.write("About...', command=lambda:messagebox.showinfo('About...', '" + about + "'))\n")
        case 'es':
            file.write("Acerca de...', command=lambda:messagebox.showinfo('Acerca de...', '" + about + "'))\n")
        case 'ca':
            file.write("Sobre...', command=lambda:messagebox.showinfo('Sobre...', '" + about + "'))\n")
    return windowed_methods