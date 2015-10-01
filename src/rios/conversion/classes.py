"""
RIOS objects are all implemented as subclasses of OrderedDict.

A dict would suffice, but the OrderedDict output matches the order 
of the Rios on-line documentation at
http://rios.readthedocs.org/en/latest/index.html 
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
    def __init__(self, props={}, **kwargs):
        """
        if ``self.props`` has items, filter out any keys
        in  ``props`` and ``kwargs`` not in self.props;
        otherwise initialize from props and/or kwargs.
        """
        super(DefinitionSpecification, self).__init__()
        self.update(self.props)
        self.update({
                k: v 
                for k, v in props.items()  
                if not self.props or k in self.props})
        self.update({
                k: v 
                for k, v in kwargs.items() 
                if not self.props or k in self.props})

class AudioSourceObject(DefinitionSpecification):
    pass

class EnumerationCollectionObject(DefinitionSpecification):
    pass

class LocalizedStringObject(DefinitionSpecification):
    pass

class ParameterCollectionObject(DefinitionSpecification):
    pass

class TypeCollectionObject(DefinitionSpecification):
    pass

class Instrument(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', ''),
            ('version', ''),
            ('title', ''),
            ('description', ''),
            ('types', TypeCollectionObject()),
            ('record', []),
            ])
    def add_field(self, field_object):
        assert isinstance(field_object, FieldObject), field_object
        self.props['record'].append(field_object)
    
    def add_type(self, type_name, type_object):
        assert isinstance(type_name, str), type_name
        assert isinstance(type_object, TypeObject), type_object
        self.props['types'][type_name] = type_object

class FieldObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', ''),
            ('description', ''),
            ('type', ''),
            ('required', False),
            ('annotation', ''),
            ('explanation', ''),
            ('identifiable', False),
            ])

class BoundConstraintObject(DefinitionSpecification):
    """Must have at least one of ['max', 'min']
    """
    props = collections.OrderedDict([
            #('min', None),
            #('max', None),
            ])

class TypeObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('base', ''),
            ('range', BoundConstraintObject()),
            ('length', BoundConstraintObject()),
            ('pattern', ''),
            ('enumerations', EnumerationCollectionObject()),
            ('record', []),
            ('columns', []),
            ('rows', []),
            ])
    def add_column(self, column_object):
        assert isinstance(column_object, ColumnObject), column_object
        self.props['columns'].append(column_object)
        
    def add_enumeration(self, name, description=''):
        self.props['enumerations'][name] = EnumerationObject(
                description=description)

    def add_field(self, field_object):
        assert isinstance(field_object, FieldObject), field_object
        self.props['record'].append(field_object)

    def add_row(self, row_object):
        assert isinstance(row_object, RowObject), row_object
        self.props['rows'].append(row_object)

class ColumnObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', ''),
            ('description', ''),
            ('type', ''),
            ('required', False),
            ('identifiable', False),
            ])

class RowObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', ''),
            ('description', ''),
            ('required', False),
            ])

class EnumerationObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('description', ''),
            ])

class InstrumentReferenceObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', ''),
            ('version', ''),
            ])

class CalculationSetObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('instrument', InstrumentReferenceObject()),
            ('calculations', []),
            ])
    def add(self, calc_object):
        assert isinstance(calc_object, CalculationObject), calc_object
        self.props['calculations'].append(calc_object)

class CalculationObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', ''),
            ('description', ''),
            ('type', ''),
            ('method', ''),
            ('options', {}),
            ])

class WebForm(DefinitionSpecification):
    props = collections.OrderedDict([
            ('instrument', InstrumentReferenceObject()),
            ('defaultLocalization', ''),
            ('title', ''),
            ('pages', []),
            ('parameters', {}),
            ])
    def add_page(self, page_object):
        assert isinstance(page_object, PageObject), page_object
        self.props['pages'].append(page_object)
        
    def add_parameter(self, parameter_name, parameter_object):
        assert isinstance(parameter_name, str), parameter_name
        assert isinstance(parameter_object, ParameterObject), parameter_object
        self.props['parameters'][parameter_name] = parameter_object

class PageObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', ''),
            ('elements', []),
            ])
    def add_element(self, element_object):
        element_list = (
                element_object 
                if isinstance(element_object, list) 
                else [element_object])
        for element in element_list:
            assert isinstance(element, ElementObject), element
            self.props['elements'].append(element)

class ElementObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('type', ''),
            ('options', {}),
            ('tags', []),
            ])

class QuestionObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('fieldId', ''),
            ('text', LocalizedStringObject()),
            ('audio', AudioSourceObject()),
            ('help', LocalizedStringObject()),
            ('error', LocalizedStringObject()),
            ('enumerations', []),
            ('questions', []),
            ('rows', []),
            ('widget', WidgetConfigurationObject()),
            ('events', []),
            ])
    def add_enumeration(self, descriptor_object):
        assert isinstance(
                descriptor_object, 
                DescriptorObject), descriptor_object
        self.props['enumerations'].append(descriptor_object)

    #def add_question(
    #def add_row(
    # def add_event(

    def set_widget(self, widget):
        assert isinstance(widget, WidgetConfigurationObject), widget
        self.props['widget'] = widget
        
class DescriptorObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('id', ''),
            ('text', {}),
            ('audio', {}),
            ('help', {}),
            ])

class EventObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('trigger', ''),
            ('action', ''),
            ('targets', []),
            ('options', {}),
            ])

class WidgetConfigurationObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('type', ''),
            ('options', {}),
            ])

class ParameterObject(DefinitionSpecification):
    props = collections.OrderedDict([
            ('type', ''),
            ])


