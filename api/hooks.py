from tqdm.auto import tqdm
from proteus import reporting, logger


class TqdmUpWithReport(tqdm):
    """Provides `update_with_report(n)` which uses `tqdm.update(delta_n)`
    and sends a report with upload progress."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __enter__(self):
        logger.disabled = True
        return super().__enter__()

    def __exit__(self, *args):
        logger.disabled = False
        super().__exit__(*args)

    def update_with_report(self, n=1):
        status = "completed" if self.total == (self.n + n) else "processing"
        reporting.send(
            "uploading",
            status=status,
            progress=int((self.n + n) * 100 / self.total),
            number=self.n + n,
            total=self.total,
        )
        return self.update(n)
