import readchar
from tabulate import tabulate

from cli.runtime import proteus

job_columns = [
    {"label": "Creation", "field": "created"},
    {"label": "Last update", "field": "modified"},
    {"label": "Entity name", "field": "entity_name"},
    {"label": "Status", "field": "status"},
    {"label": "UUID", "field": "uuid"},
]

job_status_columns = [
    {"label": "At", "field": "at"},
    {"label": "Status", "field": "set_status"},
    {"label": "Progress", "field": "progress"},
    {"label": "Message", "field": "message"},
]

MISSING = "* not found *"

ALLOWED_KEYS = ["n", "b", "q"]

COMMANDS_TEXT = "Press n (continue), b (back), q (exit)"


def as_row(columns):
    def whatever_as_columns(item):
        return [item.get(column.get("field"), MISSING) for column in columns]

    return whatever_as_columns


def has_next(data):
    if data is None:
        return None
    return data.get("next", None)


def has_prev(data):
    if data is None:
        return None
    return data.get("prev", None)


def api_load(url):
    response = proteus.api.get(url)
    response.raise_for_status()
    return response.json()


def receive_command():
    while True:
        command = readchar.readkey()
        if command in ALLOWED_KEYS:
            return command


def view(data, render_row=None, headers=None):
    content = [render_row(item) for item in data.get("results", [])]
    table = tabulate(content, headers)
    print(table)


job_as_row = as_row(job_columns)
job_headers = [column.get("label") for column in job_columns]


def list_jobs(target_type, rows=25 - 3):
    url = f"/api/v1/jobs?target_type={target_type}&per_page={rows}"
    command = None
    data = None
    while command is not False:
        if command == "q":
            break
        next_ = has_next(data)
        if command == "n" and next_ is not None:
            url = next_
        prev_ = has_prev(data)
        if command == "b" and prev_ is not None:
            url = prev_
        data = api_load(url)
        page, pages = data["page"], data["pages"]
        print("\n" f"Listing jobs page {page} of {pages}" f", {COMMANDS_TEXT}")
        view(data, render_row=job_as_row, headers=job_headers)
        command = receive_command()


job_status_as_row = as_row(job_status_columns)
job_status_headers = [column.get("label") for column in job_status_columns]


def list_job_status(uuid):
    url = f"/api/v1/jobs/{uuid}/status"
    command = None
    data = None
    while command is not False:
        if command == "q":
            break
        next_ = has_next(data)
        if command == "n" and next_ is not None:
            url = next_
        prev_ = has_prev(data)
        if command == "b" and prev_ is not None:
            url = prev_
        data = api_load(url)
        page, pages = data["page"], data["pages"]
        print("\n" f"Listing job status page {page} of {pages}" f", {COMMANDS_TEXT}")
        view(data, render_row=job_status_as_row, headers=job_status_headers)
        command = receive_command()
