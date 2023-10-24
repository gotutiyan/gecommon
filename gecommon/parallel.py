from typing import List, Tuple, Optional, Union
from dataclasses import dataclass
from collections import Counter
import itertools
import errant

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
        return self.type.startswith('M')
    
    def is_delete(self):
        return self.type.startswith('U')

    def is_replace(self):
        return self.type.startswith('R')

    def __str__(self):
        return f'Edit({self.o_start}, {self.o_end}, {self.c_str}, {self.type})'

    def __repr__(self) -> str:
        return f'Edit({self.o_start}, {self.o_end}, {self.c_str}, {self.type})'

class Parallel:
    def __init__(
        self,
        m2: List[str] = None,
        srcs: List[str] = None,
        trgs: List[str] = None
    ):
        self.srcs, self.trgs, self.edits_list = None, None, None
        if m2 is not None:
            self.srcs, self.trgs, self.edits_list = self.load_m2(m2)
        elif srcs is not None and trgs is not None:
            self.srcs, self.trgs, self.edits_list = self.load_parallel(srcs, trgs)

        assert self.srcs is not None and self.edits_list is not None

    @classmethod
    def from_m2(cls, m2: str):
        '''
        Input
            m2: Input file path of M2
        '''
        m2 = open(m2).read().rstrip().split('\n\n')
        return cls(m2=m2)

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
        m2_contents
    ) -> Union[List[str], List[List[Edit]]]:
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
                if not e.startswith('A -1')  # remove noop errors
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
    ) -> Union[List[str], List[List[Edit]]]:
        annotator = errant.load('en')
        edits_list = []
        num_error_sent = 0
        num_words = 0
        num_edits = 0
        num_corrected_token = 0
        for src, trg in zip(srcs, trgs):
            orig = annotator.parse(src)
            cor = annotator.parse(trg)
            edits = annotator.annorate(orig, cor)
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
    
    def show_stats(self, cat3=False):
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

    def show_etype_stats(self, cat=2):
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
    
    def generate_corrupted_refs(self, n=1, return_labels: bool=False):
        ''' Generate corrupted references that is missed only one or more edits for each.
        E.g.
        S a b c
        A 0 1|||dummy|||d ... # replace
        B 1 1|||dummy|||||| ... # delete
        C 2 2|||dummy|||e ... # inseting
        
        Using above example,
        The completely reference is "d c e" but this function returns
        ["a c e", "d b c e", "d c"].
        '''
        references = []
        labels = []
        for src, edits in zip(self.srcs, self.edits_list):
            all_edits = set(edits)
            for edit_set in itertools.combinations(edits, n):
                edit_to_be_removed = set(edit_set)
                edit_to_be_applied = all_edits - edit_to_be_removed
                references.append(self.apply_edits(src, edit_to_be_applied))
                labels.append([e.type for e in edit_to_be_removed])
        if return_labels:
            assert len(references) == len(labels)
            return references, labels
        else:
            return references
    
    def generate_corrected_srcs(self, n=1, return_labels: bool=False):
        corrected = []
        labels = []
        for src, edits in zip(self.srcs, self.edits_list):
            for edit_set in itertools.combinations(edits, n):
                corrected.append(self.apply_edits(src, edit_set))
                labels.append([e.type for e in edit_set])
        if return_labels:
            assert len(corrected) == len(labels)
            return corrected, labels
        else:
            return corrected

    @staticmethod
    def apply_edits(src: str, edits: List[Edit]):
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
        trg = ' '.join(tokens).replace(' $DELETE', '').replace('$DELETE ', '')
        return trg

    def ged_labels_sent(self):
        labels = []
        for s, t in zip(self.srcs, self.trgs):
            if s == t:
                labels.append(0)
            else:
                labels.append(1)
        return labels

    def ged_labels_token(self):
        labels = []
        for s, edits in zip(self.srcs, self.edits_list):
            label = [0] * len(s.split(' '))
            for e in edits:
                if e.is_insert():
                    continue
                label[e.o_start:e.o_end] = [1] * (e.o_end - e.o_start)
            labels.append(label)
        return labels
