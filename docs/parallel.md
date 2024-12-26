# gecommon.Parallel

### `from_parallel(src: str=None, trg: str=None) -> Parallel`

Load dataset from raw text files.

```python
from gecommon import Parallel
gec = Parallel.from_parallel(
    src=<a src file path>,
    trg=<a trg file path>
)
```

### `from_m2(m2: str=None, ref_id: int=0) -> Parallel`

Load dataset from a M2 file.

```python
from gecommon import Parallel
gec = Parallel.from_m2(
    m2=<a m2 file path>,
    ref_id=0
)
```

### `from_demo() -> Parallel`

Load demo data. This is to understand how to use (and is for debugging).
```python
from gecommon import Parallel
gec = Parallel.from_demo()

# The above uses the examples based on one in the ERRANT's offical page.
# https://github.com/chrisjbryant/errant
'''S This are gramamtical sentence .
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

'''
```

### `show_stats(cat3: bool=False) -> None`
Show statistics of dataset. E.g. the number of sentence, the word error rate.

Also show combined error types such as `R:NOUN` if `cat3=True`.

```python
from gecommon import Parallel
gec = Parallel.from_demo()
print(gec.show_stats())
'''
Number of sents: 3
Number of words: 18
Number of edits: 5
Number of error sents: 0.6666666666666666
Word error rate: 0.2777777777777778
=== Cat1 ===
Error type Freq   Ratio
M               1 20.00
R               3 60.00
U               1 20.00
=== Cat2 ===
Error type Freq   Ratio
DET             1 20.00
ORTH            1 20.00
SPELL           1 20.00
VERB            1 20.00
VERB:SVA        1 20.00
'''
```

### `ged_labels_sent(mode: str = 'bin', return_id=False) -> List[List[Union[str, int]]]`

Output sentence-level error detection labels.

- `mode=` indicates the type of detection labels.
    - `mode='bin'` is 2-class labels, correct and incorrect.
    - `mode='cat1'` is 4-class labels, correct, replacement, missing, and unnecessary.
    - `mode='cat2'` is 25-class labels, correct and 24 labels without UNK of ERRANT's definition.
    - `mode='cat3'` is 55-class labels, correct and 54 labels like `M:NOUN`. Refer to Appendix A in the [Bryant+ 17](https://aclanthology.org/P17-1074.pdf).
- By default, this function returns labels as string. If you want ids instead, specify `return_id=True`.

```python
from gecommon import Parallel
gec = Parallel.from_demo()
print(gec.ged_labels_sent()) 
# [['INCORRECT'], ['INCORRECT'], ['CORRECT']]
print(gec.ged_labels_sent(return_id=True))
# [[1], [1], [0]] 
print(gec.ged_labels_sent(mode='cat1'))
# [['R', 'M'], ['U', 'R'], ['CORRECT']]
print(gec.ged_labels_sent(mode='cat2'))
# [['DET', 'SPELL', 'VERB:SVA'], ['ORTH', 'VERB'], ['CORRECT']]
print(gec.ged_labels_sent(mode='cat3'))
# [['M:DET', 'R:VERB:SVA', 'R:SPELL'], ['R:ORTH', 'U:VERB'], ['CORRECT']]
print(gec.ged_labels_sent(mode='cat3', return_id=True))
# [[5, 38, 36], [35, 52], [0]]
```

### `ged_labels_token(mode: str = 'bin', return_id=False) -> List[List[Union[str, int]]]`
Output token-level error detection labels based on ERRANT's alignments.
The behavior is the same as `ged_labels_sent()`.

```python
from gecommon import Parallel
gec = Parallel.from_demo()
print(gec.ged_labels_token())
# [['CORRECT', 'INCORRECT', 'INCORRECT', 'CORRECT', 'CORRECT'],
#  ['CORRECT', 'CORRECT', 'INCORRECT', 'CORRECT', 'INCORRECT', 'INCORRECT', 'CORRECT', 'CORRECT'],
#  ['CORRECT', 'CORRECT', 'CORRECT', 'CORRECT', 'CORRECT']]
print(gec.ged_labels_token(return_id=True))
# [[0, 1, 1, 0, 0],
#  [0, 0, 1, 0, 1, 1, 0, 0],
#  [0, 0, 0, 0, 0]]
```

### `def get_ged_id2label(mode='bin') -> Dict[int, str]`
Return the id2label dictionary for error detection.

- `mode=` indicates the type of detection labels.
    - `mode='bin'` is 2-class labels, correct and incorrect.
    - `mode='cat1'` is 4-class labels, correct, replacement, missing, and unnecessary.
    - `mode='cat2'` is 25-class labels, correct and 24 labels without UNK of ERRANT's definition.
    - `mode='cat3'` is 55-class labels, correct and 54 labels like `M:NOUN`. Refer to Appendix A in the [Bryant+ 17](https://aclanthology.org/P17-1074.pdf)

```python
from gecommon import Parallel
gec = Parallel.from_demo()
print(gec.get_ged_id2label(mode='bin'))
# {0: 'CORRECT', 1: 'INCORRECT'}
print(gec.get_ged_id2label(mode='cat1'))
# {0: 'CORRECT', 1: 'M', 2: 'R', 3: 'U'}
print(gec.get_ged_id2label(mode='cat2'))
# {0: 'CORRECT', 1: 'ADJ', 2: 'ADV', 3: 'CONJ', 4: 'CONTR', ...
print(gec.get_ged_id2label(mode='cat3'))
# {0: 'CORRECT', 1: 'M:ADJ', 2: 'M:ADV', 3: 'M:CONJ', 4: 'M:CONTR', 5: 'M:DET', ... 
```

### `def get_ged_label2id(mode='bin') -> Dict[str, int]`
Return the label2id dictionary for error detection.

```python
from gecommon import Parallel
gec = Parallel.from_demo()
print(gec.get_ged_label2id(mode='bin'))
# {'CORRECT': 0, 'INCORRECT': 1}
print(gec.get_ged_label2id(mode='cat1'))
# {'CORRECT': 0, 'M': 1, 'R': 2, 'U': 3}
print(gec.get_ged_label2id(mode='cat2'))
# {'CORRECT': 0, 'ADJ': 1, 'ADV': 2, 'CONJ': 3, 'CONTR': 4, ...
print(gec.get_ged_label2id(mode='cat3'))
# {'CORRECT': 0, 'M:ADJ': 1, 'M:ADV': 2, 'M:CONJ': 3, 'M:CONTR': 4, 'M:DET': 5, ...
```

