import boto3
import os
import re
from functools import partial
from api import api
from cli.config import config
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper
from pathlib import Path
from datetime import datetime, timezone
from multiprocessing.dummy import Pool
from api.oidc import may_insist_up_to
from azure.storage.blob import ContainerClient, BlobClient
from azure.storage.blob._models import BlobProperties as AzureBlobProperties
from io import BytesIO


PROTEUS_HOST, S3_REGION, WORKERS_COUNT, AZURE_STORAGE_CONNECTION_STRING = (
    config.PROTEUS_HOST,
    config.S3_REGION,
    config.WORKERS_COUNT,
    config.AZURE_STORAGE_CONNECTION_STRING,
)


def s3_client():
    return boto3.client(
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

az_uri_re = re.compile(
    r"^https://(?P<bucket_name>.*\.windows\.net)/"
    r"(?P<container_name>.*)(/(?P<prefix>.*))?$"
)

case_re = re.compile(
    r"(?P<root>.*/(?P<group>validation|training|testing)"
    r"/SIMULATION_(?P<number>\d+))/(?P<content>.*)"
)

_sheet_extension = re.compile(
    r".*(?P<extension>DATA|EGRID|INIT|SMSPEC|GRDECL)$"
)

_timestep = re.compile(r".*(?P<extension>X\d{4}|S\d{4})$")


def list_s3_bucket_contents(bucket_uri):
    match = s3_uri_re.match(bucket_uri)
    assert match is not None, f"{bucket_uri} must be an s3 URI"
    terms = match.groupdict()
    client = s3_client()
    paginator = client.get_paginator("list_objects")
    page_iterator = paginator.paginate(
        Bucket=terms.get("bucket_name"),
        Prefix=terms.get("prefix"),
    )
    for page in page_iterator:
        for item in page["Contents"]:
            yield item, item["Key"]


def list_az_bucket_contents(bucket_uri):
    match = az_uri_re.match(bucket_uri)
    assert match is not None, f"{bucket_uri} must be an s3 URI"
    container_name = match.groupdict()["container_name"]
    client = ContainerClient.from_connection_string(
        conn_str=AZURE_STORAGE_CONNECTION_STRING, container_name=container_name
    )
    for item in client.list_blobs():
        yield item, item["name"]


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


def get_source_items(source_uri):
    match = s3_uri_re.match(source_uri)
    if match is not None:
        return list_s3_bucket_contents(source_uri)
    match = az_uri_re.match(source_uri)
    if match is not None:
        return list_az_bucket_contents(source_uri)
    return list_folder_contents(source_uri)


def list_folder_contents(source_uri):
    for item in Path(source_uri).rglob("*"):
        yield item, str(item)


def load_from(
    case_by_group_and_number, source_uri, progress, workers=WORKERS_COUNT
):
    skipped_count = 0
    processed = 0
    progress.update(processed)
    items_and_paths = get_source_items(source_uri)
    upload_partial = partial(
        parallelized_upload,
        case_by_group_and_number=case_by_group_and_number,
        progress=progress,
        processed=processed,
        skipped_count=skipped_count,
    )
    with Pool(processes=workers) as pool:
        for res in pool.imap(upload_partial, items_and_paths):
            pass


@may_insist_up_to(5, delay_in_secs=5)
def parallelized_upload(
    item_and_path, case_by_group_and_number, progress, processed, skipped_count
):
    item, path = item_and_path
    matchs_as_case = case_re.match(path)
    terms = matchs_as_case.groupdict() if matchs_as_case is not None else {}
    target = find_target(case_by_group_and_number, **terms)
    if target is None:
        skipped_count += 1
        progress.set_postfix_str(
            s=f"{skipped_count} files non related, last one: {path[-15:]}"
        )
    else:
        content = terms.get("content")
        matchs = _timestep.match(content) or _sheet_extension.match(content)
        if matchs:
            if is_pending(matchs, target):
                progress.set_postfix_str(s=f"transfering file {path[-20:]}")
                done, skipped = send_as(
                    target, item, **terms, **matchs.groupdict()
                )
                processed += done
                skipped_count += skipped
            else:
                processed += 1
                progress.set_postfix_str(s=f"already uploaded: {path[-20:]}")
    progress.update(processed)
    progress.refresh()


def is_pending(match, target):
    extension = match.groupdict().get("extension")
    missing_core = target.get("missing_parts").get("core")
    if extension in missing_core:
        return True
    missing_steps = target.get("missing_parts").get("steps")
    if extension in missing_steps:
        return True
    return False


def get_data_from(source):
    if isinstance(source, Path):
        stats = source.stat()
        source_path = str(source)
        modified = datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc)
        file_size = stats.st_size
        return source_path, file_size, modified, source.open("rb")
    elif type(source) == AzureBlobProperties:
        container = source.get("container")
        source_path = source.get("name")
        file_size = source["size"]
        modified = source["last_modified"]
        blob_client = BlobClient.from_connection_string(
            conn_str=AZURE_STORAGE_CONNECTION_STRING,
            container_name=container,
            blob_name=source_path,
        )
        stream = BytesIO()
        streamdownloader = blob_client.download_blob()
        streamdownloader.download_to_stream(stream)
        stream.seek(0)
        return source_path, file_size, modified, stream
    else:  # S3 storage
        client = s3_client()
        source_path = source.get("Key")
        source_response = client.get_object(
            Bucket="client-research-data", Key=source_path
        )
        file_size = source_response["ContentLength"]
        stream = source_response["Body"]
        modified = source_response["LastModified"]
        return source_path, file_size, modified, stream


def send_as(target, source, group=None, number=None, extension=None, **other):
    target_url = target.get("case_url")
    source_path, file_size, modified, stream = get_data_from(source)
    done = 0
    skipped = 0
    transfer = None
    try:
        with tqdm(
            total=file_size, unit="B", unit_scale=True, unit_divisor=1024
        ) as progress:
            progress.set_description(f"uploading {source_path}")
            wrapped_file = CallbackIOWrapper(progress.update, stream, "read")
            transfer = api.post_file(
                target_url,
                source_path,
                content=wrapped_file,
                modified=modified,
            )
            progress.set_description(f"uploaded {source_path[-20:]}")
            stream.close()
            assert transfer.json()
            progress.close()
            if transfer.status_code == 201:
                done = 1
            elif transfer.status_code == 200:
                skipped = 1
            else:
                raise Exception("transfer failed")
    except Exception as error:
        print(f"Failed upload: {source_path}")
        if transfer is not None:
            print(error, transfer.content)
        raise error
    return done, skipped
