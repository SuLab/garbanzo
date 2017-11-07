from itertools import chain

import connexion

from garbanzo import lookup
from garbanzo.models.statement import Statement
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime


def get_statements(s, relations=None, t=None, keywords=None, semanticGroups=None, pageNumber=None, pageSize=None):
    """
    get_statements
    Given a specified set of [CURIE-encoded](https://www.w3.org/TR/curie/)  &#39;source&#39; (&#39;s&#39;) concept identifiers,  retrieves a paged list of relationship statements where either the subject or object concept matches any of the input &#39;source&#39; concepts provided.  Optionally, a set of &#39;target&#39; (&#39;t&#39;) concept  identifiers may also be given, in which case a member of the &#39;target&#39; identifier set should match the concept opposing the &#39;source&#39; in the  statement, that is, if the&#39;source&#39; matches a subject, then the  &#39;target&#39; should match the object of a given statement (or vice versa). 
    :param s: a set of [CURIE-encoded](https://www.w3.org/TR/curie/) identifiers of  &#39;source&#39; concepts possibly known to the beacon. Unknown CURIES should simply be ignored (silent match failure). 
    :type s: List[str]
    :param relations: a (url-encoded, space-delimited) string of predicate relation identifiers with which to constrain the statement relations retrieved  for the given query seed concept. The predicate ids sent should  be as published by the beacon-aggregator by the /predicates API endpoint. 
    :type relations: str
    :param t: (optional) an array set of [CURIE-encoded](https://www.w3.org/TR/curie/)  identifiers of &#39;target&#39; concepts possibly known to the beacon.  Unknown CURIEs should simply be ignored (silent match failure). 
    :type t: List[str]
    :param keywords: a (url-encoded, space-delimited) string of keywords or substrings against which to match the subject, predicate or object names of the set of concept-relations matched by any of the input exact matching concepts 
    :type keywords: str
    :param semanticGroups: a (url-encoded, space-delimited) string of semantic groups (specified as codes CHEM, GENE, ANAT, etc.) to which to constrain the subject or object concepts associated with the query seed concept (see [Semantic Groups](https://metamap.nlm.nih.gov/Docs/SemGroups_2013.txt) for the full list of codes) 
    :type semanticGroups: str
    :param pageNumber: (1-based) number of the page to be returned in a paged set of query results 
    :type pageNumber: int
    :param pageSize: number of concepts per page to be returned in a paged set of query results 
    :type pageSize: int

    :rtype: List[Statement]
    """
    if relations or t:
        # todo: relations and t are NOT IMPLEMENTED YET
        return []
    qids = s
    qids = set(chain(*[x.split(",") for x in qids]))
    # get rid of any non wd identifiers
    qids = set(x for x in qids if x.startswith("wd:"))
    qids = frozenset([x.strip().replace("wd:", "") for x in qids])
    print(qids)

    keywords = frozenset(keywords.split(" ")) if keywords else None
    types = frozenset(semanticGroups.split(" ")) if semanticGroups else None
    datapage = lookup.get_statements(qids, keywords, types)

    pageNumber = pageNumber if pageNumber else 1
    pageSize = pageSize if pageSize else 10

    start_idx = ((pageNumber - 1) * pageSize)
    end_idx = start_idx + pageSize

    datapage = datapage[start_idx:end_idx]
    return [Statement(**x) for x in datapage]
