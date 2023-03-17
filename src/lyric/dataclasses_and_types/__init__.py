# Python's import management leaves something to be desired. It's fairly easy - in a complex project - to structure
# code that provokes a circular import. I agree with this write-up:
# https://medium.com/@hamana.hadrien/so-you-got-a-circular-import-in-python-e9142fe10591
# which thinks calling circular import problems 'bad design' is silly.
#
# Regardless, LyricManager keeps these widely used type definitions in here so as to not trigger ...

from .lyric_align_task import LyricAlignTask
from .lyric_aligner_type import LyricAlignerType
from .lyric_fetcher_type import LyricFetcherType
from .lyric_payload import LyricPayload
from .lyric_validity import LyricValidity
#from .lyric_validity import ValidityNew