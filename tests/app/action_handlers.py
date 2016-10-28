from actrack import ActionHandler


class MyActionHandler(ActionHandler):
    verb = 'my_action'


class MyIncludedActionHandler(ActionHandler):
    verb = 'my_included_action'

    @classmethod
    def combine(cls, actor, timestamp, **kwargs):
        # if there is any existing 'my_all_inclusive_action' we don't save this
        # one
        if cls.queue['my_all_inclusive_action']:
            return False


class MyAllInclusiveActionHandler(ActionHandler):
    verb = 'my_all_inclusive_action'

    @classmethod
    def combine(cls, actor, timestamp, **kwargs):
        """
        If there are any existing 'my_included_action', they are removed
        """
        if cls.queue['my_included_action']:
            del cls.queue['my_included_action'][:]
