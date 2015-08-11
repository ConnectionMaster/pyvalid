Python type validation system.

Usage
-----
(This example usage is duplicated in `valid/__init__.py`.)

Example usage:

    from valid import validate, types

    # This will be a validated sub-object, used below.  Don't define
    # them as inner classes.
    class EncryptionDict(types.Dict):
      key = types.Str(128)
      iv = types.Str(8)

    class JobDict(types.Dict):
      # Specifying just a type means the field is required.
      jobid = types.Int()
      # Specifying a second item here provides a default value.
      encryption = EncryptionDict, None
      # The special value types.fromtype means the default will be
      # chosen automatically for the type.
      nodeblock = types.Bool(), types.fromtype
      destination = types.Str(256)
      # Lists must be all of the same type.
      languages = types.List(types.Str(4))
      # Fields in the input data not mentioned in the type dict will
      # not appear in the validated output.

    def handle_data(data):
      try:
        data = validate(JobDict, data)
      except types.Error, e:
        # Calling e.format returns a nice human-readable phrase
        # summarizing why the validation failed.
        log(e.format())
      else:
        # Data is now validated!

See the Pydoc documentation in the `types` module for more information
on specific types.

Documentation
-------------
See the `valid` package's Pydoc documentation.

Testing
-------
Run `python -m valid.test` to invoke the unit tests.
