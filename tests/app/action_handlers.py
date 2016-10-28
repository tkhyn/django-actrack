from actrack import ActionHandler


class MyActionHandler(ActionHandler):
    verb = 'my_action'


class MyIncludedActionHandler(ActionHandler):
    verb = 'my_included_action'

    @classmethod
    def combine_with_my_all_inclusive_action(cls, kwargs):
        # if there is any existing 'my_all_inclusive_action' we don't save this
        # one
        return True


class MyAllInclusiveActionHandler(ActionHandler):
    verb = 'my_all_inclusive_action'
