from itertools import chain

import connexion

from garbanzo import lookup
from garbanzo.models.statement import Statement
from datetime import date, datetime
from typing import List, Dict
from six import iteritems

from garbanzo.utils import always_curie
from ..util import deserialize_date, deserialize_datetime


def get_statements(s, relations=None, t=None, keywords=None, semanticGroups=None, pageNumber=None, pageSize=None):
    """
    get_statements
    Given a specified set of [CURIE-encoded](https://www.w3.org/TR/curie/)  'source' ('s')
    concept identifiers,  retrieves a paged list of relationship statements where either the subject or object
    concept matches any of the input 'source' concepts provided.  Optionally, a set of 'target' (
    't') concept  identifiers may also be given, in which case a member of the 'target' identifier
     set should match the concept opposing the 'source' in the  statement, that is, if the'source'
     matches a subject, then the  'target' should match the object of a given statement (or vice versa).
    :param s: a set of [CURIE-encoded](https://www.w3.org/TR/curie/) identifiers of  'source' concepts
    possibly known to the beacon. Unknown CURIES should simply be ignored (silent match failure).
    :type s: List[str]
    :param relations: a (url-encoded, space-delimited) string of predicate relation identifiers with which to constrain
    the statement relations retrieved  for the given query seed concept. The predicate ids sent should  be as published
    by the beacon-aggregator by the /predicates API endpoint.
    :type relations: str
    :param t: (optional) an array set of [CURIE-encoded](https://www.w3.org/TR/curie/)  identifiers of 'target'
    concepts possibly known to the beacon.  Unknown CURIEs should simply be ignored (silent match failure).
    :type t: List[str]
    :param keywords: a (url-encoded, space-delimited) string of keywords or substrings against which to match the
    subject, predicate or object names of the set of concept-relations matched by any of the input exact matching concepts
    :type keywords: str
    :param semanticGroups: a (url-encoded, space-delimited) string of semantic groups (specified as codes CHEM, GENE,
    ANAT, etc.) to which to constrain the subject or object concepts associated with the query seed concept
    (see [Semantic Groups](https://metamap.nlm.nih.gov/Docs/SemGroups_2013.txt) for the full list of codes)
    :type semanticGroups: str
    :param pageNumber: (1-based) number of the page to be returned in a paged set of query results 
    :type pageNumber: int
    :param pageSize: number of concepts per page to be returned in a paged set of query results 
    :type pageSize: int

    :rtype: List[Statement]
    """

    # This will only accept wd items in s and t
    # TODO: This can be made to handle other curies

    s = set(x for x in s if x.startswith("wd:"))
    t = set(x for x in t if x.startswith("wd:")) if t else {}
    relations = frozenset(relations.split(" ")) if relations else None
    keywords = frozenset(keywords.split(" ")) if keywords else None
    types = frozenset(semanticGroups.split(" ")) if semanticGroups else None

    datapage = lookup.query_and_filter_statements(s, t, relations, keywords, types)

    pageNumber = pageNumber if pageNumber else 1
    pageSize = pageSize if pageSize else 10

    start_idx = ((pageNumber - 1) * pageSize)
    end_idx = start_idx + pageSize

    datapage = datapage[start_idx:end_idx]
    return [Statement(**x) for x in datapage]
