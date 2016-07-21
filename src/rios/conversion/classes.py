"""
RIOS objects are all implemented as subclasses of DefinitionSpecification
which is a subclass of OrderedDict.

A dict would suffice, but the OrderedDict output matches the order
of the Rios on-line documentation at
http://rios.readthedocs.org/en/latest/index.html

The RIOS objects are instantiated with ALL their attributes however
all the "empty" attributes must be removed to pass RIOS validation.
DefinitionSpecification.clean() will recurse through the object and
remove all the "empty" attributes.

Note that clean() does not consider False, 0, 0.0, or None to be empty.
Use '', the empty string, to ensure an attribute will be removed.
"""
import collections

__all__ = (
        'DefinitionSpecification',
        'Instrument',
        'FieldObject',
        'TypeCollectionObject',
        'TypeObject',
        'ColumnObject',
        'RowObject',
        'BoundConstraintObject',
        'EnumerationCollectionObject',
        'EnumerationObject',
        'CalculationSetObject',
        'InstrumentReferenceObject',
        'CalculationObject',
        'WebForm',
        'PageObject',
        'ElementObject',
        'QuestionObject',
        'DescriptorObject',
        'EventObject',
        'WidgetConfigurationObject',
        'AudioSourceObject',
        'ParameterCollectionObject',
        'ParameterObject',
        'LocalizedStringObject',
        )


class DefinitionSpecification(collections.OrderedDict):
    props = collections.OrderedDict()
    """
    props == {(key, type), ...}
    """
    def __init__(self, props={}, **kwargs):
        """
        if ``self.props`` has items, filter out any keys
        in  ``props`` and ``kwargs`` not in self.props;
        otherwise initialize from props and/or kwargs.
        """
        super(DefinitionSpecification, self).__init__()
        self.update({k: v() for k, v in self.props.items()})
        self.update({
                k: v
                for k, v in props.items()
                if not self.props or k in self.props})
        self.update({
                k: v
                for k, v in kwargs.items()
                if not self.props or k in self.props})

    def clean(self):
        """Removes "empty" items from self.
        items whose values are empty arrays, dicts, and strings
        are deleted.

        All arrays are assumed to be arrays of DefinitionSpecification.
        """
        for k, v in self.items():
            if v not in [False, 0, 0.0, None]:
                if bool(v):
                    if isinstance(v, DefinitionSpecification):
                        v.clean()
                    elif isinstance(v, list):
                        v = [x for x in v if x.clean()]
                    if not bool(v):
                        del self[k]
                else:
                    del self[k]
        return self

    def as_dict(self):
        out = dict()

        for key, value in self.items():
            if isinstance(value, DefinitionSpecification):
                out[key] = value.as_dict()
            elif isinstance(value, (list, tuple)):
                out[key] = []
                for v in value:
                    if isinstance(v, DefinitionSpecification):
                        out[key].append(v.as_dict())
                    else:
                        out[key] = v
            else:
                out[key] = value

        return out


class AudioSourceObject(DefinitionSpecification):
    pass


class EnumerationCollectionObject(DefinitionSpecification):
    def add(self, name, description=''):
        self[name] = (
                EnumerationObject(description=description)
                if description
                else None)


class LocalizedStringObject(DefinitionSpecification):
    pass


class ParameterCollectionObject(DefinitionSpecification):
    pass


class TypeCollectionObject(DefinitionSpecification):
    pass


class Instrument(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', str),
            ('version', str),
            ('title', str),
            ('description', str),
            ('types', TypeCollectionObject),
            ('record', list),
            ])

    def add_field(self, field_object):
        assert isinstance(field_object, FieldObject), field_object
        self['record'].append(field_object)

    def add_type(self, type_name, type_object):
        assert isinstance(type_name, str), type_name
        assert isinstance(type_object, TypeObject), type_object
        self['types'][type_name] = type_object


class FieldObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', str),
            ('description', str),
            ('type', str),
            ('required', bool),
            ('annotation', str),
            ('explanation', str),
            ('identifiable', bool),
            ])


