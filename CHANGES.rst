========================
django-actrack - changes
========================


v0.3 (30-10-2016)
=================

- use of a buffer to combine actions according to user-defined rules
- use of a deleted items buffer

v0.3.1 (03-11-2016)
-------------------

- grouping only occurs at save time

v0.3.2 (04-11-2016)
-------------------

- add grouping customization via action handler methods

v0.3.3 (08-12-2016)
-------------------

- fix db selection via 'using' keyword
- combine_with_* methods now require the kwargs from the 2 actions

v0.3.4 (20-12-2016)
-------------------

- fix combine_with using targets inclusion rather than equality
- add 'inherit' option for group method


v0.2
====

- adds log level
- bug fixes


v0.1
====

- multi-db support
- migrations support
- base features


v0.0 (11-08-2014)
=================

- Birth
