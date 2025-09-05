# MVCGUIGenerator

This tool generates the GUI design of a program according to the Model and Controller part(s) implementation, following the MVC architecture and applying a ML model, with the premise of generating a GUI that corresponds to the View part(s).

## Main features

- Supports **9 widgets**.
- Supports up to **10 arguments/return values** ​​for the same method.
- **Type hints** support (must be used to allow data type extraction for arguments/return values).
- Uses **SGD classifier** (less than 100.000 samples).

## How it works

1. Implement the source code following the MVC architecture (only Models and Controllers must be implemented). Source code must be located inside `code` folder.
2. Run the `main.py` file.
3. A window will appear. Click `Scan` button to scan the implemented source code. This will allow to modify the settings prior to GUI generation.
4. Once the settings has been modified, click `Generate` button to start the generation process.
5. Run `code\main.py` file.

## Screenshots

TBD.

## Used libraries

- **Tkinter**.
- **Pandas**.
- **AST** (Abstract Syntax Tree).
- **Scikit-Learn**.
- **LangID**.

## Installation

1. Clone this repository:

```terminal
git clone https://github.com/RubenRS040398/MVCGUIGenerator.git
```

2. Install the libraries specified above (it is recommended to run the project with the PyCharm Community Edition IDE).

## Main structure

The tool is divided into six modules:

| Module | Description |
| - | - |
| `main.py` | Program's main flow, including a window in order to modify the settings prior to GUI generation. |
| `load.py` | Functions associated with loading Python files (source code and data). |
| `scanner.py` | Functions which are used to scan the code through syntactic analysis (Abstract Syntax Tree module) allowing the feature extraction for the learning phase (test set). |
| `model.py` | Functions which allows model training once the training and test datasets are available (Scikit-Learn library). |
| `refiner.py` | Additional functions in order to improve the results obtained during the learning phase and subsequently translate them into GUI elements, among other stuff. |
| `generator.py` | Functions which translate the learning outcomes into GUI design using pre-established source code (Tkinter module). |

## Supported widgets

| Widget | Data type | Input | Process | Output |
| - | - | - | - | - |
| Label | `int, float, bool, complex, str` | No | No | Yes |
| Entry | `complex, str` | Yes | No | Yes |
| Button | - | No | Yes | No |
| Checkbutton | `bool` | Yes | No | No |
| Radiobutton | `str` | Yes | No | No |
| Scale | `int, float` | Yes | No | No |
| Spinbox | `int, float` | Yes | No | No |
| Combobox | `str` | Yes | No | No |
| Treeview | `list, tuple, set, dict` | Yes | No | Yes |

*Note: The IPO model is used to extrapolate the relationship between supported widgets and their counterparts at the code syntax level (input would be equivalent to an argument, process to method call, and output to a return value).*

## Data features

| Name | Description | Type (`dtype`) |
| - | - | - |
| Name | Method name/argument/return value. | `object` |
| Type | Data type of the method/argument/return value. Can be `int`, `float`, `bool`, `str`, `complex`, `list`, `tuple`, `set` or `dict` (`NaN` for any type). | `object` |
| From | Minimum value with which an argument of type `int` or `float` can be assigned. | `float64` |
| To | Maximum value with which an argument of type `int` or `float` can be assigned. | `float64` |
| IsAnArgument | If `True`, it is an argument, otherwise `False`. | `bool` |
| IsAMethod | If `True`, it is a method, otherwise `False`. | `bool` |
| IsAReturnValue | If `True`, it is a return value, otherwise `False`. | `bool` |
| ArgumentName1-10 | Name of the arguments passed to a method, if required. | `object` |
| ArgumentType1-10 | Data type of the arguments passed to a method, if required. | `object` |
| ReturnValueName1-10 | Name of the return values passed to a method, if required. | `object` |
| ReturnValueType1-10 |  Data type of the return values passed to a method, if required. | `object` |
| DefaultValue | Default value of an argument, if required. | `object` |
| PossibleValues | Set of possible values ​​that an argument of type `str` could take, if required. The values ​​are separated by a comma. | `object` |
| BelongsTo | Name of the method which an argument or return value belongs to. | `object` |
| ClassName | Name of the class which a method/argument/return value belongs to. | `object` |
| UsedByView | If `True`, it has direct communication with the View, otherwise `False`. | `bool` |
| Widget | Widget label name. | `object` |

## License

This project is under the MIT License.

## Others

This project is part of the Final Degree Project called *Generation of the graphical interface design of a program based on the MVC architecture using machine learning*. You can find more related information [here](https://ddd.uab.cat/pub/tfg/2024/tfg_8713429/InformeFinal.pdf).