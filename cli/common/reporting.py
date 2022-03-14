from cli.common.logger import logger


class VoidReporting:
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

    @classmethod
    def error(self, msg, extra=None):
        logger.error(msg, exc_info=True, extra=extra)

    @classmethod
    def info(self, msg):
        logger.info(msg)


class Reporting:
    """Unifies logging and reporting to status API"""

    @classmethod
    def new(cls, api=None):
        if api is None or api.auth.worker_uuid is None:
            return VoidReporting()

        return cls(api=api)

    def __init__(self, api):
        self.api = api
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
        logger.info(
            message,
            extra={"status": status, "progress": progress, "result": result},
        )
        self.report(
            self.worker_uuid,
            set_status=str(status),
            message=message,
            progress=progress,
            result=result,
            total=total,
            number=number,
        )

    def report(
        self,
        worker_uuid,
        set_status="processing",
        message=None,
        progress=0,
        result=None,
        total=None,
        number=None,
    ):
        status_url = f"/api/v1/jobs/{worker_uuid}/status"
        data = {
            "set_status": set_status,
            "progress": progress,
        }
        report = {}
        if message is not None:
            report["message"] = message
        if result is not None:
            report["result"] = result
        report["number"] = number
        report["total"] = total
        data["report"] = report
        response = self.api.post(status_url, data)
        response.raise_for_status()
        return response

    @classmethod
    def error(self, msg, extra=None):
        logger.error(msg, exc_info=True, extra=extra)

    @classmethod
    def info(self, msg):
        logger.info(msg)
