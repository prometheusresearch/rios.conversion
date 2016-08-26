#
# Copyright (c) 2016, Prometheus Research, LLC
#


import collections


from rios.conversion import structures


class InstrumentCalcStorage(collections.MutableMapping):
    """
    Storage for instrument and calculation objects.

    Object is of default form {'i': [], 'c': []}. The 'i' key corresponds to 
    instrument field objects only of the Instrument class. The 'c' key
    corresponds to calculation objects only of the CalculationObject class.
    This is to ensure that the values are only lists of either instrument field
    objects or calculation objects. Allowable keys are only those defined
    in __keys.
    """

    __keys = ('i', 'c',)
    __default = {}.fromkeys(__keys, list())

    def __init__(self):
        self.__dict__.update(self.__default)

    def __setitem__(self, key, value):
        if key not in self.__keys:
            raise KeyError('Invalid key value')
        if key is 'i' and not issubclass(value, structures.Instrument):
            raise ValueError(
                'Value must be a subclass of Instrument'
            )
        if key is 'c' and not issubclass(value, structures.CalculationObject):
            raise ValueError(
                'Value must be a subclass of CalculationObject'
            )
        self.__dict__[key].append(value)

    def __getitem__(self, key):
        if key not in self.__keys:
            raise KeyError('Invalid key value')
        return self.__dict__[key]

    def __delitem__(self, key):
        if key not in self.__keys:
            raise KeyError('Invalid key value')
        self.__dict__[key] = list()

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def clear(self, key):
        if key not in self.__keys:
            raise KeyError('Invalid key value')
        self.__dict__.fromkeys(self.__keys, list())
