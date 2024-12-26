from .cached_errant import CachedERRANT
import pytest

cases = [
    (
        "This is sample sentece . dummy",
        "This is a sample sentence .",
        [(2, 2, "a"), (3, 4, "sentence"), (5, 6, "")],
    )
]


class TestCachedERRANT:
    @pytest.fixture(scope="class")
    def cached_errant(self):
        return CachedERRANT()

    @pytest.mark.parametrize("src,trg,gold_edits", cases)
    def test_forward(self, cached_errant, src, trg, gold_edits):
        edits = cached_errant.extract_edits(src, trg)
        for edit_id in range(len(edits)):
            hyp_edit = (
                edits[edit_id].o_start,
                edits[edit_id].o_end,
                edits[edit_id].c_str,
            )
            assert hyp_edit == gold_edits[edit_id]
