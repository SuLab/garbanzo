import connexion
from werkzeug.exceptions import abort

from garbanzo import lookup
from garbanzo.models.concept import Concept
from garbanzo.models.concept_with_details import ConceptWithDetails
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime


def get_concept_details(conceptId):
    """
    get_concept_details
    Retrieves details for a specified concepts in the system, as specified by a (url-encoded) CURIE identifier of a concept known the given knowledge source. 
    :param conceptId: (url-encoded) CURIE identifier of concept of interest
    :type conceptId: str

    :rtype: List[ConceptWithDetails]
    """
    # Retrieves details for a specified concept in Wikidata
    # only accepts wd:Q####
    if not conceptId.startswith("wd:"):
        return []
    try:
        concept = lookup.getConcept(conceptId)
        details = lookup.get_concept_details(conceptId)
        concept['details'] = details
        return [concept]
    except Exception:
        return []


def get_concepts(keywords, semanticGroups=None, pageNumber=None, pageSize=None):
    """
    get_concepts
    Retrieves a (paged) list of concepts in the system 
    :param keywords: a (urlencoded) space delimited set of keywords or substrings against which to match concept names and synonyms
    :type keywords: str
    :param semanticGroups: a (url-encoded) space-delimited set of semantic groups (specified as codes CHEM, GENE, ANAT, etc.) to which to constrain concepts matched by the main keyword search (see [Semantic Groups](https://metamap.nlm.nih.gov/Docs/SemGroups_2013.txt) for the full list of codes) 
    :type semanticGroups: str
    :param pageNumber: (1-based) number of the page to be returned in a paged set of query results 
    :type pageNumber: int
    :param pageSize: number of concepts per page to be returned in a paged set of query results 
    :type pageSize: int

    :rtype: List[Concept]
    """
    keywords = keywords.split(" ")
    semgroups = semanticGroups
    semgroups = semgroups.split(" ") if semgroups else []
    pageNumber = pageNumber if pageNumber else 1
    pageSize = pageSize if pageSize else 10
    if pageSize > 50:
        abort(400, "pageSize can not be greater than 50")

    dataPage = lookup.search_wikidata(keywords, semgroups=semgroups, pageNumber=pageNumber, pageSize=pageSize)

    return dataPage
