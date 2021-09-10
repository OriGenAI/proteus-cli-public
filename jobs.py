from api import api
from tabulate import tabulate
import readchar


def get_status(uuid):
    response = api.get(f"/api/v1/jobs/{uuid}/status")
    response.raise_for_status()
    return response.json()


job_columns = [
    {"label": "Creation", "field": "created"},
    {"label": "Last update", "field": "modified"},
    {"label": "Entity name", "field": "entity_name"},
    {"label": "Status", "field": "status"},
    {"label": "UUID", "field": "uuid"},
]

MISSING = "* not found *"

ALLOWED_KEYS = ["n", "b", "q"]

COMMANDS_TEXT = "Press n (continue), b (back), q (exit)"


def data_of_job(item):
    return [item.get(column.get("field"), MISSING) for column in job_columns]


job_headers = [column.get("label") for column in job_columns]


def has_next(data):
    if data is None:
        return False
    return data.get("next", False)


def has_prev(data):
    if data is None:
        return False
    return data.get("prev", False)


def api_load(url):
    response = api.get(url)
    response.raise_for_status()
    return response.json()


def receive_command():
    while True:
        command = readchar.readkey()
        if command in ALLOWED_KEYS:
            return command


def list_jobs(target_type, rows=25 - 3):
    url = f"/api/v1/jobs?target_type={target_type}&per_page={rows}"
    command = None
    data = None
    while command is not False:
        if command == "q":
            break
        next_ = has_next(data)
        if command == "n" and next_ is not False:
            url = next_
        prev_ = has_prev(data)
        if command == "b" and prev_ is not False:
            url = prev_
        data = api_load(url)
        page, pages = data["page"], data["pages"]
        print(
            f"Listing {target_type} jobs page {page} of {pages}"
            f", {COMMANDS_TEXT}"
        )
        content = [data_of_job(item) for item in data.get("results", [])]
        table = tabulate(content, job_headers)
        print(table)
        command = receive_command()
