from typing import List, Tuple, Optional, Union, Dict
from collections import Counter
import errant
from tqdm import tqdm
from .utils import apply_edits


class Edit(errant.edit.Edit):
    """Wrap class for initialization that does not require a spacy object."""

    def __init__(
        self, o_start, o_end, o_str, c_str, c_start=None, c_end=None, type="NA"
    ):
        self.o_start = o_start
        self.o_end = o_end
        self.o_str = o_str
        self.o_toks = self.o_str.split(" ")
        self.c_start = c_start
        self.c_end = c_end
        self.c_str = c_str
        self.c_toks = self.c_str.split(" ")
        self.type = type


class Parallel:
    def __init__(
        self,
        m2: str = None,
        ref_id: int = 0,
        srcs: List[str] = None,
        trgs: List[str] = None,
    ):
        """Initialize a Parallel instance.

        Args:
            m2 (str): Path to a M2 file.
            ref_id (int): Reference ID.
            srcs (list[str]): Source sentences.
            trgs (list[str]): Target sentences.
        """
        self.srcs, self.trgs, self.edits_list = None, None, None
        self.GED_MODES = ["bin", "cat1", "cat2", "cat3"]
        if m2 is not None:
            self.srcs, self.trgs, self.edits_list = self.load_m2(m2, ref_id)
        elif srcs is not None and trgs is not None:
            self.srcs, self.trgs, self.edits_list = self.load_parallel(srcs, trgs)

        assert self.srcs is not None and self.edits_list is not None

    @classmethod
    def from_m2(cls, m2: str, ref_id: int = 0) -> "Parallel":
        """Make a Parallel instance from a M2 file.

        Args:
            m2 (str): Path to a M2 file.
            ref_id (int): Reference id.

        Returns:
            Parallel: A Parallel instance.

        """
        m2 = open(m2).read().rstrip().split("\n\n")
        return cls(m2=m2, ref_id=ref_id)

    @classmethod
    def from_demo(cls) -> "Parallel":
        """Load demo data and make a Parallel instance.

        Returns:
            Parallel: Parallel instance.

        """

        # Cited ERRANT official page for the following example.
        # https://github.com/chrisjbryant/errant
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
        return cls(m2=m2)

    @classmethod
    def from_parallel(cls, src: str, trg: str) -> "Parallel":
        """Make a Parallel instance from raw files.

        Args:
            src (str): Path to source file.
            trg (str): Path to target file.

        Returns:
            Parallel: The Parallel instance.
        """
        srcs = open(src).read().rstrip().split("\n")
        trgs = open(trg).read().rstrip().split("\n")
        return cls(srcs=srcs, trgs=trgs)

    def load_m2(
        self, m2_contents: List[str], ref_id: int = 0
    ) -> Tuple[List[str], List[str], List[List[Edit]]]:
        """Make a Parallel instance from m2 contents (not a file path).

        Args:
            m2_contents (list[str]): M2 contents after splitting "\n\n".
            ref_id (int): Reference id.

        Returns:
            Tuple containing
                - srcs (list[str]): The source sentences.
                - trgs (list[str]): The target sentences.
                - edits_list (list[list[errant.edit.Edit]]):
                    The edits extracted from each parallel pair.
        """

        srcs: List[str] = []
        trgs: List[str] = []
        edits_list: List[List[errant.edit.Edit]] = []
        num_error_sent = 0
        num_words = 0
        num_edits = 0
        num_corrected_token = 0
        for content in m2_contents:
            src, *edits = content.split("\n")
            src = src[2:]  # remove 'S '
            edits = [
                self.make_edit_instance(src, e[2:])
                for e in edits
                if e.split("|||")[1] not in ["noop", "UNK"]
                and int(e.split("|||")[-1]) == ref_id
            ]
            srcs.append(src)
            trgs.append(apply_edits(src, edits))
            edits_list.append(edits)
            num_words += len(src.split(" "))
            num_edits += len(edits)
            num_corrected_token += sum(e.o_end - e.o_start for e in edits)
            if len(edits) > 0:
                num_error_sent += 1
        self.num_sents = len(srcs)
        self.num_error_sent = num_error_sent
        self.num_words = num_words
        self.num_edits = num_edits
        self.num_corrected_token = num_corrected_token
        return srcs, trgs, edits_list

    @staticmethod
    def make_edit_instance(src, editstr: str) -> Edit:
        """Make an Edit instance from an edit string of the M2 format,
            such as "S 0 1|||..."

        Args:
            editstr (str): The edit string of the M2 format.

        Returns:
            Edit: The Edit instance.
        """
        tokens = src.split(" ")
        pos, etype, c_str, *others = editstr.split("|||")
        start, end = map(int, pos.split(" "))
        return Edit(
            o_start=start,
            o_end=end,
            o_str=" ".join(tokens[start:end]),
            c_str=c_str,
            type=etype,
        )

    def load_parallel(
        self, srcs: List[str], trgs: List[str]
    ) -> Tuple[List[str], List[str], List[List[Edit]]]:
        """Make a Parallel instance from parallel sentences (not file paths).

        Args:
            srcs (list[str]): The source sentences.
            trgs (list[str]): The target sentences.

        Returns:
            Tuple containing
                - srcs (list[str]): The source sentences.
                - trgs (list[str]): The target sentences.
                - edits_list (list[list[errant.edit.Edit]]):
                    The edits extracted from each parallel pair.
        """
        annotator = errant.load("en")
        edits_list = []
        num_error_sent = 0
        num_words = 0
        num_edits = 0
        num_corrected_token = 0
        for src, trg in tqdm(zip(srcs, trgs), total=len(srcs)):
            orig = annotator.parse(src)
            cor = annotator.parse(trg)
            edits = annotator.annotate(orig, cor)
            edits_list.append(edits)
            num_words += len(src.split(" "))
            num_edits += len(edits)
            num_corrected_token += sum(e.o_end - e.o_start for e in edits)
            if len(edits) > 0:
                num_error_sent += 1
        self.num_sents = len(srcs)
        self.num_error_sent = num_error_sent
        self.num_words = num_words
        self.num_edits = num_edits
        self.num_corrected_token = num_corrected_token
        return srcs, trgs, edits_list

    def show_stats(self, cat3: bool = False) -> None:
        """Show statistics of the loaded dataset.

        Args:
            cat3 (bool): If True, the distributions of cat3 error type (e.g., R:NOUN) are also shown.
        """
        print("Number of sents:", self.num_sents)
        print("Number of words:", self.num_words)
        print("Number of edits:", self.num_edits)
        print("Number of error sents:", self.num_error_sent / self.num_sents)
        print("Word error rate:", self.num_corrected_token / self.num_words)
        print("=== Cat1 ===")
        self.show_etype_stats(cat=1)
        print("=== Cat2 ===")
        self.show_etype_stats(cat=2)
        if cat3:
            print("=== Cat3 ===")
            self.show_etype_stats(cat=3)

    def show_etype_stats(self, cat: int = 2) -> None:
        """Show the distribution of error type.

        Args:
            cat (int): The category of the error type.
                - 1: M, R, and U.
                - 2: NOUN, VERB:FORM, etc.
                - 3 (other than 1 and 2): M:NOUN, R:VERB:FORM, etc.
        """

        def show(cat, num_edits):
            cat2freq = Counter(cat)
            print(f'{"Error type":10} {"Freq":6} Ratio')
            for k in sorted(cat2freq.keys()):
                print(f"{k:10} {cat2freq[k]:6} {cat2freq[k]/num_edits*100:.2f}")

        num_edits = 0
        cat1 = []
        cat2 = []
        cat3 = []
        for edits in self.edits_list:
            for e in edits:
                num_edits += 1
                cat1.append(e.type[0])
                cat2.append(e.type[2:])
                cat3.append(e.type)
        if cat == 1:
            show(cat1, num_edits)
        elif cat == 2:
            show(cat2, num_edits)
        else:
            show(cat3, num_edits)

    def n_edits_distribution(self) -> Tuple:
        """Calculate the distributoin of number of edits.

        Returns:
            dict[int, int]: The dictionary contains {num_edits: frequency}.
        """
        n_errors = [len(edits) for edits in self.edits_list]
        n_error_to_freq = Counter(n_errors)
        return sorted(n_error_to_freq.items(), key=lambda x: x[0])

    def convert_etype(self, etype, cat=1) -> str:
        """Convert error type into specific format.

        Args:
            etype (str): Error type.
            cat: Category of the error type.
                - 1: M, R, and U.
                - 2: NOUN, VERB:FORM, etc.
                - 3 (other than 1 and 2): M:NOUN, R:VERB:FORM, etc.

        Returns:
            str: The error type string.
        """
        # cat=1, M, R, U
        # cat=2, e.g. DET, NOUN:NUM
        # cat=3, M:DET, R:NOUN:NUM
        if cat == 1:
            return etype[0]
        elif cat == 2:
            return etype[2:]
        else:
            return etype

    def ged_labels_sent(
        self, mode: str = "bin", return_id: bool = False
    ) -> List[List[Union[str, int]]]:
        """Generate error detection label at sentence level for the loaded parallel data.

        Args:
            mode (str): Error type category including binary setting.
                - "bin": CORRECT or INCORRECT.
                - "cat1": CORRECT, M, R, and U.
                - "cat2": CORRECT, NOUN, VERB:FORM, etc.
                - "cat3": CORRECT, M:NOUN, R:VERB:FORM, etc.

            return_id(bool): If true, the label is converted into integer.

        Returns:
            list[list[Union[str, int]]]: Sentence-level detection labels.
                Int If return_id is True, otherwise str.
        """
        assert mode in self.GED_MODES
        labels = []
        label2id = self.get_ged_label2id(mode=mode)
        for s, t, edits in zip(self.srcs, self.trgs, self.edits_list):
            if s == t:
                label = ["CORRECT"]
            else:
                if mode == "bin":
                    label = ["INCORRECT"]
                else:
                    cat = int(mode[-1])
                    label = list(set(self.convert_etype(e.type, cat) for e in edits))
            if return_id:
                label = [label2id[l] for l in label]
            labels.append(label)
        assert len(labels) == len(self.srcs)
        return labels

    def ged_labels_token(
        self, mode: str = "bin", return_id: bool = False
    ) -> List[List[Union[str, int]]]:
        """Generate error detection label at token level for the loaded parallel data.

        Args:
            mode (str): Error type category including binary setting.
                - "bin": CORRECT or INCORRECT.
                - "cat1": CORRECT, M, R, and U.
                - "cat2": CORRECT, NOUN, VERB:FORM, etc.
                - "cat3": CORRECT, M:NOUN, R:VERB:FORM, etc.

            return_id(bool): If true, the label is converted into integer.

        Returns:
            list[list[Union[str, int]]]: Token-level detection labels.
                Int If return_id is True, otherwise str.
        """
        assert mode in self.GED_MODES
        labels = []
        label2id = self.get_ged_label2id(mode=mode)
        for s, edits in zip(self.srcs, self.edits_list):
            label = ["CORRECT"] * len(s.split(" "))
            for e in edits:
                st = e.o_start
                en = e.o_end
                if e.o_start == e.o_end:
                    # If missing error, we assign an incorrect label to the token on the right of the span.
                    # This follows [Yuan+ 21]'s strategy (Sec. 4.2): https://aclanthology.org/2021.emnlp-main.687.pdf
                    st = e.o_end
                    en = e.o_end + 1
                if mode == "bin":
                    label[st:en] = ["INCORRECT"] * (en - st)
                else:
                    cat = int(mode[-1])
                    t = self.convert_etype(e.type, cat)
                    label[st:en] = [t] * (en - st)
            if return_id:
                label = [label2id[l] for l in label]
            labels.append(label)
        assert len(labels) == len(self.srcs)
        return labels

    def get_ged_id2label(self, mode: str = "bin") -> Dict[int, str]:
        """Get relationship between error types and their ids.

        Args:
            mode (str): Category of the error type.
                - "bin": CORRECT or INCORRECT.
                - "cat1": CORRECT, M, R, and U.
                - "cat2": CORRECT, NOUN, VERB:FORM, etc.
                - "cat3": CORRECT, M:NOUN, R:VERB:FORM, etc.

        Returns:
            dict[int, str]: The dictionary of {id: error type}.
        """
        mru_cats = [
            "ADJ",
            "ADV",
            "CONJ",
            "CONTR",
            "DET",
            "NOUN",
            "NOUN:POSS",
            "OTHER",
            "PART",
            "PREP",
            "PRON",
            "PUNCT",
            "VERB",
            "VERB:FORM",
            "VERB:TENSE",
        ]
        r_cats = [
            "ADJ:FORM",
            "MORPH",
            "NOUN:INFL",
            "NOUN:NUM",
            "ORTH",
            "SPELL",
            "VERB:INFL",
            "VERB:SVA",
            "WO",
        ]
        cat1 = {0: "CORRECT"}
        cat2 = {0: "CORRECT"}
        cat3 = {0: "CORRECT"}
        for i, c in enumerate("MRU"):
            cat1[i + 1] = c
        for i, c in enumerate(mru_cats + r_cats):
            cat2[i + 1] = c
        idx = 1
        for c1 in "MRU":
            for c2 in mru_cats:
                cat3[idx] = c1 + ":" + c2
                idx += 1
            if c1 == "R":
                for c2 in r_cats:
                    cat3[idx] = c1 + ":" + c2
                    idx += 1
        assert len(cat1) == 4
        assert len(cat2) == 25
        assert len(cat3) == 55

        if mode == "bin":
            return {0: "CORRECT", 1: "INCORRECT"}
        elif mode == "cat1":
            return cat1
        elif mode == "cat2":
            return cat2
        else:
            return cat3

    def get_ged_label2id(self, mode: str = "bin") -> Dict[str, int]:
        """Get relationship between error types and their ids.

        Args:
            mode (str): Category of the error type.
                - "bin": CORRECT or INCORRECT.
                - "cat1": CORRECT, M, R, and U.
                - "cat2": CORRECT, NOUN, VERB:FORM, etc.
                - "cat3": CORRECT, M:NOUN, R:VERB:FORM, etc.

        Returns:
            dict[str, int]: The dictionary of {id: error type}.
        """
        id2label = self.get_ged_id2label(mode)
        return {v: k for k, v in id2label.items()}
