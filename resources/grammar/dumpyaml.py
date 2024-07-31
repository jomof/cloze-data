import yaml
from collections import OrderedDict

class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)

def str_presenter(dumper, data):
    # If the string has newline characters, use block style
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())

def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))

yaml.add_representer(str, str_presenter, Dumper=MyDumper)
yaml.add_representer(OrderedDict, dict_representer, Dumper=MyDumper)
yaml.add_constructor('tag:yaml.org,2002:map', dict_constructor, Loader=yaml.Loader)

def dump_yaml(data):
    return yaml.dump(data, Dumper=MyDumper, allow_unicode=True, default_flow_style=False, width=100, sort_keys=False)

def dump_yaml_file(data, file):
    return yaml.dump(data, file, Dumper=MyDumper, allow_unicode=True, default_flow_style=False, width=100, sort_keys=False)
