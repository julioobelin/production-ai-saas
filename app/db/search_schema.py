"""Full-text configuration shared by the column and the lexical retriever.

``simple`` does not stem and does not assume English. It is a retrieval
choice, not a vendor choice.
"""

FTS_REGCONFIG = "simple"
SEARCH_VECTOR_SQL = f"to_tsvector('{FTS_REGCONFIG}', content)"
