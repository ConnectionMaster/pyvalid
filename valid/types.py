# cpennello 2014-08-21

'''Library of types for validation system.

The module constant fromtype is a special token for indicating that the
default value of a field should use the default value from its type.  In
other words, it will call the default method on the type object.

Type classes here are slotted for two reasons.  (1) There are a lot of
objects in this libarary, and it's a minor performance gain.  More
importantly, though, (2) it makes the Pydoc documentation easier to
read.

Project authors are encouraged to subclass any of the classes in this
module and build their own application-specific ones as needed.
'''

from .util import kooljoin

fromtype = object()

class Error(Exception):
  '''Valid type error class.'''

  def __init__(self, *errors):
    '''Construct by passing one or more (path, msg) tuples as arguments.
    The message should summarize why validation failed, and the path
    should summarize at what location in validation the error was
    detected.  Generally, "scalar" errors (Int, Str, etc.) pass up an
    empty path, and "vector" errors (Dict, List, etc.) fill in and
    handle the path.

    For example, if there is an error checking an integer, the path
    would be '', and a good message to pass back up would be 'is not a
    valid integer'.

    These messages and paths will be joined together to form a readable
    error message.

    '''
    super(Error, self).__init__(*errors)
    self.errors = errors

  def format(self):
    '''Return human-readable phrase summarizing errors.'''
    ret = ()
    for path, msg in self.errors:
      path = path.lstrip('.')
      if not path: path = 'value'
      ret += '%s %s' % (path, msg),
    return kooljoin('and', ret)

class Base(object):
  '''Base is the base class for valid types (except Dict; see below).
  Implementers are expected to write a default method, which provides a
  default value for the type or leave it unimplemented, and let a
  NotImplementedError be thrown in the case that a default value does
  not make sense for the type.  The check method takes a value (often,
  but not necessarily, a string) and converts it to the desired type.

  If a conversion is not possible, an Error should be raised with one or
  more (path, msg) tuples.  The message should summarize why validation
  failed, and the path should summarize at what location in validation
  the error was detected.  Generally, "scalar" errors (Int, Str, etc.)
  pass up an empty path, and "vector" errors (Dict, List, etc.) fill in
  and handle the path.
  '''
  __slots__ = ()

  def _default(self): raise NotImplementedError()
  def _check(self, v, **kw): raise NotImplementedError()

class LenRange(Base):
  '''Provide one argument to give an upper bound only.'''

  __slots__ = 'word', 'range'

  def __init__(self, word, min, max=None):
    '''If you pass only min, it will be used as an upper bound
    instead.
    '''
    self.word = word
    if max is None: min, max = 0, min
    self.range = xrange(min, max + 1)

  def _check(self, v, **kw):
    try: x = len(v)
    except TypeError:
      raise Error(('', 'has no length defined'))
    if x not in self.range:
      min, max = self.range[0], self.range[-1]
      if min == max: s = 'exactly %s %s' % (min, self.word)
      if min: s = 'between %s and %s %s' % (min, max, self.word)
      else: s = 'no more than %s %s' % (max, self.word)
      raise Error(('', 'must be %s' % s))
    return v

class NumberBase(Base):
  '''Subclasses are expected to define a class attribute cls for the
  kind of number they represent.
  '''

  __slots__ = ()

  def _default(self): return self.cls()

  def _check(self, v, **kw):
    try: return self.cls(v)
    except ValueError:
      raise Error(('', 'is not a valid %s' % self.cls.__name__))

class Int(NumberBase):
  __slots__ = ()
  cls = int
class Float(NumberBase):
  __slots__ = ()
  cls = float

class BoundedNumber(NumberBase):
  __slots__ = 'valrange',

  def __init__(self, min, max):
    # We would use a LenRange, but min or max may be non-integral.
    self.valrange = min, max

  def _default(self): return self.valrange[0]

  def _check(self, v, **kw):
    v = super(BoundedNumber, self)._check(v, **kw)
    if not (self.valrange[0] <= v <= self.valrange[1]):
      raise Error(('', 'must be between %s and %s' %  self.valrange))
    return v

class BoundedInt(BoundedNumber):
  __slots__ = ()
  cls = int
class BoundedFloat(BoundedNumber):
  __slots__ = ()
  cls = float

class Bool(Base):
  '''Non-trivial Python values that are in the falsevalues set will
  check to False.
  '''

  __slots__ = ()

  falsevalues = frozenset((
    '0',
    'false',
    'no',
    'off',
  ))

  def _default(self): return False

  def _check(self, v, **kw):
    if not v or v.lower() in self.falsevalues: return False
    return True

