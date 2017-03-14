
class NestedObject(object):
    def add_element(self, elementname, element):
        setattr(self, elementname, element)

def tupperware(mapping):
    result = NestedObject()
    for key, value in mapping.items():
        new_value = objectify(mapping[key])
        result.add_element(key, new_value)
    return result


def objectify(mapping):
    result = NestedObject()
    for key, value in mapping.items():
        result.add_element(key, value)
    return result


