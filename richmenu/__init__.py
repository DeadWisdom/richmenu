import warnings

## It's okay, our corpus is very very tiny.
warnings.filterwarnings(
    "ignore",
    "Using slow pure-python SequenceMatcher. Install python-Levenshtein to remove this warning",
)

from .menu import Menu, QuitException