class Enum(Base):
  __slots__ = 'items',

  def __init__(self, itr):
    '''Pass an iterable of items to use for the enumeration.'''
    self.items = tuple(itr)

  def _default(self): return self.items[0]

  def _check(self, v, **kw):
    if v not in self.items: raise Error(('', 'is not a valid value'))
    return v

class StrBase(Base):
  '''Subclasses are expected to define a class attribute cls for the
  kind of string they represent as well as a class attribute defchar for
  the default character to use in default string construction.
  '''

  __slots__ = 'lenrange',

  def __init__(self, min, max=None):
    '''If you pass a single value, it will be an upper bound.'''
    self.lenrange = LenRange('characters', min, max)

  def _default(self): return self.defchar * self.lenrange.range[0]

  def _check(self, v, **kw):
    v = self.lenrange._check(v, **kw)
    try: return self.cls(v)
    except (UnicodeEncodeError, UnicodeDecodeError):
      raise Error(('', 'is not a valid %s' % self.cls.__name__))

class Str(StrBase):
  __slots__ = ()
  cls = str
  defchar = '\x00'

class Unicode(StrBase):
  __slots__ = ()
  cls = unicode
  defchar = u'\x00'

class SeqBase(Base):
  '''Subclasses are expected to define a class attribute cls for the
  kind of sequence they represent.
  '''

  __slots__ = 'lenrange', 'type'

  def __init__(self, typ, min=None, max=None):
    '''If you pass only min, it will be used as a length upper bound.
    If you provide min None (the default), no length range checking will
    be performed.
    '''

    self.type = typ
    if min is None: self.lenrange = None
    else: self.lenrange = LenRange('elements', min, max)

  def _default(self): return self.cls()

  def _check(self, v, **kw):
    if not isinstance(v, self.cls):
      raise Error(('', 'is not a %s' % self.cls.__name__))

    if self.lenrange is not None:
      v = self.lenrange._check(v, **kw)
    ret = ()
    bad = ()
    for i, x in enumerate(v):
      try: ret += self.type._check(x, **kw),
      except Error, e:
        for path, msg in e.errors:
          bad += ('[%s]%s' % (i, path), msg),
    if bad: raise Error(*bad)
    return self.cls(ret)

class Tuple(SeqBase):
  __slots__ = ()
  cls = tuple
class List(SeqBase):
  __slots__ = ()
  cls = list

class DictType(type):
  '''Internal metaclass for Dict.'''

  def __init__(self, name, bases, dct):
    if '__metaclass__' in dct: return # Base class; ignore.
    t = set()
    # The types set stored with name _types so as not to collide with
    # class attributes users might use.
    for cls in bases:
      if hasattr(cls, '_types'): t.update(cls._types)
    # Since Dicts are special, specially handle them.
    def istype(typ): return isinstance(typ, (Base, DictType))
    for name, spec in dct.iteritems():
      if isinstance(spec, tuple) and istype(spec[0]):
        t.add(name)
      elif istype(spec):
        # Normalize all specs to be tuples.
        setattr(self, name, (spec,))
        t.add(name)
    self._types = t

class Dict(object):
  '''Dicts are a bit special.  Instead of creating instances of them
  like the other types, you use only classes.  Subclass Dict and specify
  class attributes whose values are equal to instances of other classes
  from the types module, or further Dict subclasses.  Then call
  validate, passing in your dict class (not an instance!) as the first
  argument, and the dictionary of data to validate as the second
  argument.

  Dicts support a keyword boolean 'optional' in the validate call that
  causes *all* fields to be treated as optional, even if not
  individually specified as such.
  '''

  __metaclass__ = DictType
  # No slots.

  def __init__(self):
    '''Don't call this; it will throw an error.  You are meant to use
    just Dict classes.
    '''
    raise TypeError("don't instantiate Dicts")

  @staticmethod
  def _default():
    '''Named _default so as not to collide with class attributes users
    might use.
    '''
    return {}

  @classmethod
  def _check(cls, v, **kw):
    '''Named _check so as not to collide with class attributes users
    might use.
    '''

    optional = kw.get('optional', False)

    if not isinstance(v, dict): raise Error(('', 'is not a dict'))

    ret = {}
    bad = ()

    for name in cls._types:
      spec = getattr(cls, name)

      if len(spec) == 2:
        opt = True
        default = spec[1]
      else:
        opt = False
      typ = spec[0]

      if name not in v:
        if not optional:
          if opt:
            if default is fromtype: ret[name] = typ._default()
            else: ret[name] = default
          else:
            bad += ('.' + name, 'is required'),
      else:
        try:
          ret[name] = typ._check(v[name], **kw)
        except Error, e:
          for path, msg in e.errors:
            bad += ('.' + name + path, msg),

    if bad: raise Error(*bad)
    return ret
