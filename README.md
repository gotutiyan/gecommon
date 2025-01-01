# GECOMMON: A common toolkit for Grammatical Error Correcion

You can install from PyPi:
```
pip install gecommon
python -m spacy download en_core_web_sm
```

Or, from github:
```
git clone https://github.com/gotutiyan/gecommon.git
cd gecommon
pip install -e ./
python -m spacy download en_core_web_sm
```

# Features
- `gecommon.CachedERRANT`: Class to use ERRANT faster by caching.
- [gecommon.Parallel](https://github.com/gotutiyan/gecommon#gecommonparallel) ([docs](./docs/parallel.md)): Class to handle parallel and M2 format in the same interface.
- `gecommon.utils.apply_edits`: A function to apply an errant.edit.Edit sequence to a sentence.


# Use cases

### gecommon.CachedERRANT
You can replace `parse()` and `annotate()` of original ERRANT with `.extract_edits()`.  
This also caches the results of `parse()` and `annotate()`, thus it works faster when processing the same sentence or parallel sentence two or more times.

```python
from gecommon import CachedERRANT
errant = CachedERRANT()
edits = errant.extract_edits('This is a sample sentences .', 'These are sample sentences .')
print(edits)
```

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
assert gec.srcs is not None
assert gec.trgs is not None
assert gec.edits_list is not None
```

- To generate error detection labels
    - You can use not only binary labels but also 4-class, 25-class, 55-class like [[Yuan+ 21]](https://aclanthology.org/2021.emnlp-main.687/).
```python
from gecommon import Parallel
gec = Parallel.from_demo()
# Sentence-level labels
print(gec.ged_labels_sent()) 
# [['INCORRECT'], ['INCORRECT'], ['CORRECT']]

# Token-level labels
print(gec.ged_labels_token(mode='cat3'))
# [['CORRECT', 'R:VERB:SVA', 'R:SPELL', 'CORRECT', 'CORRECT'],
# ['CORRECT', 'CORRECT', 'U:VERB', 'CORRECT', 'R:ORTH', 'R:ORTH', 'CORRECT', 'CORRECT'],
# ['CORRECT', 'CORRECT', 'CORRECT', 'CORRECT', 'CORRECT']]
```

- To use edits information
    - This is useful for pre-processing that requires editing information, like [[Chen+ 20]](https://aclanthology.org/2020.emnlp-main.581/), [[Li+ 23]](https://aclanthology.org/2023.acl-long.380/) and [[Bout+ 23]](https://aclanthology.org/2023.emnlp-main.355/).
```python
from gecommon import Parallel
gec = Parallel.from_demo()
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