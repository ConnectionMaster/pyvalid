# cpennello 2015-08-11

'''Utilities for validation system.'''

# cpennello 2014-08-21 From cr.util.
def kooljoin(word, seq):
  '''Comma-join sequence of strings, inserting word before the final
  sequence element if there are more than two elements.  Omit commas and
  uses only the word to join the sequence elements if there are fewer
  than three elements.
  '''

  word += ' '
  if len(seq) < 3: return (' ' + word).join(seq)
  seq = list(seq)
  seq[-1] = word + seq[-1]
  return ', '.join(seq)
