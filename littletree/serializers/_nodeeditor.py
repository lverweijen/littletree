from typing import Sequence


def get_editor(fields, data):
    if fields:
        return FieldNodeEditor(fields)
    elif data:
        return DataNodeEditor(data)
    else:
        return FieldNodeEditor([])


class DataNodeEditor:
    def __init__(self, data_field):
        if not isinstance(data_field, str):
            raise ValueError("data field should be a string")
        self.data_field = data_field

    def get_attributes(self, node):
        return getattr(node, self.data_field)

    def get(self, node, field, default=None):
        return getattr(node, self.data_field).get(field, default)

    def set(self, node, field, value):
        getattr(node, self.data_field)[field] = value

    def update(self, node, attributes):
        return getattr(node, self.data_field).update(attributes)


class FieldNodeEditor:
    def __init__(self, fields):
        if not isinstance(fields, Sequence) and all(isinstance(field, str) for field in fields):
            raise ValueError("field should be a sequence of strings")
        elif isinstance(fields, str):
            raise TypeError(f"fields should be given as [{fields!r}]")
        self.fields = fields

    def get_attributes(self, node):
        return {field: getattr(node, field) for field in self.fields}

    def get(self, node, field):
        if field in self.fields:
            return getattr(node, field)

    def set(self, node, field, value):
        if field in self.fields:
            return setattr(node, field, value)

    def update(self, node, attributes):
        for k, v in attributes.items():
            self.set(node, k, v)