class BoundConstraintObject(DefinitionSpecification):
    """Must have at least one of ['max', 'min']
    """
    props = collections.OrderedDict([
            ('min', str),
            ('max', str),
            ])


class TypeObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('base', str),
            ('range', BoundConstraintObject),
            ('length', BoundConstraintObject),
            ('pattern', str),
            ('enumerations', EnumerationCollectionObject),
            ('record', list),
            ('columns', list),
            ('rows', list),
            ])

    def add_column(self, column_object):
        assert isinstance(column_object, ColumnObject), column_object
        self['columns'].append(column_object)

    def add_enumeration(self, name, description=''):
        self['enumerations'].add(name, description)

    def add_field(self, field_object):
        assert isinstance(field_object, FieldObject), field_object
        self['record'].append(field_object)

    def add_row(self, row_object):
        assert isinstance(row_object, RowObject), row_object
        self['rows'].append(row_object)


class ColumnObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', str),
            ('description', str),
            ('type', str),
            ('required', bool),
            ('identifiable', bool),
            ])


class RowObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', str),
            ('description', str),
            ('required', bool),
            ])


class EnumerationObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('description', str),
            ])


class InstrumentReferenceObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', str),
            ('version', str),
            ])


class CalculationSetObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('instrument', InstrumentReferenceObject),
            ('calculations', list),
            ])

    def add(self, calc_object):
        assert isinstance(calc_object, CalculationObject), calc_object
        self['calculations'].append(calc_object)


class CalculationObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', str),
            ('description', str),
            ('type', str),
            ('method', str),
            ('options', DefinitionSpecification),
            ])


class WebForm(DefinitionSpecification):
    props = collections.OrderedDict([
            ('instrument', InstrumentReferenceObject),
            ('defaultLocalization', str),
            ('title', str),
            ('pages', list),
            ('parameters', DefinitionSpecification),
            ])

    def add_page(self, page_object):
        assert isinstance(page_object, PageObject), page_object
        self['pages'].append(page_object)

    def add_parameter(self, parameter_name, parameter_object):
        assert isinstance(parameter_name, str), parameter_name
        assert isinstance(parameter_object, ParameterObject), parameter_object
        self['parameters'][parameter_name] = parameter_object


class PageObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', str),
            ('elements', list),
            ])

    def add_element(self, element_object):
        element_list = (
                element_object
                if isinstance(element_object, list)
                else [element_object])
        for element in element_list:
            assert isinstance(element, ElementObject), element
            self['elements'].append(element)


class ElementObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('type', str),
            ('options', DefinitionSpecification),
            ('tags', list),
            ])


class WidgetConfigurationObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('type', str),
            ('options', DefinitionSpecification),
            ])


class QuestionObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('fieldId', str),
            ('text', LocalizedStringObject),
            ('audio', AudioSourceObject),
            ('help', LocalizedStringObject),
            ('error', LocalizedStringObject),
            ('enumerations', list),
            ('questions', list),
            ('rows', list),
            ('widget', WidgetConfigurationObject),
            ('events', list),
            ])

    def add_enumeration(self, descriptor_object):
        assert isinstance(
                descriptor_object,
                DescriptorObject), descriptor_object
        self['enumerations'].append(descriptor_object)

    def add_question(self, question_object):
        assert isinstance(question_object, QuestionObject), question_object
        self['questions'].append(question_object)

    def add_row(self, descriptor_object):
        assert isinstance(
                descriptor_object,
                DescriptorObject), descriptor_object
        self['rows'].append(descriptor_object)

    def add_event(self, event_object):
        assert isinstance(event_object, EventObject), event_object
        self['events'].append(event_object)

    def set_widget(self, widget):
        assert isinstance(widget, WidgetConfigurationObject), widget
        self['widget'] = widget


class DescriptorObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', str),
            ('text', LocalizedStringObject),
            ('audio', AudioSourceObject),
            ('help', LocalizedStringObject),
            ])


class EventObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('trigger', str),
            ('action', str),
            ('targets', list),
            ('options', DefinitionSpecification),
            ])


class ParameterObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('type', str),
            ])
