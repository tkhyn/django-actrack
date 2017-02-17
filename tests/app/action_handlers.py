from actrack import ActionHandler


class MyActionHandler(ActionHandler):
    verb = 'my_action'


class MyIncludedActionHandler(ActionHandler):
    verb = 'my_included_action'

    def combine_with_my_all_inclusive_action(self, kws_self, kws_other):
        # if there is any existing 'my_all_inclusive_action' we don't save this
        # one
        return True


class MyAllInclusiveActionHandler(ActionHandler):
    verb = 'my_all_inclusive_action'
