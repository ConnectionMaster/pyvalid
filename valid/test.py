# cpennello 2014-08-21

'''Tests for validation system.'''

import unittest

from . import validate, types

# It's easier to test error messages by looking at them.
show_errors = False

class SingleDictTest(unittest.TestCase):
  # expects class attributes type and data

  def failtest(self, k, v):
    data = self.data.copy()
    data[k] = v
    try:
      validate(self.type, data)
      er = False
    except types.Error, e:
      er = e.format()
    assert er
    if show_errors: print er

  def validate(self, data): return validate(self.type, data)

  def tearDown(self):
    del self.type, self.data

class TestBasic(SingleDictTest):
  def setUp(self):
    class TestDict(types.Dict):
      a = types.Str(10)
      b = types.Str(5, 10)
      c = types.Str(5), types.fromtype
    self.type = TestDict
    self.data = dict(a='hello', b='123456', c='abc')

  def test_basic(self):
    v = self.validate(self.data)
    assert v
    assert isinstance(v, dict)
    assert all(isinstance(x, str) for x in v.itervalues())

  def test_longstring(self):
    self.failtest('a', 'hello' * 3)

  def test_shortstring(self):
    self.failtest('b', '')

class TestUnicode(SingleDictTest):
  def setUp(self):
    class TestUnicodeDict(types.Dict):
      a = types.Str(10)
      b = types.Unicode(10)
    self.type = TestUnicodeDict
    self.data = dict(a='hello', b=u'\u1234')

  def test_basic(self):
    v = self.validate(self.data)
    assert v
    assert isinstance(v, dict)
    assert isinstance(v['a'], str)
    assert isinstance(v['b'], unicode)

  def test_badunicode(self):
    self.failtest('b', '\xff')

  def test_badstr(self):
    self.failtest('a', u'\u1234')

# basic comprehensive test of non-str scalar types
class TestTypes(SingleDictTest):
  def setUp(self):
    class TestDict(types.Dict):
      i = types.Int()
      f = types.Float()
      bi = types.BoundedInt(1, 20)
      bf = types.BoundedFloat(1.3, 2.4)
      b = types.Bool()
      e = types.Enum(('a', 'b', 'c'))
    self.type = TestDict
    self.data = dict(
      i='42', f='2.71828', bi='15', bf='1.41421', b='true', e='b')

  def test_basic(self):
    v = self.validate(self.data)
    assert v
    assert v['i'] == 42
    assert v['f'] == 2.71828
    assert v['bi'] == 15
    assert v['bf'] == 1.41421
    assert v['b'] is True
    assert v['e'] == 'b'
    assert isinstance(v, dict)

  def test_bad(self):
    self.failtest('i', 'fgsfds')
    self.failtest('f', '2.x')
    self.failtest('bi', '0')
    self.failtest('bf', '1.1')
    self.failtest('e', 'x')

class TestSub(SingleDictTest):
  def setUp(self):
    class TestDict(types.Dict):
      i = types.Int()
      f = types.Float()
      bi = types.BoundedInt(1, 20)
      bf = types.BoundedFloat(1.3, 2.4)
      b = types.Bool()
      e = types.Enum(('a', 'b', 'c'))
    class SubTestDict(TestDict):
      zuul = types.Str(7, 9)
    self.type = SubTestDict
    self.data = dict(
      i='42', f='2.71828', bi='15', bf='1.41421', b='true', e='b')

  def test_fail(self):
    self.failtest('zuul', 'x')

class TestDefault(SingleDictTest):
  def setUp(self):
    class DefaultDictTest(types.Dict):
      a = types.Str(10), 'yeah'
      b = types.Str(10), types.fromtype
    self.type = DefaultDictTest
    self.data = {}

  def test_basic(self):
    v = self.validate(self.data)
    assert v
    assert v['a'] == 'yeah'
    assert v['b'] == ''

class TestSubDefault(SingleDictTest):
  def setUp(self):
    class DefaultDictTest(types.Dict):
      a = types.Str(10), 'yeah'
      b = types.Str(10), types.fromtype

    class TestDict(types.Dict):
      x = types.Str(10)

    class XDict(DefaultDictTest, TestDict):
      a = types.Str(10), 'ooh'
      c = types.Str(10)
    self.type = XDict
    self.data = dict(c='', x='')

  def test_basic(self):
    v = self.validate(dict(c='', x=''))
    assert v
    assert v['a'] == 'ooh'

class TestSeq(unittest.TestCase):
  def test_list(self):
    v = validate(types.List(types.Int()), ['1', '2'])
    assert v
    assert isinstance(v, list)
    assert all(isinstance(x, int) for x in v)

  def test_tuple(self):
    v = validate(types.Tuple(types.Int()), ('1', '2'))
    assert v
    assert isinstance(v, tuple)
    assert all(isinstance(x, int) for x in v)

  def test_list2(self):
    try:
      validate(types.List(types.Int()), ['1', 'foo'])
      er = False
    except types.Error, e:
      er = e.format()
    assert er
    if show_errors: print er

  def test_list3(self):
    try:
      validate(types.List(types.Int(), 1), [1, 2])
      er = False
    except types.Error, e:
      er = e.format()
    assert er
    if show_errors: print er

class TestSubDict(unittest.TestCase):
  def test_basic(self):
    class TestDict(types.Dict):
      x = types.Str(10)

    class SubDictTest(types.Dict):
      sub = TestDict

    v = validate(SubDictTest, dict(sub=dict(x='hello')))
    assert v
    assert v['sub']
    assert v['sub']['x'] == 'hello'

  def test_fail(self):
    class TestDict(types.Dict):
      x = types.Str(10)

    class SubErrorTest(types.Dict):
      sublist = types.List(types.Int())
      sub = TestDict
      sublist2 = types.List(TestDict)
    try:
      validate(SubErrorTest,
        dict(sub={}, sublist=[1, 2, 3, 'a'], sublist2=[{}]))
      er = False
    except types.Error, e:
      er = e.format()
    assert er
    if show_errors: print er

class TestNesting(unittest.TestCase):
  def test_basic(self):
    class NestTest3(types.Dict):
      x = types.Int()
    class NestTest2(types.Dict):
      y = NestTest3
    class NestTest1(types.Dict):
      z = NestTest2
    try:
      validate(NestTest1, dict(z=dict(y=dict(x='asdf'))))
      er = False
    except types.Error, e:
      er = e.format()
    assert er
    if show_errors: print er

class TestOptional(unittest.TestCase):
  def test_simple(self):
    class Dict(types.Dict):
      a = types.Int()
      b = types.Int()
    data = validate(Dict, {}, optional=True)
    assert not data
    data = validate(Dict, dict(a=1), optional=True)
    assert data == dict(a=1)

  def test_sub(self):
    class SubDict(types.Dict):
      a = types.Int()
    class Dict(types.Dict):
      a = types.Int()
      b = SubDict
    data = validate(Dict, {}, optional=True)
    assert not data
    data = validate(Dict, dict(b={}), optional=True)
    assert data == dict(b={})
    data = validate(Dict, dict(a=1), optional=True)
    assert data == dict(a=1)
    data = validate(Dict, dict(a=1, b=dict(a=3)), optional=True)
    assert data == dict(a=1, b=dict(a=3))

unittest.main()
