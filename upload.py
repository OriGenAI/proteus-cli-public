import boto3
import os
import re
import multiprocessing as mp
from functools import partial
from api import api
from config import config
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper
from multiprocessing.dummy import Pool as ThreadPool    
from api.oidc import may_insist_up_to

PROTEUS_HOST, S3_REGION = config.PROTEUS_HOST, config.S3_REGION

client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_SERVER_PUBLIC_KEY"),
    aws_secret_access_key=os.getenv("AWS_SERVER_SECRET_KEY"),
    region_name=S3_REGION,
    config=boto3.session.Config(
        signature_version="s3v4", s3={"addressing_style": "path"}
    ),
)


s3_uri_re = re.compile(
    r"^s3://(?P<bucket_name>[a-zA-Z0-9.\-_]{1,255})/(?P<prefix>.*)$"
)

case_re = re.compile(
    r"(?P<root>.*/(?P<group>validation|training|testing)"
    r"/SIMULATION_(?P<number>\d+))/(?P<content>.*)"
)

_sheet_extension = re.compile(
    r".*(?P<extension>DATA|EGRID|INIT|SMSPEC|GRDECL)$"
)

_timestep = re.compile(r".*(?P<extension>X\d{4}|S\d{4})$")


def list_bucket_contents(bucket_uri):
    match = s3_uri_re.match(bucket_uri)
    assert match is not None, f"{bucket_uri} must be an s3 URI"
    terms = match.groupdict()
    paginator = client.get_paginator("list_objects")
    page_iterator = paginator.paginate(
        Bucket=terms.get("bucket_name"),
        Prefix=terms.get("prefix"),
    )
    for page in page_iterator:
        for item in page["Contents"]:
            yield item


def upload_dataset(bucket, dataset_uuid):
    try:
        assert api.auth.access_token is not None
        total_expected, case_by_group_and_number = get_cases(
            api.auth, dataset_uuid
        )
        with tqdm(total=total_expected) as progress:
            load_from(case_by_group_and_number, bucket, progress)
    except KeyboardInterrupt:
        pass
    finally:
        api.auth.stop()


def get_cases(auth, dataset_uuid):
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
    return total, case_by_group_and_number


def find_target(case_by_group_and_number, group=None, number=None, **other):
    if group is None or number is None:
        return None
    return case_by_group_and_number.get(f"{group}-{number}")


def load_from(case_by_group_and_number, bucket_uri, progress, workers=10):
    skipped_count = 0
    processed = 0
    progress.update(processed)
    items = list_bucket_contents(bucket_uri)
    upload_partial = partial(parallelized_upload, case_by_group_and_number=case_by_group_and_number, progress=progress, processed=processed, skipped_count=skipped_count)
    from multiprocessing.dummy import Pool as ThreadPool    
    pool = ThreadPool(workers)
    pool.map(upload_partial, items)

@may_insist_up_to(5, delay_in_secs=1)
def parallelized_upload(item, case_by_group_and_number, progress, processed, skipped_count):
    path = item.get("Key")
    matchs_as_case = case_re.match(path)
    terms = (
        matchs_as_case.groupdict() if matchs_as_case is not None else {}
    )
    target = find_target(case_by_group_and_number, **terms)
    if target is None:
        skipped_count += 1
        progress.set_postfix_str(
            s=f"{skipped_count} files skipped last one: {path}"
        )
    else:
        content = terms.get("content")
        matchs = _timestep.match(content) or _sheet_extension.match(
            content
        )
        if matchs and is_pending(matchs, target):
            progress.set_postfix_str(s=f"transfering file {path}")
            done, skipped = send_as(
                target, path, **terms, **matchs.groupdict()
            )
            processed += done
            skipped_count += skipped
    progress.update(processed)

def is_pending(match, target):
    extension = match.groupdict().get("extension")
    missing_core = target.get("missing_parts").get("core")
    if extension in missing_core:
        return True
    missing_steps = target.get("missing_parts").get("steps")
    if extension in missing_steps:
        return True
    return False


def send_as(
    target, source_path, group=None, number=None, extension=None, **other
):
    target_url = target.get("case_url")
    source_response = client.get_object(
        Bucket="client-research-data", Key=source_path
    )
    file_size = source_response["ContentLength"]
    source = source_response["Body"]
    modified = source_response["LastModified"]
    done = 0
    skipped = 0
    transfer = None
    try:
        with tqdm(
            total=file_size, unit="B", unit_scale=True, unit_divisor=1024
        ) as progress:
            progress.set_description(f"uploading {source_path}")
            wrapped_file = CallbackIOWrapper(progress.update, source, "read")
            transfer = api.post_file(
                target_url,
                source_path,
                content=wrapped_file,
                modified=modified,
            )
            progress.set_description(f"uploaded {source_path}")
            source.close()
            assert transfer.json()
            progress.close()
            if transfer.status_code == 201:
                done = 1
            elif transfer.status_code == 200:
                skipped = 1
            else:
                print("transfer failed", transfer.content)

    except Exception as error:
        if transfer is not None:
            print(transfer.content)
        raise error
    return done, skipped
