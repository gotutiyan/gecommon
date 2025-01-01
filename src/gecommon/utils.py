from errant.edit import Edit


def apply_edits(src: str, edits: list[Edit]) -> str:
    """Generate corrected sentence after applying the edits.

    Args:
        src (str): Source sentence.
        edits: (list[Edit]): Edit sequence.

    Returns:
        str: The corrected sentence.
    """
    offset = 0
    tokens = src.split(" ")
    for e in edits:
        if e.o_start == -1:
            continue
        s_idx = e.o_start + offset
        e_idx = e.o_end + offset
        if e.c_str == "":
            tokens[s_idx:e_idx] = ["$DELETE"]
            offset -= (e.o_end - e.o_start) - 1
        elif e.o_start == e.o_end:
            tokens[s_idx:e_idx] = e.c_str.split(" ")
            offset += len(e.c_str.split())
        else:
            tokens[s_idx:e_idx] = e.c_str.split(" ")
            offset += len(e.c_str.split(" ")) - (e.o_end - e.o_start)
    trg = (
        " ".join(tokens)
        .replace(" $DELETE", "")
        .replace("$DELETE ", "")
        .replace("$DELETE", "")
    )
    return trg
