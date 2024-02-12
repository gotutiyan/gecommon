# GECOMMON: A common toolkit for Grammatical Error Correcion

This is a common toolkit for Grammatical Error Correction (GEC).

Install by:
```
git clone https://github.com/gotutiyan/gecommon.git
cd gecommon
pip install -e .
```

# Features
- [Parallel](https://github.com/gotutiyan/gecommon#gecommonparallel) ([docs](./docs/parallel.md)): A class to do some operations with parallel data. E.g. make error detection labels, generate corrupt references.
- [Comparison](https://github.com/gotutiyan/gecommon#gecommoncomparison) ([docs](./docs/comparison.md)): A class to compare evaluation results of ERRANT.

# Use cases

### gecommon.Parallel

- The most important feature is the ability to handle both M2 and parallel formats in the same interface.

```python
from gecommon import Parallel
# If the input is M2 format
gec = Parallel.from_m2(
    m2=<a m2 file path>,
    ref_id=0
)
# If parallel format
gec = Parallel.from_parallel(
    src=<a src file path>,
    trg=<a trg file path>
)
# After that, you can handle the input data in the same interface.
```

- To convert a M2 file into parallel format
```python
from gecommon import Parallel
gec = Parallel.from_m2(
    m2=<a m2 file path>,
    ref_id=0
)
gec.srcs  # sources
gec.trgs  # targets
```

- To generate error detection labels
    - You can use not only binary labels but also 4-class, 25-class, 55-class like [[Yuan+ 21]](https://aclanthology.org/2021.emnlp-main.687/).
```python
gec = Parallel.from_demo()
# Sentence-level labels
print(gec.ged_labels_sent()) 
# [['INCORRECT'], ['INCORRECT'], ['CORRECT']]

# Token-level labels
print(gec.ged_labels_token(mode='cat3'))
# [['CORRECT', 'INCORRECT', 'INCORRECT', 'CORRECT', 'CORRECT'],
#  ['CORRECT', 'CORRECT', 'INCORRECT', 'CORRECT', 'INCORRECT', 'INCORRECT', 'CORRECT', 'CORRECT'],
#  ['CORRECT', 'CORRECT', 'CORRECT', 'CORRECT', 'CORRECT']]
```

- To use edits information
    - This is useful for pre-processing that requires editing information, like [[Chen+ 20]](https://aclanthology.org/2020.emnlp-main.581/), [[Li+ 23]](https://aclanthology.org/2023.acl-long.380/) and [[Bout+ 23]](https://aclanthology.org/2023.emnlp-main.355/).
```python
for edits in gec.edits_list:
    for e in edits:
        print(e.o_start, e.o_end, e.c_str)
    print('---')

# 1 2 is
# 2 2 a
# 2 3 grammatical
# ---
# 2 3 
# 4 6 grammatical
# ---
# ---
```

- To generate corrected sentences with some corrections applied (like [[PT-M2]](https://aclanthology.org/2022.emnlp-main.463/)), or reference sentences with some corrections excluded (like [[IMPARA]](https://aclanthology.org/2022.coling-1.316/)).

```python
from gecommon import Parallel
gec = Parallel.from_demo()
print(gec.generate_corrected_srcs(n=1))
# [[{'corrected': 'This is gramamtical sentence .', 'labels': ['R:VERB:SVA'], 'ids': [0]},
#   {'corrected': 'This are a gramamtical sentence .', 'labels': ['M:DET'], 'ids': [1]},
#   {'corrected': 'This are grammatical sentence .', 'labels': ['R:SPELL'], 'ids': [2]}],
# [{'corrected': 'This is a gram matical sentence .', 'labels': ['U:VERB'], 'ids': [0]},
# {'corrected': 'This is are a grammatical sentence .', 'labels': ['R:ORTH'], 'ids': [1]}],
# []]

print(gec.generate_corrupted_refs(n=1))
# [[{'ref': 'This are a grammatical sentence .', 'labels': ['R:VERB:SVA'], 'ids': [0]},
#   {'ref': 'This is grammatical sentence .', 'labels': ['M:DET'], 'ids': [1]},
#   {'ref': 'This is a gramamtical sentence .', 'labels': ['R:SPELL'], 'ids': [2]}],
# [{'ref': 'This is are a grammatical sentence .', 'labels': ['U:VERB'], 'ids': [0]},
#  {'ref': 'This is a gram matical sentence .', 'labels': ['R:ORTH'], 'ids': [1]}],
# []]
```
