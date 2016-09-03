#
# Copyright (c) 2016, Prometheus Research, LLC
#


import collections
import six


from rios.conversion.base import structures


__all__ = ('InstrumentCalcStorage',)


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

    __keys = {
        'i': structures.FieldObject,
        'c': structures.CalculationObject,
    }

    def __init__(self):
        self.__dict__ = self.__new_dict()

    def __setitem__(self, key, value):
        if key not in self.__keys:
            raise KeyError('Invalid key value')
        if not isinstance(value, self.__keys[key]):
            raise ValueError(
                'Value must be a subclass of ' + str(self.__keys[key])
            )
        self.__getitem__(key).append(value)

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

    def clear(self):
        self.__dict__ = self.__new_dict()

    def __new_dict(self):
        return dict((k, list(),) for k in six.iterkeys(self.__keys))
