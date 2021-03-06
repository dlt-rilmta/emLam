#!/usr/bin/env python3
"""An instantiable component. See the docstring for the class."""

from __future__ import absolute_import, division, print_function
from future.utils import with_metaclass
import logging
import inspect


class NamedClass(type):
    """
    A read-only name property for classes. See
    http://stackoverflow.com/questions/3203286/how-to-create-a-read-only-class-property-in-python
    """
    @property
    def name(cls):
        return getattr(cls, 'NAME', None)

    @property
    def description(cls):
        return getattr(cls, 'DESCRIPTION', None)

class Component(with_metaclass(NamedClass, object)):
    """
    Base class for corpus and preprocessor objects. All corpus and preprocessor
    classes must be subclasses of Component. Also, multiple inheritence is
    discouraged, as it may break some parts of the code.
    """
    def __init__(self):
        self.logger = logging.getLogger(inspect.getmodule(self).__name__)
        self.logger.setLevel(self.logger.parent.level)

    @classmethod
    def instantiate(cls, process_id=0, **kwargs):
        """
        Instantiates the class from keyword arguments. The process_id (not a
        real pid, but an ordinal starting from 0) is there so that components
        that use external resources can "plan" accordingly.
        """
        argspec = inspect.getargspec(cls.__init__).args
        component_args = {k: kwargs[k] for k in argspec[1:] if k in kwargs}
        logging.getLogger(cls.__module__).debug(
            'Instantiating with parameters {}'.format(component_args))
        return cls(**component_args)
