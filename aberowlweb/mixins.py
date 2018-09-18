import re
from django.http import (
    Http404,
    HttpResponseRedirect,
    HttpResponse)

ACTION_RE = re.compile(r'\w+')


class FormRequestMixin(object):

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(FormRequestMixin, self).get_form_kwargs(*args, **kwargs)
        kwargs['request'] = self.request
        return kwargs

    
class ActionMixin(object):
    """Mixin for managing actions
    """

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        self.kwargs = kwargs

        if action is None or not ACTION_RE.search(action):
            return super(ActionMixin, self).post(request, *args, **kwargs)
        response = None
        do_action = getattr(self, 'on_{}'.format(action), None)
        if do_action is not None and callable(do_action):
            response = do_action(request, action)
        else:
            raise Http404

        if response is not None:
            return response
        return HttpResponseRedirect(self.get_success_url())
