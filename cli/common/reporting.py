import cli.common


class VoidReporting:
    def __init__(self, logger=cli.common.logger):
        self.logger = logger

    def send(
        self,
        message,
        status="processing",
        progress=0,
        result=None,
        total=None,
        number=None,
    ):
        pass

    def error(self, error, status=None, progress=-1):
        pass


class Reporting:
    """Unifies logging and reporting to status API"""

    @classmethod
    def new(cls, api=None, logger=cli.common.logger):
        if api is None or api.auth.worker_uuid is None:
            return VoidReporting()

        return cls(api=api, logger=logger)

    def __init__(self, api, logger=cli.common.logger):
        self.api = api
        self.logger = logger
        self.worker_uuid = api.auth.worker_uuid

    def send(
        self,
        message,
        status="processing",
        progress=0,
        result=None,
        total=None,
        number=None,
    ):
        assert status is not None, "Status can't be set to None"
        self.logger.info(
            message,
            extra={"status": status, "progress": progress, "result": result},
        )
        self.api.report(
            self.worker_uuid,
            set_status=str(status),
            message=message,
            progress=progress,
            result=result,
            total=total,
            number=number,
        )

    def error(self, error, status=None, progress=-1):
        self.logger.error(
            "exception occurred",
            exc_info=True,
            extra={"status": status, "progress": progress},
        )
        self.api.report(
            self.worker_uuid,
            str(status),
            message=f"exception occurred: {error}",
            progress=progress,
        )
