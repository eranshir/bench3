"""Filter expression language for the segmentation service.

A record is a plain dict. `evaluate` decides whether a record matches an
expression written by a non-engineer in the segment builder UI.
"""


def evaluate(expression, record):
    """Return True if `record` matches `expression`, else False."""
    raise NotImplementedError
