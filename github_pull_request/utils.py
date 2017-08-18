
def namedtype(typename, fields):
    """
        Factory function for ceating named types. This is similar to
        python's namedtuple but for dictionaries and allows optional
        parameters. It is not safe to use for arbitry field names, but
        ok if you know your field names won't collide with dict().
    """
    if isinstance(fields, basestring):
        fields = [f.strip() for f in fields.split(',')]
    else:
        fields = list(fields)
    return type(typename, (_namedtype,), {'_fields': fields})


class _namedtype(dict):
    """
    This class is similar to namedtuple, except that the constructor does not
    require all arguments to be present and will ignore addtional kwargs. It is
    backed by a dict and is not careful to check for name collisions with
    built in attributes so is not safe to use for arbitrary data.

    Example use:
        User = namedtype('User', 'first_name, last_name, email')
        user = User(first_name='First', last_name='Last', extra='ignored')

        user.first_name => 'First'
        user.last_name => 'Last'
        user.email => None
        user.extra => AttributeError
    """
    @property
    def _fields(self):
        return self.__class__._fields

    def __init__(self, *args, **kwargs):
        for k in kwargs.keys():
            if k not in self._fields:
                kwargs.pop(k)
        for f in self._fields:
            if f not in kwargs:
                kwargs[f] = None
        super(_namedtype, self).__init__(*args, **kwargs)

    def __getattr__(self, name):
        if name in self._fields:
            return self.get(name)
        else:
            raise AttributeError('No such attribute: ' + name)

    def __setattr__(self, name, value):
        if name in self._fields:
            self[name] = value
        else:
            raise AttributeError('No such attribute: ' + name)

    def __delattr__(self, name):
        if name in self._fields:
            del self[name]
        else:
            raise AttributeError('No such attribute: ' + name)

    def __repr__(self):
        field_str = ', '.join(['{}={}'.format(f, self[f]) for f in self._fields])
        return '{}({})'.format(self.__class__.__name__, field_str)
