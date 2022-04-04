from tqdm.auto import tqdm
from proteus import Reporting, logger


class TqdmUpWithReport(tqdm):
    """Provides `update_with_report(n)` which uses `tqdm.update(delta_n)`
    and sends a report with upload progress."""

    def __init__(self, reporting=Reporting(), **kwargs):
        super().__init__(**kwargs)
        self.reporting = reporting

    def __enter__(self):
        logger.disabled = True
        return super().__enter__()

    def __exit__(self):
        logger.disabled = False
        super().__exit__()

    def update_with_report(self, n=1):
        self.reporting.send(
            "uploading",
            status="processing",
            progress=int((self.n + n) * 100 / self.total),
            number=self.n + n,
            total=self.total,
        )
        return self.update(n)
