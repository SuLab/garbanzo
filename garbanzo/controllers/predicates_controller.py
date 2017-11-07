import connexion
from garbanzo.models.predicate import Predicate
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime


def get_predicates():
    """
    get_predicates
    Get a list of predicates used in statements issued by the knowledge source 

    :rtype: List[Predicate]
    """
    return []
