import boto3
import os
import re
from api import api
from config import config
import requests
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper


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


def list_bucket_contents(bucket, prefix):
    paginator = client.get_paginator("list_objects")
    page_iterator = paginator.paginate(
        Bucket=bucket,
        Prefix=prefix,
    )
    for page in page_iterator:
        for item in page["Contents"]:
            yield item


case_re = re.compile(
    r"(?P<root>.*/(?P<group>validation|training|testing)/SIMULATION_(?P<number>\d+))/(?P<content>.*)"
)

_sheet_extension = re.compile(r".*(?P<extension>DATA|EGRID|INIT|SMSPEC|GRDECL)$")

_timestep = re.compile(r".*(?P<extension>X\d{4}|S\d{4})$")


def upload_dataset(bucket, prefix, dataset_uuid):
    try:
        assert api.auth.access_token is not None
        total_expected, case_by_group_and_number = get_cases(api.auth, dataset_uuid)
        with tqdm(total=total_expected) as progress:
            load_from(case_by_group_and_number, bucket, prefix, progress)
    except KeyboardInterrupt:
        pass
    finally:
        api.auth.stop()


def get_cases(auth, dataset_uuid):
    # ceba91e4-53ab-4dbb-8488-34ee655f2ce0
    cases_url = f"/api/v1/datasets/{dataset_uuid}/cases"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth.access_token}",
    }
    
    response = requests.get(f"{PROTEUS_HOST}{cases_url}", headers=headers)
    cases = response.json().get("cases")

    case_by_group_and_number = {}
    total = 0
    for case in cases:
        key = f"{case.get('group')}-{case.get('number')}"
        case_by_group_and_number[key] = case.get("case_url")
        total += 5 + (2 * case.get("steps", 0))
    return total, case_by_group_and_number


def find_target(case_by_group_and_number, group=None, number=None, **other):
    if group is None or number is None:
        return None
    return case_by_group_and_number.get(f"{group}-{number}")


def load_from(case_by_group_and_number, bucket, prefix, progress):
    skipped_count = 0
    processed = 0
    progress.update(processed)
    for item in list_bucket_contents(bucket, prefix):
        path = item.get("Key")
        matchs_as_case = case_re.match(path)
        terms = matchs_as_case.groupdict() if matchs_as_case is not None else {}
        target = find_target(case_by_group_and_number, **terms)
        if target is None:
            skipped_count += 1
            progress.set_postfix_str(
                s=f"{skipped_count} files skipped last one: {path}"
            )
        else:
            content = terms.get("content")
            matchs = _timestep.match(content) or _sheet_extension.match(content)
            if matchs:
                progress.set_postfix_str(s=f"transfering file {path}")
                processed += send_as(target, path, **terms, **matchs.groupdict())
        progress.update(processed)


def send_as(target, source_path, group=None, number=None, extension=None, **other):
    source_response = client.get_object(Bucket="client-research-data", Key=source_path)
    file_size = source_response["ContentLength"]
    source = source_response["Body"]
    modified = source_response['LastModified']
    done = 0
    transfer = None
    try:
        with tqdm(
            total=file_size, unit="B", unit_scale=True, unit_divisor=1024
        ) as progress:
            progress.set_description(f"uploading {source_path}")
            wrapped_file = CallbackIOWrapper(progress.update, source, "read")
            transfer = api.post_file(target, source_path, content=wrapped_file, modified=modified)
            progress.set_description(f"uploaded {source_path}")
            source.close()
            assert transfer.json()
            progress.close()
            if transfer.status_code in [200, 201]:
                done = 1
    except Exception as error:
        if transfer is not None:
            print(transfer.content)
        raise error
    return done
