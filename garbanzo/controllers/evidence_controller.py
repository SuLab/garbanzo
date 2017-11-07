import connexion
import requests

from garbanzo.models.annotation import Annotation
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime


def get_evidence(statementId, keywords=None, pageNumber=None, pageSize=None):
    """
    get_evidence
    Retrieves a (paged) list of annotations cited as evidence for a specified concept-relationship statement 
    :param statementId: (url-encoded) CURIE identifier of the concept-relationship statement (\&quot;assertion\&quot;, \&quot;claim\&quot;) for which associated evidence is sought 
    :type statementId: str
    :param keywords: (url-encoded, space delimited) keyword filter to apply against the label field of the annotation 
    :type keywords: str
    :param pageNumber: (1-based) number of the page to be returned in a paged set of query results 
    :type pageNumber: int
    :param pageSize: number of cited references per page to be returned in a paged set of query results 
    :type pageSize: int

    :rtype: List[Annotation]
    """
    # example url: https://www.wikidata.org/w/api.php?action=wbgetclaims&claim=Q7758678$1187917E-AF3E-4A5C-9CED-6F2277568D29
    if '$' not in statementId:
        statementId = statementId.replace("-", '$', 1)

    # support both curied and not-curied statement Ids
    if statementId.lower().startswith("wds:"):
        statementId = statementId[4:]

    params = {'action': 'wbgetclaims',
              'claim': statementId,
              'format': 'json'}
    r = requests.get("https://www.wikidata.org/w/api.php", params=params)
    r.raise_for_status()
    d = r.json()
    pid = list(d['claims'].keys())[0]
    qid = statementId.split("$")[0].upper()
    url = "https://www.wikidata.org/wiki/{}#{}".format(qid, pid)

    # but always return curied IDs
    return [Annotation(id=url)]
