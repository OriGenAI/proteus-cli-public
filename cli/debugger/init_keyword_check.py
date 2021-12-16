import re
from functools import partial
from api import api
from cli.config import config
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper
from multiprocessing.pool import Pool
from api.oidc import may_insist_up_to


PROTEUS_HOST, WORKERS_COUNT = (
    config.PROTEUS_HOST,
    config.WORKERS_COUNT,
)


def upload(bucket, dataset_uuid, workers=WORKERS_COUNT):
    try:
        assert api.auth.access_token is not None
        print(f"This process will use {workers} simultaneous threads.")
        with tqdm(total=0) as progress:
            total_expected, case_by_group_and_number = get_cases(
                api.auth, dataset_uuid, progress
            )
            load_from(
                case_by_group_and_number, bucket, progress, workers=workers
            )
    except KeyboardInterrupt:
        pass
    finally:
        api.auth.stop()


def get_cases(auth, dataset_uuid, progress):
    progress.set_description("retrieving cases and expected files")
    progress.refresh()
    cases_url = f"/api/v1/datasets/{dataset_uuid}/cases"
    response = api.get(cases_url)
    cases = response.json().get("cases")
    case_by_group_and_number = {}
    total = 0
    for case in cases:
        case_details = api.get(case.get("case_url")).json().get("case")
        key = f"{case.get('group')}-{case.get('number')}"
        case_by_group_and_number[key] = case_details
        total += 5 + (2 * case.get("steps", 0))
        progress.total = total
        progress.refresh()
    return total, case_by_group_and_number


def find_target(case_by_group_and_number, group=None, number=None, **other):
    if group is None or number is None:
        return None
    return case_by_group_and_number.get(f"{group}-{number}")



@may_insist_up_to(5, delay_in_secs=5)
def parallelized_upload(
    item_and_path, case_by_group_and_number, processed, skipped_count
):
    item, path, reference = item_and_path
    matchs_as_case = case_re.match(path)
    terms = matchs_as_case.groupdict() if matchs_as_case is not None else {}
    target = find_target(case_by_group_and_number, **terms)
    if target is None:
        skipped_count += 1
    else:
        content = terms.get("content")
        matchs = _timestep.match(content) or _sheet_extension.match(content)
        if matchs:
            if is_pending(matchs, target):
                done, skipped = send_as(
                    target, item, reference, **terms, **matchs.groupdict()
                )
                processed += done
                skipped_count += skipped
            else:
                processed += 1

    return processed



