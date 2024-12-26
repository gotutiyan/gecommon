from .parallel import Parallel
import pytest

cases_parallel = [
    ("This is sample sentece . dummy", "This is a sample sentence .", 3),
    ("This is sample sentece . dummy", "This is sample sentece . dummy", 0),
]

cases_ged = [
    (
        "This is sample sentece . dummy",
        "This is a sample sentence .",
        "bin",
        ["INCORRECT"],
        ["CORRECT", "CORRECT", "INCORRECT", "INCORRECT", "CORRECT", "INCORRECT"],
    ),
    (
        "This is sample sentece . dummy",
        "This is sample sentece . dummy",
        "bin",
        ["CORRECT"],
        ["CORRECT", "CORRECT", "CORRECT", "CORRECT", "CORRECT", "CORRECT"],
    ),
    (
        "This is sample sentece . dummy",
        "This is a sample sentence .",
        "cat1",
        ["M", "R", "U"],
        ["CORRECT", "CORRECT", "M", "R", "CORRECT", "U"],
    ),
    (
        "This is sample sentece . dummy",
        "This is a sample sentence .",
        "cat2",
        ["DET", "SPELL", "NOUN"],
        ["CORRECT", "CORRECT", "DET", "SPELL", "CORRECT", "NOUN"],
    ),
    (
        "This is sample sentece . dummy",
        "This is a sample sentence .",
        "cat3",
        ["M:DET", "R:SPELL", "U:NOUN"],
        ["CORRECT", "CORRECT", "M:DET", "R:SPELL", "CORRECT", "U:NOUN"],
    ),
]


class TestParallel:
    @pytest.mark.parametrize("src,trg,num_edits", cases_parallel)
    def test_parallel(self, src, trg, num_edits):
        gec = Parallel(srcs=[src], trgs=[trg])
        assert len(gec.edits_list) == 1
        assert len(gec.edits_list[0]) == num_edits
        assert gec.apply_edits(src, gec.edits_list[0]) == trg

    @pytest.mark.parametrize("src,trg,mode,slabel,tlabel", cases_ged)
    def test_ged_label(self, src, trg, mode, slabel, tlabel):
        gec = Parallel(srcs=[src], trgs=[trg])
        assert set(gec.ged_labels_sent(mode=mode)[0]) == set(slabel)
        assert gec.ged_labels_token(mode=mode)[0] == tlabel
