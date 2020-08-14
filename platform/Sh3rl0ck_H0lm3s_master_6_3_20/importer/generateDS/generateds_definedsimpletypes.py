
class TypeDescriptor(object):
    def __init__(self, name, type_name=None):
        self.name_ = name
        self.type_name_ = type_name
        self.type_obj_ = None
    def __str__(self):
        return '<%s -- name: %s type: %s>' % (self.__class__.__name__,
            self.name, self.type_name,)
    def get_name_(self):
        return self.name_
    def set_name_(self, name):
        self.name_ = name
    name = property(get_name_, set_name_)
    def get_type_name_(self):
        return self.type_name_
    def set_type_name_(self, type_name):
        self.type_name_ = type_name
    type_name = property(get_type_name_, set_type_name_)
    def get_type_obj_(self):
        return self.type_obj_
    def set_type_obj_(self, type_obj):
        self.type_obj_ = type_obj
    type_obj = property(get_type_obj_, set_type_obj_)

class ComplexTypeDescriptor(TypeDescriptor):
    def __init__(self, name):
        super(ComplexTypeDescriptor, self).__init__(name)
        self.elements_ = []
        self.attributes_ = {}
    def get_elements_(self):
        return self.elements_
    def set_elements_(self, elements):
        self.elements_ = elements
    elements = property(get_elements_, set_elements_)
    def get_attributes_(self):
        return self.attributes_
    def set_attributes_(self, attributes):
        self.attributes_ = attributes
    attributes = property(get_attributes_, set_attributes_)

class SimpleTypeDescriptor(TypeDescriptor):
    def __init__(self, name, type_name):
        super(SimpleTypeDescriptor, self).__init__(name, type_name)

Defined_simple_type_table = {
    'nameType': SimpleTypeDescriptor('nameType', 'string'),
    'UUID': SimpleTypeDescriptor('UUID', 'string'),
}

