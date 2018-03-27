django-actrack - changes
========================


v0.4 (28-03-2018)
-----------------

- Django 2.0 support
- drop django 1.8 support
- documentation is on readthedocs
- fix group classmethod


v0.3 (30-10-2016)
-----------------

- use of a buffer to combine actions according to user-defined rules
- use of a deleted items buffer

v0.3.1 (03-11-2016)
...................

- grouping only occurs at save time

v0.3.2 (04-11-2016)
...................

- add grouping customization via action handler methods

v0.3.3 (08-12-2016)
...................

- fix db selection via 'using' keyword
- combine_with_* methods now require the kwargs from the 2 actions

v0.3.4 (20-12-2016)
...................

- fix combine_with using targets inclusion rather than equality
- add 'inherit' option for group method

v0.3.5 (17-02-2017)
...................

- add 'get_del_item' function to enable logging during deletion
- add 'DeletedItems.registry.remove' to enable cleanup of DeletedItems

v0.3.6 (29-03-2017)
...................

- allow undefined actor on action creation

v0.3.7 (22-05-2017)
...................

- django 1.11 compatibility
- fix database router call in actrack.track

v0.3.8 (19-07-2017)
...................

- deletion management fix

v0.3.9 (19-10-2017)
...................

- reverse 1to1 descriptor getter fix (db)
- improve tracker performance


v0.2b (18-10-2016)
------------------

- adds log level
- bug fixes


v0.1b (24-09-2015)
------------------

- multi-db support
- migrations support
- base features


v0.0 (11-08-2014)
-----------------

- Birth
