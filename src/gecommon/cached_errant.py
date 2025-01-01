import errant
import hashlib
import spacy


class CachedERRANT:
    """The efficent version of ERRANT.Annotator"""

    def __init__(self, lang="en"):
        self.errant = errant.load(lang)
        self.cache_parse = dict()
        self.cache_annotate = dict()

    def cached_parse(self, sent: str) -> spacy.tokens.doc.Doc:
        """Efficient parse() by caching.

        Args:
            sent (str): The sentence to be parsed.
        Return:
            spacy.tokens.doc.Doc: The parse results.
        """
        key = hashlib.sha256(sent.encode()).hexdigest()
        if self.cache_parse.get(key) is None:
            self.cache_parse[key] = self.errant.parse(sent)
        return self.cache_parse[key]

    def extract_edits(self, src: str, trg: str) -> list[errant.edit.Edit]:
        """Extract edits given a source and a corrected.

        Args:
            src (str): The source sentence.
            trg (str): The corrected sentence.

        Returns:
            list[errant.edit.Edit]: Extracted edits.
        """
        key = hashlib.sha256((src + "|||" + trg).encode()).hexdigest()
        if self.cache_annotate.get(key) is None:
            self.cache_annotate[key] = self.errant.annotate(
                self.cached_parse(src), self.cached_parse(trg)
            )
        return self.cache_annotate[key]
