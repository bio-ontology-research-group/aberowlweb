from django import http


class CorsMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        request_url = request.get_full_path()
        if '/api/dlquery' not in request_url:
            if (request.method == "OPTIONS"  and "HTTP_ACCESS_CONTROL_REQUEST_METHOD" in request.META):
                response = http.HttpResponse()
                response["Content-Length"] = "0"
                response["Access-Control-Max-Age"] = 86400

            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Headers"] = "accept, accept-encoding, authorization, content-type, origin, x-csrftoken, x-requested-with"
            
        return response