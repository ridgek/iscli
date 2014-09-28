===============================
iscli - "Industry Standard" CLI
===============================

iscli is a Python framework for building complex command line interfaces.

The API is heavily inspired by the Flask web framework.

"Industry Standard CLI" is a phrase commonly heard in the network
equipment industry, when companies claim their products have a
similar CLI to the "IOS CLI" of the 800 pound gorilla.

This is yet another implementation of that CLI style.

The `linenoise <http://github.com/antirez/linenoise>`_ line editor
that powers iscli only supports modern UNIX systems, so iscli will not
work on Windows.

Features
========

- Command expansion and tab completion
- Nested command modes
- '?' key help

