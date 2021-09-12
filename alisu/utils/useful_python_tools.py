from collections import namedtuple


def dict_snake_case(data: dict, same_for_sub_dict: bool = True):
    output_dict = {}
    for data_keys, data_values in data.items():
        if same_for_sub_dict:
            if isinstance(data_values, dict):
                data_values = dict_snake_case(data_values)
            output_dict[data_keys.replace(" ", "_")] = data_values
        else:
            output_dict[data_keys.replace(" ", "_")] = data_values
    return output_dict


def dict2py(data: dict, name: str = "pyobject"):
    return namedtuple(name, data.keys())(*data.values())
