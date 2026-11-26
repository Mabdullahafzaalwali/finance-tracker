"""Core logic for the Personal Finance Tracker.

This module holds every class, data structure, algorithm, calculation and the
CSV save/load code. It is the single place where data is validated.

Layer rule (FRD section 6.1): the core contains no print(), no input() and no
tkinter. The front ends (cli.py, gui.py) and the tests call the core; the core
never calls them.

Implementation is added on the feature/core branch.
"""
