from tqdm.auto import tqdm
from cli.common.reporting import Reporting


class TqdmUpWithReport(tqdm):
    """Provides `update_to(n)` which uses `tqdm.update(delta_n)`."""

    def __init__(self, reporting=Reporting.new(), **kwargs):
        super().__init__(**kwargs)
        self.reporting = reporting

    def update_with_report(self, n=1):
        self.reporting.send(
            "uploading",
            status="processing",
            progress=self.n + n,
            total=self.total,
        )
        return self.update(n)
