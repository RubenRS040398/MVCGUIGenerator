from load import *
from scanner import *
from model import *
from refiner import *
from generator import *
from tkinter import *
from tkinter import ttk
from tkinter import font
import time

train_data = None   # Training dataset
test_data = None    # Test dataset belonging to the scanned source code
init_data = None    # Dataset of Model and Controller constructors (methods only)
model_data = None   # Dataset belonging to the Models of the scanned source code

def toggle_scan():  # Initialize the source code scanning process
    global train_data
    global test_data
    global init_data
    global model_data

    _code = load_source_code()  # Loads the source code
    _test_data = scan(_code)    # Scan the code and return the test dataset
    _train_data = load_train_data()
    _init_data = _test_data[_test_data['Name'] == '__init__'].reset_index(drop=True)
    _model_data = _test_data[_test_data['Name'] != '__init__'].reset_index(drop=True)
    _model_data = _model_data[_model_data['UsedByView'] == False].reset_index(drop=True)
    _test_data = _test_data[_test_data['Name'] != '__init__'].reset_index(drop=True)
    _test_data = _test_data[_test_data['UsedByView'] == True].reset_index(drop=True)

    window_title.config(state='enabled')
    window_title.delete(0, END)
    window_title.insert(0, 'Main window')
    main_controller.config(state='readonly')
    controller_data = _test_data[_test_data['UsedByView'] == True]
    main_controller['values'] = list(controller_data['ClassName'].unique())
    main_controller.current(0)
    display_model_attributes.config(state='enabled')
    hide_methods.config(state='enabled')
    multiple_views.config(state='enabled')
    multiple_views.set(3)
    about.config(state='enabled')
    about.insert(0, '2025 - MVCGUIGenerator')
    separate_window.config(state='enabled')
    separate_window.set(5)
    evaluate_button.config(state='enabled')
    generate_button.config(state='enabled')

    train_data = _train_data
    test_data = _test_data
    init_data = _init_data
    model_data = _model_data

def toggle_evaluate():  # Evaluate the model by preprocessing and performing a classification using CV
    global train_data
    global test_data

    x_train, y_train, _ = preprocess_and_split(train_data, test_data)
    classifier = fit(x_train, y_train)
    evaulate(classifier, x_train, y_train)

def toggle_generate():  # Generates the GUI and destroys this window
    global train_data
    global test_data
    global init_data
    global model_data

    init_time = time.time()
    x_train, y_train, x_test = preprocess_and_split(train_data, test_data)
    classifier = fit(x_train, y_train)
    y_test = classify(classifier, x_test)
    main_data = pd.concat([test_data, y_test], axis=1)
    main_data, model_data = refine(main_data, init_data, model_data, main_controller.get(), show_model_attr.get(), hide_model_attr.get(), int(multiple_views.get()), int(window_threshold.get()))
    generate(main_data, init_data, model_data, main_controller.get(), window_title.get(), "Copyright...", int(multiple_views.get()))
    print("Elapsed time: " + str(time.time() - init_time) + " seconds")
    root.destroy()

# Initializes the main generator window

root = Tk()
root.title('MVCGUIGenerator')
root.resizable(False, False)
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
w = (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2
h = (root.winfo_screenheight() - root.winfo_reqheight()) // 4
root.geometry(f'+{w}+{h}')
icon = PhotoImage(file='media/GUIMVCLogo48px.png')
root.iconphoto(False, icon)
bold_font = font.nametofont('TkDefaultFont').copy()
bold_font.configure(weight='bold')
title_font = font.nametofont('TkDefaultFont').copy()
title_font.configure(weight='bold', size=16)
title_style = ttk.Style()
title_style.configure('Custom.TLabel', font=title_font, foreground="#3f48cc", size=16)  # Hex color (orange-red)
logo = PhotoImage(file='media/GUIMVCLogo128px.png')
large_icon = ttk.Label(root, image=logo)
large_icon.image = logo
large_icon.grid(row=0, column=0, padx=4, pady=4, columnspan=2)
title = ttk.Label(root, text='Model-View-Controller GUI Generator', style='Custom.TLabel')
title.grid(row=1, column=0, padx=4, pady=4, columnspan=2)
scan_button = ttk.Button(root, text='Scan', width=12, command=lambda:toggle_scan())
scan_button.grid(row=2, column=0, padx=4, pady=4, columnspan=2)
desc_1 = ttk.Label(root, text='Main window title:')
desc_1.grid(row=3, column=0, padx=4, pady=4, sticky='e')
window_title = ttk.Entry(root, state='disabled')
window_title.grid(row=3, column=1, padx=4, pady=4, sticky='we')
desc_2 = ttk.Label(root, text='Main controller:')
desc_2.grid(row=4, column=0, padx=4, pady=4, sticky='e')
main_controller = ttk.Combobox(root, state='disabled')
main_controller.grid(row=4, column=1, padx=4, pady=4, sticky='we')
show_model_attr = BooleanVar()
display_model_attributes = ttk.Checkbutton(root, text='Display Model attributes', variable=show_model_attr, state='disabled')
display_model_attributes.grid(row=5, column=0, padx=4, pady=4, columnspan=2)
hide_model_attr = BooleanVar()
hide_methods = ttk.Checkbutton(root, text='Hide methods which return Model attributes', variable=hide_model_attr, state='disabled')
hide_methods.grid(row=6, column=0, padx=4, pady=4, columnspan=2)
desc_3 = ttk.Label(root, text='Min. num. of Controllers to split\nthe View into multiple Views:')
desc_3.grid(row=7, column=0, padx=4, pady=4, sticky='e')
view_threshold = IntVar()
multiple_views = ttk.Spinbox(root, textvariable=view_threshold, from_=2, to=5, state='disabled')
multiple_views.grid(row=7, column=1, padx=4, pady=4, sticky='we')
desc_4 = ttk.Label(root, text='Min. num. of arguments/return\nvalues to display methods\nin a separate window:')
desc_4.grid(row=8, column=0, padx=4, pady=4, sticky='e')
window_threshold = IntVar()
separate_window = ttk.Spinbox(root, textvariable=window_threshold, from_=2, to=10, state='disabled')
separate_window.grid(row=8, column=1, padx=4, pady=4, sticky='we')
cont = ttk.LabelFrame(root, text='About description:', style='Bold.TLabelframe')
cont.grid(row=9, column=0, padx=4, pady=4, sticky='we', columnspan=2)
cont.columnconfigure(0, weight=1)
about = ttk.Entry(cont, state='disabled')
about.grid(row=0, column=0, padx=4, pady=4, sticky='we')
evaluate_button = ttk.Button(root, text='Evaluate', width=12, state='disabled', command=lambda:toggle_evaluate())
evaluate_button.grid(row=10, column=0, padx=4, pady=4, columnspan=2)
generate_button = ttk.Button(root, text='Generate', width=12, state='disabled', command=lambda:toggle_generate())
generate_button.grid(row=11, column=0, padx=4, pady=4, columnspan=2)
_exit = ttk.Button(root, text='Exit', width=11, command=root.destroy)
_exit.grid(row=12, column=0, padx=4, pady=4, columnspan=2)
root.mainloop()