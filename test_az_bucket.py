from proteus.app import create_app
from proteus.config import configs
from proteus.models.bucket import Bucket
from proteus.logic.storage import open_bucket_access


def do(*args):
    print("runinng do")
    app = create_app(configs["development"])
    with app.app_context():
        bucket = Bucket(type="az", loc="this-is-a-test")
        access = open_bucket_access(bucket)
        # access.ensure_creation()
        access.store_stream("a-sample-to-clear.txt", b"content a-sample to clear")
        print(access.retrieve_stream("a-sample-to-clear.txt"))
        access.delete("a-sample-to-clear.txt")
