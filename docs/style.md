Style Guide
===========

Sean Kelleher
-------------

### Spacing

+ Tabs are 4 whitespace characters.
+ There should be 2 blank lines between top-level functions and classes, and 1
  between methods in classes.
+ When a list (parameter list or regular list) is placing one element per line,
  the first element should be on the line following the opening delimiter and
  indented by one tab. This allows for easier folding in vi than would be
  possible for lists where the elements are aligned with the opening delimiter.

### Comments and Docstrings

+ Docstrings should always be verbatim string literals. This will allow them to
  be extended to be multi-line comments without change.

### Expressions

+ If an expression is testing that a value is _inside_ a certain range, use the
  following syntax: `min_val <= val <= max_val` (changing the strictness of the
  comparison operators as necessary). An expression that is testing that a value
  is _outside_ a certain range, use the following syntax:
  `val < min_val or val > max_val` (changing the strictness of the comparison
  operators as necessary). These layouts take inspiration from the layout of
  mathematical ranges, and aim to make it obvious at a glance whether the value
  being tested should be inside or outside the given range.
