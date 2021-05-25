from .common import CommonLifecycle


class Lifecycle(CommonLifecycle):
    """This is the proper runner lifecycle"""

    __steps__ = ["declare_processing", "load_entity", "celebrate"]

    def celebrate(self):
        print("yeeeah")
