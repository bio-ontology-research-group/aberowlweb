class FormRequestMixin(object):

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(FormRequestMixin, self).get_form_kwargs(*args, **kwargs)
        kwargs['request'] = self.request
        return kwargs
