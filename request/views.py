import notmuch
import sys, json
from django.http import HttpResponse

from request import search
from request import action

def manage (request) :
    response = {
        'ok' : False
    }

    if request.method == 'GET' :
        try :
            data = json.loads (request.GET.get ('command'))
        except :
            response ['message'] = str (sys.exc_info() [0]) + " on GET 'command' json decoding"
            return HttpResponse (content = json.dumps(response), content_type = "text/plain")
    elif request.method == 'POST' :
        try :
            data = json.loads (request.POST.get ('command'))
        except :
            response ['message'] = str (sys.exc_info()) + " on POST 'command' json decoding"
            return HttpResponse (content = json.dumps(response), content_type = "text/plain")
    else :
        response ['message'] = "Only GET and POST http method are accepted"
        return HttpResponse (content = json.dumps(response), content_type = "text/plain")

    if 'search' in data :
        response ['search_response'] = []
        for s in data ['search'] :
            try :
                search_response = search.manage (s);
            except :
                response ['message'] = str (sys.exc_info()) + " on request " + str (s)
                return HttpResponse (content = json.dumps(response), content_type = "text/plain")

            response ['search_response'].append ({
                'request' : s,
                'response' : search_response
            })

    if 'action' in data :
        response ['action_response'] = []
        for a in data ['action'] :
            try :
                action_response = action.manage (a);
            except :
                response ['message'] = str (sys.exc_info() [0]) + " on request " + str (a)
                return HttpResponse (content = json.dumps(response), content_type = "text/plain")

            response ['action_response'].append ({
                'request' : a,
                'response' : action_response
            })
    response ['ok'] = True
    return HttpResponse (content = json.dumps(response), content_type = "text/plain")
