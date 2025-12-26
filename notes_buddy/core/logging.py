import logging


class RequestIDLogFilter(logging.Filter):
    def filter(self, record):

        from notes_buddy.core.middleware import get_request_id
        record.request_id = get_request_id()
        return True