def escape_like_term(term: str, escape_char: str = "\\") -> str:
    """
    Escapes special characters (%, _, and the escape character itself)
    in a term for use in a SQL LIKE/ILIKE clause.
    """
    if not term:
        return term
    return (
        term.replace(escape_char, escape_char + escape_char)
        .replace("%", escape_char + "%")
        .replace("_", escape_char + "_")
    )
