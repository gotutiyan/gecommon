from .utils import apply_edits
from .parallel import Parallel
import pytest

cases_parallel = [
    ("This is sample sentece . dummy", "This is a sample sentence ."),
    ("This is sample sentece . dummy", "This is sample sentece . dummy"),
]


class TestParallel:
    @pytest.mark.parametrize("src,trg", cases_parallel)
    def test_parallel(self, src, trg):
        gec = Parallel(srcs=[src], trgs=[trg])
        assert apply_edits(src, gec.edits_list[0]) == trg
