from tqdm.auto import tqdm
from cli.common.reporting import Reporting


class TqdmUpWithReport(tqdm):
    """Provides `update_with_report(n)` which uses `tqdm.update(delta_n)`
    and sends a report with upload progress."""

    def __init__(self, reporting=Reporting.new(), **kwargs):
        super().__init__(**kwargs)
        self.reporting = reporting
        self.reporting.logger.disabled = True

    def update_with_report(self, n=1):
        self.reporting.send(
            "uploading",
            status="processing",
            progress=int((self.n + n) * 100 / self.total),
            number=self.n + n,
            total=self.total,
        )
        return self.update(n)
