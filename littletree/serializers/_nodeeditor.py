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


# class DataNodeEditor:
#     def __init__(self, fields, distance_field, comment_field):
#         self.fields = fields
#         self.distance_field = distance_field
#         self.comment_field = comment_field
#
#     def apply_distance(self, node, distance):
#         getattr(node, self.fields)[self.distance_field] = distance
#
#     def apply_comment(self, node, comment):
#         comment_field = self.comment_field
#         data = getattr(node, self.fields)
#         if comment_field in data:
#             data[comment_field] += f"|{comment}"
#         else:
#             data[comment_field] = comment
#
#     def apply_items(self, node, items):
#         data = getattr(node, self.fields)
#         data.update(items)
#
#
# class FieldNodeEditor:
#     def __init__(self, fields, distance_field, comment_field):
#         self.fields = fields
#         self.distance_field = distance_field
#         self.comment_field = comment_field
#
#     def apply_distance(self, node, distance):
#         setattr(node, self.distance_field, distance)
#
#     def apply_comment(self, node, comment):
#         comment_field = self.comment_field
#         if comment_field:
#             if existing_comment := getattr(node, comment_field):
#                 comment = existing_comment + f"|{comment}"
#                 setattr(node, comment_field, comment)
#             else:
#                 setattr(node, comment_field, comment)
#
#     def apply_items(self, node, items):
#         existing_fields = self.fields
#         for field, value in items.items():
#             if field in existing_fields:
#                 setattr(node, field, items[field])
