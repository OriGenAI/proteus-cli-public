from config import config
from api import api
from common.logger import logger
from common.reporting import Reporting


def acquire_result(output):
    progress = None
    result = None
    if output is None:
        pass
    elif type(output) in [list, tuple] and len(output) == 2:
        progress, result = output
    else:
        progress = output
    return progress, result


class CommonLifecycle:

    __steps__ = ["declare_processing", "load_entity"]

    def __init__(self, session=api, context={}):
        self.context = context
        self.report = Reporting(logger, session)

    def load_entity(self):
        entity_res = api.get(config.ENTITY_URL)
        self.context["entity"] = dict(**entity_res.json())

    def declare_processing(self):
        return self.report.send(
            "started to operate", status="processing", progress=0
        )

    def _report_method_starts(self, method):
        method_name = method.__doc__ or method.__name__
        return self.report.send(f"Starting {method_name}", status="processing")

    def _report_method_ends(self, method, progress, result):
        method_name = method.__doc__ or method.__name__
        status = "completed" if progress == 100 else "processing"
        return self.report.send(
            f"Done {method_name}",
            status=status,
            progress=progress,
            result=result,
        )

    def run(self):
        for step in self.__class__.__steps__:
            try:
                method = getattr(self.__class__, step)
                self._report_method_starts(method)
                progress, result = acquire_result(method(self))
                self._report_method_ends(method, progress, result)
            except Exception as error:
                self.report.error(error, status="failed")
                raise error from error
