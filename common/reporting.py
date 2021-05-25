class Reporting:
    """Unifies logging and reporting to status API"""

    def __init__(self, logger, api):
        self.logger = logger
        self.api = api

    def send(self, message, status="processing", progress=0, result=None):
        assert status is not None, "Status can't be set to None"
        self.logger.info(
            message,
            extra={"status": status, "progress": progress, "result": result},
        )
        self.api.report(
            str(status),
            message=message,
            progress=progress,
            result=result,
        )

    def error(self, error, status=None, progress=-1):
        self.logger.error(
            "exception occurred",
            exc_info=True,
            extra={"status": status, "progress": progress},
        )
        self.api.report(
            str(status),
            message=f"exception occurred: {error}",
            progress=progress,
        )
