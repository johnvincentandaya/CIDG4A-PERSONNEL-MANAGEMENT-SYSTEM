"""
App package initializer.

Do not import `main` here to avoid circular imports when running
`uvicorn main:app` from the `backend` directory. Keeping this module
minimal ensures `app` package imports its submodules without pulling
in the top-level `main` module.
"""

__all__ = []
