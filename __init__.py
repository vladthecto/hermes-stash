"""Hermes Agent plugin entry point.

Imports happen inside ``register`` so the package can be imported on its own
(for example by test runners) without Hermes loading it.
"""


def register(ctx):
    from .plugin import register as _register

    _register(ctx)
