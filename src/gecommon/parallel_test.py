from .parallel import Parallel, Edit
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
    @pytest.fixture(scope="class")
    def demo_instance(self):
        m2 = """S This are gramamtical sentence .
A 1 2|||R:VERB:SVA|||is|||REQUIRED|||-NONE-|||0
A 2 2|||M:DET|||a|||REQUIRED|||-NONE-|||0
A 2 3|||R:SPELL|||grammatical|||REQUIRED|||-NONE-|||0

S This is are a gram matical sentence .
A 2 3|||U:VERB||||||REQUIRED|||-NONE-|||0
A 4 6|||R:ORTH|||grammatical|||REQUIRED|||-NONE-|||0

S This are gramamtical sentence .
A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||0

""".rstrip().split("\n\n")
        gec = Parallel(m2=m2, ref_id=0)
        return gec

    @pytest.mark.parametrize("src,trg,num_edits", cases_parallel)
    def test_parallel_init(self, src, trg, num_edits):
        gec = Parallel(srcs=[src], trgs=[trg])
        assert len(gec.edits_list) == 1
        assert len(gec.edits_list[0]) == num_edits

    def test_m2_init(self, demo_instance):
        def compare_edit_sequence(edits1, edits2):
            for e1, e2 in zip(edits1, edits2):
                assert e1.o_start == e2.o_start
                assert e1.o_end == e2.o_end
                assert e1.c_str == e2.c_str
                assert e1.type == e2.type

        assert demo_instance.srcs == [
            "This are gramamtical sentence .",
            "This is are a gram matical sentence .",
            "This are gramamtical sentence .",
        ]
        assert demo_instance.trgs == [
            "This is a grammatical sentence .",
            "This is a grammatical sentence .",
            "This are gramamtical sentence .",
        ]
        compare_edit_sequence(
            demo_instance.edits_list[0],
            [
                Edit(1, 2, "are", "is", type="R:VERB:SVA"),
                Edit(2, 2, "", "a", type="M:DET"),
                Edit(2, 3, "gramamtical", "grammatical", type="R:SPELL"),
            ],
        )
        compare_edit_sequence(
            demo_instance.edits_list[1],
            [
                Edit(2, 3, "are", "", type="U:VERB"),
                Edit(4, 6, "gram matical", "grammatical", type="R:ORTH"),
            ],
        )
        assert demo_instance.edits_list[2] == []

    @pytest.mark.parametrize("src,trg,mode,slabel,tlabel", cases_ged)
    def test_ged_label(self, src, trg, mode, slabel, tlabel):
        gec = Parallel(srcs=[src], trgs=[trg])
        assert set(gec.ged_labels_sent(mode=mode)[0]) == set(slabel)
        assert gec.ged_labels_token(mode=mode)[0] == tlabel
        assert len(gec.get_ged_id2label(mode="bin")) == 2
        assert len(gec.get_ged_id2label(mode="cat1")) == 4
        assert len(gec.get_ged_id2label(mode="cat2")) == 25
        assert len(gec.get_ged_id2label(mode="cat3")) == 55

    def test_n_edit_dist(self, demo_instance):
        assert demo_instance.n_edits_distribution() == [(0, 1), (2, 1), (3, 1)]

    def test_convert_etype(self, demo_instance):
        etype = "R:VERB:INFL"
        assert demo_instance.convert_etype(etype, cat=1) == "R"
        assert demo_instance.convert_etype(etype, cat=2) == "VERB:INFL"
        assert demo_instance.convert_etype(etype, cat=3) == "R:VERB:INFL"

    def test_others(self):
        """Just check no errors."""
        gec = Parallel.from_demo()
        gec.show_stats()
        gec.show_etype_stats(cat=1)
        gec.show_etype_stats(cat=2)
        gec.show_etype_stats(cat=3)
