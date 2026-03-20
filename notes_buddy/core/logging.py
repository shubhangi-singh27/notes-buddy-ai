import logging


class RequestIDLogFilter(logging.Filter):
    def filter(self, record):
        from notes_buddy.core.middleware import get_request_id
        rid = get_request_id()
        record.request_id = rid if rid is not None else '-'
        return True