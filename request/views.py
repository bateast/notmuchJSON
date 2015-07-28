import notmuch
import sys, json
from django.http import HttpResponse

import request.search, request.action

def manage (request) :
    response = {
        'ok' : False,
        'message' : "request not found"
    }

    if request.method == 'GET' :
        data = request.GET.get ('')
    elif request.method == 'POST' :
        data = request.POST.get ('')
    else :
        response ['message'] = "Only GET and POST http method are accepted"
        return HttpResponse (content = json.dumps(response), content_type = "text/plain")

    response ['search_response'] = []
    for search in request ['search'] :
        try :
            search_response = request.seach.manage (search);
        except :
            response ['message'] = sys.exc_info() [0] + " on request " + search
            return HttpResponse (content = json.dumps(response), content_type = "text/plain")

        response ['search_response'].append ({
            'request' : search,
            'response' : search_response
        })

    response ['action_response'] = []
    for action in request ['action'] :
        try :
            action_response = request.action.manage (action);
        except :
            response ['message'] = sys.exc_info() [0] + " on request " + action
            return HttpResponse (content = json.dumps(response), content_type = "text/plain")

        response ['action_response'].append ({
            'request' : action,
            'response' : action_response
        })
