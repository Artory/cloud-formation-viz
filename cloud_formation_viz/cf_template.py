import json

import yaml


def equals_constructor(self, node):
    value = self.construct_sequence(node)
    return value.count(value[0]) == len(value)


def if_constructor(self, node):
    condition, then, otherwise = self.construct_sequence(node)
    return then if condition else otherwise


def getatt_constructor(self, node):
    value = self.construct_scalar(node)
    return {'Fn::GetAtt': [value]}


def join_constructor(self, node):
    scalar, sequence = node.value
    sep = self.construct_scalar(scalar)
    items = self.construct_sequence(sequence)
    return {'Fn::Join': [sep, items]}


def ref_constructor(self, node):
    value = self.construct_scalar(node)
    return {'Ref': value}


def init_yaml():
    yaml.SafeLoader.add_constructor(u'!Equals', equals_constructor)
    yaml.SafeLoader.add_constructor(u'!If', if_constructor)
    yaml.SafeLoader.add_constructor(u'!GetAtt', getatt_constructor)
    yaml.SafeLoader.add_constructor(u'!Join', join_constructor)
    yaml.SafeLoader.add_constructor(u'!Ref', ref_constructor)


def load(f):
    try:
        return json.load(f)
    except json.decoder.JSONDecodeError:
        f.seek(0)
        init_yaml()
        return yaml.safe_load(f)
