from typing import List, Tuple, Dict, Optional, Union
from dataclasses import dataclass
import numpy as np

@dataclass
class Performance:
    tp: int = None
    fp: int = None
    fn: int = None
    p: float = None
    r: float = None
    f05: float = None

@dataclass
class SystemPerformance:
    overall: Performance = None
    etype: Dict[str, Performance] = None

class Comparison:
    def __init__(self, scores: List[str]=[], labels: List[str]=[]):
        self.system_performances: Dict[str, SystemPerformance] = dict()
        for string, label in zip(scores, labels):
            self.register_sys_performance(string.strip(), label)
    
    def get_sorted_etype(self):
        sample_label = list(self.system_performances.keys())[0]
        return sorted(self.system_performances[sample_label].etype.keys())

    @property
    def n_etypes(self):
        return len(self.get_sorted_etype())
    
    @classmethod
    def from_errant_format(cls, scores: List[str], labels: str=None):
        assert type(scores) == list
        assert len(scores) == len(labels)
        if labels is None:
            labels = [f'LABEL{i}' for i in range(len(scores))]
        assert len(scores) == len(labels)
        return cls(scores, labels)

    def register_sys_performance(self, scores: str, label: str) -> None:
        sys_performance = self.load_errant_format(scores)
        self.system_performances[label] = sys_performance

    @staticmethod
    def load_errant_format(data_str: str) -> SystemPerformance:
        data = data_str.rstrip().split('\n')
        type_score = dict()
        for d in data:
            if d.startswith('='):
                continue
            if d.startswith('Category'):
                continue
            if d == '':
                break
            elems = [dd for dd in d.split(' ') if dd != '']
            performance = Performance(
                tp=int(elems[1]),
                fp=int(elems[2]),
                fn=int(elems[3]),
                p=float(elems[4]),
                r=float(elems[5]),
                f05=float(elems[6])
            )
            type_score[elems[0]] = performance
        tp=sum(e.tp for e in type_score.values())
        fp=sum(e.fp for e in type_score.values())
        fn=sum(e.fn for e in type_score.values())
        p=tp / (tp + fp)
        r=tp / (tp + fn)
        overall = Performance(
            tp=tp,
            fp=fp,
            fn=fn,
            p=p,
            r=r,
            f05=1.25 * (p*r) / (0.25*p + r)
        )
        return SystemPerformance(
            overall=overall,
            etype=type_score
        )
        
    def compare(self, label1: str=None, label2: str=None, key: str='f05') -> None:
        per1: SystemPerformance = self.system_performances[label1]
        per2: SystemPerformance = self.system_performances[label2]
        print('=== Overall ===')
        print(f'Precision: {per1.overall.p:.4f} -> {per2.overall.p:.4f}')
        print(f'Recall   : {per1.overall.r:.4f} -> {per2.overall.r:.4f}')
        print(f'F0.5     : {per1.overall.f05:.4f} -> {per2.overall.f05:.4f}')
        print()
        print(f'=== Error type (key = {key}) ===')
        for t in self.get_sorted_etype():
            t_per1: Performance = per1.etype[t]
            t_per2: Performance = per2.etype[t]
            diff = t_per2.__dict__[key] - t_per1.__dict__[key]
            if diff > 0:
                diff = '+' + str(round(diff, 4))
            else:
                diff = str(round(diff, 4))
            print(f'{t:10}: {t_per1.__dict__[key]:7} -> {t_per2.__dict__[key]:7} ({diff:7})')

    def load_etype_scores(self, label: str=None, key='f05') -> Dict[str, Union[int, float]]:
        return {
            etype: self.system_performances[label].etype[etype].__dict__[key] \
            for etype in self.get_sorted_etype()
        }

    def plot_etype_comparison(
        self,
        labels: List[str]=None,
        key='f05',
        outpath='out.png'
    ) -> None:
        import matplotlib.pyplot as plt
        colors = 'gbrcmy'
        fig = plt.figure(figsize=(12, 4))
        ax = fig.add_subplot(111)
        width = 0.7 / len(labels)
        for i in range(len(labels)):
            x = np.arange(0.5+width*i, self.n_etypes+width*i+0.5, 1)
            y = [
                self.system_performances[labels[i]].etype[etype].__dict__[key] \
                for etype in self.get_sorted_etype()
            ]
            plt.bar(x, y, color=colors[i], width=width, label=labels[i], align='center')
        ax.legend(loc=2)
        ax.yaxis.grid(linestyle='--', alpha=0.4)
        ax.set_xlabel('Error types')
        ax.set_ylabel(key)
        ax.set_xticks([x - width/len(labels) \
                       for x in np.arange(0.5+width*i, self.n_etypes+width*i+0.5, 1)])
        ax.set_xticklabels(list(self.get_sorted_etype()), rotation=60)
        plt.tight_layout()
        plt.savefig(outpath)

    @classmethod
    def from_demo(cls):
        baseline = '''===================== Span-Based Correction ======================
Category       TP       FP       FN       P        R        F0.5
ADJ            9        29       104      0.2368   0.0796   0.1698
ADJ:FORM       5        1        11       0.8333   0.3125   0.625
ADV            9        41       106      0.18     0.0783   0.1429
CONJ           10       14       34       0.4167   0.2273   0.3571
CONTR          11       17       19       0.3929   0.3667   0.3873
DET            347      234      449      0.5972   0.4359   0.5561
MORPH          32       37       126      0.4638   0.2025   0.3687
NOUN           21       107      307      0.1641   0.064    0.125
NOUN:INFL      6        1        4        0.8571   0.6      0.7895
NOUN:NUM       112      84       139      0.5714   0.4462   0.5411
NOUN:POSS      22       14       44       0.6111   0.3333   0.5238
ORTH           157      94       195      0.6255   0.446    0.5789
OTHER          122      290      858      0.2961   0.1245   0.2321
PART           20       9        40       0.6897   0.3333   0.5682
PREP           245      169      495      0.5918   0.3311   0.5113
PRON           69       71       109      0.4929   0.3876   0.4675
PUNCT          300      163      1178     0.6479   0.203    0.4505
SPELL          152      48       235      0.76     0.3928   0.6403
VERB           53       96       349      0.3557   0.1318   0.2655
VERB:FORM      125      82       111      0.6039   0.5297   0.5874
VERB:INFL      4        1        1        0.8      0.8      0.8
VERB:SVA       110      64       38       0.6322   0.7432   0.6517
VERB:TENSE     159      133      314      0.5445   0.3362   0.4845
WO             19       17       76       0.5278   0.2      0.3975

=========== Span-Based Correction ============
TP      FP      FN      Prec    Rec     F0.5
2119    1816    5342    0.5385  0.284   0.4567
==============================================
'''
        ours = '''===================== Span-Based Correction ======================
Category       TP       FP       FN       P        R        F0.5
ADJ            12       35       101      0.2553   0.1062   0.1993
ADJ:FORM       7        0        9        1.0      0.4375   0.7955
ADV            21       51       94       0.2917   0.1826   0.2605
CONJ           9        19       35       0.3214   0.2045   0.2885
CONTR          11       14       19       0.44     0.3667   0.4231
DET            371      251      425      0.5965   0.4661   0.5649
MORPH          49       45       109      0.5213   0.3101   0.4588
NOUN           24       80       304      0.2308   0.0732   0.1613
NOUN:INFL      5        0        5        1.0      0.5      0.8333
NOUN:NUM       132      78       119      0.6286   0.5259   0.6049
NOUN:POSS      23       19       43       0.5476   0.3485   0.4915
ORTH           167      72       185      0.6987   0.4744   0.6384
OTHER          140      333      840      0.296    0.1429   0.2437
PART           23       8        37       0.7419   0.3833   0.625
PREP           285      178      455      0.6156   0.3851   0.5498
PRON           76       59       102      0.563    0.427    0.5292
PUNCT          330      177      1148     0.6509   0.2233   0.4706
SPELL          197      51       190      0.7944   0.509    0.7143
VERB           72       109      330      0.3978   0.1791   0.3197
VERB:FORM      132      76       104      0.6346   0.5593   0.618
VERB:INFL      5        1        0        0.8333   1.0      0.8621
VERB:SVA       123      58       25       0.6796   0.8311   0.7053
VERB:TENSE     163      125      310      0.566    0.3446   0.5015
WO             17       14       78       0.5484   0.1789   0.3881

=========== Span-Based Correction ============
TP      FP      FN      Prec    Rec     F0.5
2394    1853    5067    0.5637  0.3209  0.4896
==============================================
'''
        return cls([baseline, ours], ['baseline', 'ours'])
            