import os
import stat
from cli.config import config
import subprocess
import threading
import click


OPM_FLOW_PATH = config.OPM_FLOW_PATH


def exists_file(filepath):
    try:
        mode = os.stat(filepath).st_mode
        return stat.S_ISREG(mode)
    except FileNotFoundError:
        pass
    return False


def is_executable(filepath):
    try:
        mode = os.stat(filepath).st_mode
        return stat.S_ISREG(mode) and bool(mode & stat.S_IXUSR)
    except FileNotFoundError:
        pass
    return False


OPM_FLOW_INSTALL_INSTRUCTIONS = (
    ""
    f"OPM Flow is not available or can't be found at {OPM_FLOW_PATH}\n"
    "if it's already installed on your system set the path on OPM_FLOW_PATH\n"
    "enviroment variable\n"
    "\n"
    "To install follow these instructions https://opm-project.org/?page_id=36"
)
OPM_FLOW_PATH_CANT_BE_EMPTY = "" "OPM_FLOW_PATH can't be set to empty string."


def opm_flow_is_available():
    assert len(OPM_FLOW_PATH) > 0, OPM_FLOW_PATH_CANT_BE_EMPTY
    assert is_executable(OPM_FLOW_PATH), OPM_FLOW_INSTALL_INSTRUCTIONS


def grid_of_datafile(path):
    return path.replace(".DATA", ".EGRID")


def balance_state_of_datafile(path):
    return path.replace(".DATA", ".X0000")


def init_of_datafile(path):
    return path.replace(".DATA", ".X0000")


def discard_till_error(data_str):
    error_index = data_str.find("Error: ")
    return data_str[error_index:]


def cause_of_error(process):
    outs, errs = process.communicate()
    report = errs.decode("utf-8") if len(errs) > 0 else discard_till_error(outs.decode("utf-8"))
    return report


class OPMSupervisedExecution:
    """Supervised Execution audits flow execution waiting for a specific output
    to interrupt the simulation at the first step"""

    def __init__(self, ctx, process, breakpoint=None):
        self._supervise = None
        self._process = process
        self._ctx = ctx
        self._breakpoint = breakpoint
        self._breakpoint_len = 10000 if breakpoint is None else len(breakpoint)
        self._active = False
        self._stdout = ""

    def enable_safe_close(self):
        @self._ctx.call_on_close
        def end_process_thread():
            self._end()

    def _end(self):
        self._active = False
        self._process.terminate()
        self._exit_code = self._process.wait()

    def _meets_breakpoint(self, line):
        if len(line) < self._breakpoint_len:
            return False
        return line[: self._breakpoint_len] == self._breakpoint

    def _subprocess_is_active(self):
        return self._process.poll() is None

    def attend_subprocess_output(self):
        try:
            while self._active and self._subprocess_is_active():
                stdout_line = self._process.stdout.readline().decode("utf-8")
                if self._meets_breakpoint(stdout_line):
                    break
                self._stdout += stdout_line
        except click.Abort as error:
            self._active = False
            raise error from error
        finally:
            print("OPM: Deactivating supervising thread and subprocess")
            self._end()

    def cause_of_error(self):
        return discard_till_error(self._stdout)

    def __enter__(self):
        supervise = threading.Thread(target=self.attend_subprocess_output)
        try:
            self.enable_safe_close()
            self._active = True
            supervise.start()
            return self
        finally:
            supervise.join()

    def __exit__(self, *args):
        self._end()

    @classmethod
    def on(cls, context, process, breakpoint):
        return cls(context, process, breakpoint=breakpoint)


def run_opm_flow_on(data_filepath, cacheable=False):
    assert exists_file(data_filepath), f"DATA file not found at {data_filepath}"
    grid_filepath = grid_of_datafile(data_filepath)
    assert exists_file(grid_filepath), f"GRID file not found at {grid_filepath}"
    init_filepath = init_of_datafile(data_filepath)
    balance_state_filepath = balance_state_of_datafile(data_filepath)
    if cacheable and exists_file(init_filepath) and exists_file(balance_state_filepath):
        return [balance_state_filepath, init_filepath, grid_filepath]
    process = subprocess.Popen(
        [
            OPM_FLOW_PATH,
            "--solver-max-time-step-in-days=1",
            "--enable-dry-run=false",
            data_filepath,
        ],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    ctx = click.get_current_context()
    breakpoint = "Starting time step 1"
    with OPMSupervisedExecution.on(ctx, process, breakpoint) as execution:
        exit_code = execution._exit_code
        assert exit_code in [0, -15], (
            f"OPM flow on {data_filepath} failed with exit code {exit_code}:\n" + execution.cause_of_error()
        )
    init_filepath = init_of_datafile(data_filepath)
    assert exists_file(init_filepath), f"INIT file not found at {init_filepath} after run"
    assert exists_file(balance_state_filepath), f"X0000 file not found at {balance_state_filepath} after run"
    return [balance_state_filepath, init_filepath, grid_filepath]
