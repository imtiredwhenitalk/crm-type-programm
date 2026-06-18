_state = {'user': None}


class _CurrentUser:
    """Mutable proxy so all modules share the same logged-in user."""

    def _u(self):
        if _state['user'] is None:
            return {'username': 'system', 'role': 'user', 'id': 0,
                    'phone': '', 'email': '', 'org': '', 'department': ''}
        return _state['user']

    def __getitem__(self, key):
        return self._u()[key]

    def __setitem__(self, key, value):
        self._u()[key] = value

    def get(self, key, default=None):
        return self._u().get(key, default)

    def update(self, data):
        self._u().update(data)

    def __contains__(self, key):
        return key in self._u()

    def __repr__(self):
        return repr(self._u())


current_user = _CurrentUser()


def set_current_user(user):
    _state['user'] = user
