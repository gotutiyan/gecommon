from typing import List, Tuple, Optional, Union, Dict
from dataclasses import dataclass
from collections import Counter
import itertools
import errant
from tqdm import tqdm

class Edit:
    def __init__(
        self,
        o_start: int = None,
        o_end: int = None,
        c_str: str = None,
        type: str = None
    ):
        self.o_start = o_start
        self.o_end = o_end
        self.c_str = c_str
        self.type = type

    def is_insert(self):
        return self.o_start == self.o_end
    
    def is_delete(self):
        return self.c_str == ''

    def is_replace(self):
        return not self.is_delete() and self.o_start != self.o_end

    def __str__(self):
        return f'Edit({self.o_start}, {self.o_end}, {self.c_str}, {self.type})'

    def __repr__(self) -> str:
        return f'Edit({self.o_start}, {self.o_end}, {self.c_str}, {self.type})'

class Parallel:
    def __init__(
        self,
        m2: List[str] = None,
        ref_id: int = 0,
        srcs: List[str] = None,
        trgs: List[str] = None
    ):
        self.srcs, self.trgs, self.edits_list = None, None, None
        self.GED_MODES = ['bin', 'cat1', 'cat2', 'cat3']
        if m2 is not None:
            self.srcs, self.trgs, self.edits_list = self.load_m2(m2, ref_id)
        elif srcs is not None and trgs is not None:
            self.srcs, self.trgs, self.edits_list = self.load_parallel(srcs, trgs)

        assert self.srcs is not None and self.edits_list is not None

    @classmethod
    def from_m2(cls, m2: str, ref_id: int=0):
        '''
        Input
            m2: Input file path of M2
        '''
        m2 = open(m2).read().rstrip().split('\n\n')
        return cls(m2=m2, ref_id=ref_id)

    @classmethod
    def from_demo(cls):
        # Cited ERRANT official page for the following example.
        # https://github.com/chrisjbryant/errant
        m2 = '''S This are gramamtical sentence .
A 1 2|||R:VERB:SVA|||is|||REQUIRED|||-NONE-|||0
A 2 2|||M:DET|||a|||REQUIRED|||-NONE-|||0
A 2 3|||R:SPELL|||grammatical|||REQUIRED|||-NONE-|||0
A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||1

S This are gramamtical sentence .
A 1 2|||R:VERB:SVA|||is|||REQUIRED|||-NONE-|||0
A 2 2|||M:DET|||a|||REQUIRED|||-NONE-|||0
A 2 3|||R:SPELL|||grammatical|||REQUIRED|||-NONE-|||0
A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||1

S This are gramamtical sentence .
A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||0
A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||1

'''.rstrip().split('\n\n')
        return cls(m2=m2)
    
    @classmethod
    def from_parallel(cls, src: str, trg: str):
        srcs = open(src).read().rstrip().split('\n')
        trgs = open(trg).read().rstrip().split('\n')
        return cls(srcs=srcs, trgs=trgs)

    def load_m2(
        self,
        m2_contents: List[str],
        ref_id: int=0
    ) -> Tuple[List[str], List[str], List[List[Edit]]]:
        srcs: List[str] = []
        trgs: List[str] = [] 
        edits_list: List[List[Edit]] = []
        num_error_sent = 0
        num_words = 0
        num_edits = 0
        num_corrected_token = 0
        for content in m2_contents:
            src, *edits = content.split('\n')
            src = src[2:]  # remove 'S '
            edits = [
                self.make_edit_instance(e[2:]) for e in edits \
                if e.split('|||')[1] not in ['noop', 'UNK'] \
                    and int(e.split('|||')[-1]) == ref_id \
                    
            ]
            srcs.append(src)
            trgs.append(self.apply_edits(src, edits))
            edits_list.append(edits)
            num_words += len(src.split(' '))
            num_edits += len(edits)
            num_corrected_token += sum(
                e.o_end - e.o_start for e in edits
            )
            if len(edits) > 0:
                num_error_sent += 1
        self.num_sents = len(srcs)
        self.num_error_sent = num_error_sent
        self.num_words = num_words
        self.num_edits = num_edits
        self.num_corrected_token = num_corrected_token
        return srcs, trgs, edits_list

    @staticmethod
    def make_edit_instance(editstr: str) -> Edit:
        pos, etype, c_str, *others = editstr.split('|||')
        start, end = map(int, pos.split(' '))
        return Edit(
            o_start=start,
            o_end=end,
            c_str=c_str,
            type=etype
        )

    def load_parallel(
        self,
        srcs: List[str],
        trgs: List[str]
    ) -> Tuple[List[str], List[str], List[List[Edit]]]:
        annotator = errant.load('en')
        edits_list = []
        num_error_sent = 0
        num_words = 0
        num_edits = 0
        num_corrected_token = 0
        for src, trg in tqdm(zip(srcs, trgs), total=len(srcs)):
            orig = annotator.parse(src)
            cor = annotator.parse(trg)
            edits = annotator.annotate(orig, cor)
            edits = [self.convert_my_edit(e) for e in edits]
            edits_list.append(edits)
            num_words += len(src.split(' '))
            num_edits += len(edits)
            num_corrected_token += sum(
                e.o_end - e.o_start for e in edits
            )
            if len(edits) > 0:
                num_error_sent += 1
        self.num_sents = len(srcs)
        self.num_error_sent = num_error_sent
        self.num_words = num_words
        self.num_edits = num_edits
        self.num_corrected_token = num_corrected_token
        return srcs, trgs, edits_list
    
    @staticmethod
    def convert_my_edit(edit: errant.edit.Edit) -> Edit:
        return Edit(
            o_start=edit.o_start,
            o_end=edit.o_end,
            c_str=edit.c_str,
            type=edit.type
        )
    
    def show_stats(self, cat3: bool=False) -> None:
        print('Number of sents:', self.num_sents)
        print('Number of words:', self.num_words)
        print('Number of edits:', self.num_edits)
        print('Number of error sents:', self.num_error_sent / self.num_sents)
        print('Word error rate:', self.num_corrected_token / self.num_words)
        print('=== Cat1 ===')
        self.show_etype_stats(cat=1)
        print('=== Cat2 ===')
        self.show_etype_stats(cat=2)
        if cat3:
            print('=== Cat3 ===')
            self.show_etype_stats(cat=3)

    def show_etype_stats(self, cat: int=2) -> None:
        def show(cat, num_edits):
            cat2freq = Counter(cat)
            print(f'{"Error type":10} {"Freq":6} Ratio')
            for k in sorted(cat2freq.keys()):
                print(f'{k:10} {cat2freq[k]:6} {cat2freq[k]/num_edits*100:.2f}')
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
    
    def generate_corrupted_refs(
        self,
        n: int=1,
        return_labels: bool=False
    ) -> Union[Tuple[List[List[str]], List[List[List[str]]]], List[List[str]]]:
        '''
        Returns
            refs_list: List[List[str]], the size is (# of sources, # of currupted references).
                Note that the second dimension is different depending on sources.

            labels_list: List[List[List[str]]], the size is (# of sources, # of currupted references, # of labels)
                Note that the second dimension is different depending on sources.
                And the third dimension is the same as n.
        '''
        refs_list = []
        labels_list = []
        for src, edits in zip(self.srcs, self.edits_list):
            all_edits = set(edits)
            refs = []
            labels = []
            for edit_set in itertools.combinations(edits, n):
                edit_to_be_removed = set(edit_set)
                edit_to_be_applied = all_edits - edit_to_be_removed
                refs.append(self.apply_edits(src, edit_to_be_applied))
                labels.append([e.type for e in edit_to_be_removed])
            refs_list.append(refs)
            labels_list.append(labels)
        if return_labels:
            assert len(refs_list) == len(labels_list)
            return refs_list, labels_list
        else:
            return refs_list
    
    def generate_corrected_srcs(
        self,
        n=1,
        return_labels: bool=False
    ) -> Union[Tuple[List[List[str]], List[List[List[str]]]], List[List[str]]]:
        corrected_list = []
        labels_list = []
        for src, edits in zip(self.srcs, self.edits_list):
            corrected = []
            labels = []
            for edit_set in itertools.combinations(edits, n):
                corrected.append(self.apply_edits(src, edit_set))
                labels.append([e.type for e in edit_set])
            corrected_list.append(corrected)
            labels_list.append(labels)
        if return_labels:
            assert len(corrected_list) == len(labels_list)
            return corrected_list, labels_list
        else:
            return corrected_list

    @staticmethod
    def apply_edits(src: str, edits: List[Edit]) -> str:
        offset = 0
        tokens = src.split(' ')
        for e in edits:
            if e.o_start == -1:
                continue
            s_idx = e.o_start + offset
            e_idx = e.o_end + offset
            if e.is_delete():
                tokens[s_idx:e_idx] = ['$DELETE']
                offset -= (e.o_end - e.o_start) - 1
            elif e.is_insert():
                tokens[s_idx:e_idx] = e.c_str.split(' ')
                offset += len(e.c_str.split())
            else:
                tokens[s_idx:e_idx] = e.c_str.split(' ')
                offset += len(e.c_str.split(' ')) - (e.o_end - e.o_start)
        trg = ' '.join(tokens).replace(' $DELETE', '').replace('$DELETE ', '').replace('$DELETE', '')
        return trg
    
    def convert_etype(self, t, cat=1) -> str:
        # cat=1, M, R, U
        # cat=2, e.g. DET, NOUN:NUM
        # cat=3, M:DET, R:NOUN:NUM
        if cat == 1:
            return t[0]
        elif cat == 2:
            return t[2:]
        else:
            return t
        
    def ged_labels_sent(
            self,
            mode: str='bin',
            return_id: bool=False
        ) -> List[List[Union[str, int]]]:
        assert mode in self.GED_MODES
        labels = []
        label2id = self.get_ged_label2id(mode=mode)
        for s, t, edits in zip(self.srcs, self.trgs, self.edits_list):
            if s == t:
                label = ['CORRECT']
            else:
                if mode == 'bin':
                    label = ['INCORRECT']
                else:
                    cat = int(mode[-1])
                    label = list(set(self.convert_etype(e.type, cat) for e in edits))
            if return_id:
                label = [label2id[l] for l in label]
            labels.append(label)
        assert len(labels) == len(self.srcs)
        return labels

    def ged_labels_token(
            self,
            mode: str='bin',
            return_id: bool=False
        ) -> List[List[List[Union[str, int]]]]:
        assert mode in self.GED_MODES
        labels = []
        label2id = self.get_ged_label2id(mode=mode)
        for s, edits in zip(self.srcs, self.edits_list):
            label = ['CORRECT'] * len(s.split(' '))
            for e in edits:
                st = e.o_start
                en = e.o_end
                if e.is_insert():
                    # If missing error, we assign an incorrect label to the token on the right of the span.
                    # This follows [Yuan+ 21]'s strategy (Sec. 4.2): https://aclanthology.org/2021.emnlp-main.687.pdf
                    st = e.o_end
                    en = e.o_end + 1
                if mode == 'bin':
                    label[st:en] = ['INCORRECT'] * (en - st)
                else:
                    cat = int(mode[-1])
                    t = self.convert_etype(e.type, cat)
                    label[st:en] = [t] * (en - st)
            if return_id:
                label = [label2id[l] for l in label]
            labels.append(label)
        assert len(labels) == len(self.srcs)
        return labels
    
    def get_ged_id2label(self, mode: str='bin') -> Dict[int, str]:
        mru_cats = [
            'ADJ',
            'ADV',
            'CONJ',
            'CONTR',
            'DET',
            'NOUN',
            'NOUN:POSS',
            'OTHER',
            'PART',
            'PREP',
            'PRON',
            'PUNCT',
            'VERB',
            'VERB:FORM',
            'VERB:TENSE',
        ]
        r_cats = [
            'ADJ:FORM',
            'MORPH',
            'NOUN:INFL',
            'NOUN:NUM',
            'ORTH',
            'SPELL',
            'VERB:INFL',
            'VERB:SVA',
            'WO'
        ]
        cat1 = {0: 'CORRECT'}
        cat2 = {0: 'CORRECT'}
        cat3 = {0: 'CORRECT'}
        for i, c in enumerate('MRU'):
            cat1[i+1] = c
        for i, c in enumerate(mru_cats + r_cats):
            cat2[i+1] = c
        idx = 1
        for c1 in 'MRU':
            for c2 in mru_cats:
                cat3[idx] = c1 + ':' + c2
                idx += 1
            if c1 == 'R':
                for c2 in r_cats:
                    cat3[idx] = c1 + ':' + c2
                    idx += 1
        assert len(cat1) == 4
        assert len(cat2) == 25
        assert len(cat3) == 55

        if mode == 'bin':
            return {0: 'CORRECT', 1: 'INCORRECT'}
        elif mode == 'cat1':
            return cat1
        elif mode == 'cat2':
            return cat2
        else:
            return cat3
    
    def get_ged_label2id(self, mode: str='bin') -> Dict[str, int]:
        id2label = self.get_ged_id2label(mode)
        return {v:k for k, v in id2label.items()}
        