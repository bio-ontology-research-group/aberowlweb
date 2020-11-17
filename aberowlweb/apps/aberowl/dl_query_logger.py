# Http interceptor for logging complex Description Logic queries
#
# The current implementation logs the data in a text file with every log
# entry in json format.

import json
import os
import urllib.parse as parse

from datetime import datetime
from django.conf import settings

LOG_FOLDER = getattr(
    settings, 'DLQUERY_LOGS_FOLDER', 'dl')

def append_log(log_entry):
    os.makedirs(LOG_FOLDER, exist_ok=True)
    with open('{log_folder}/aberowl-dl-logs.txt'.format(log_folder=LOG_FOLDER), 'a') as file:
        json.dump(log_entry, file)
        file.write(os.linesep)

def is_query_complex(query):
    if query is None:
        return False

    query = query.strip()
    # query with one part
    if not query or  ' ' not in query:
        return False
    
    # query with more than one part
    if "'" not in query and " " in query:
        return True

    # query with qoutes and have more than one part
    if "'" in query:
        secondOccurance = query.find("'", query.find("'") + 1)
        if secondOccurance > -1 and len(query[secondOccurance + 1:]) > 0:
            return True
    
    return False

def DLQueryLogger(get_response):
    def middleware(request):
        response = get_response(request)
        request_url = request.get_full_path()
        query = request.GET.get('query', None)
        if '/api/dlquery' not in request_url:
            return response

        if query is None:
            return response

        if not is_query_complex(query):
            return response

        query_string = request.GET.urlencode()
        entry = parse.parse_qs(query_string)
        entry['time'] = str(datetime.now())

        append_log(entry)
        return response #response should be defined before

    return middleware

