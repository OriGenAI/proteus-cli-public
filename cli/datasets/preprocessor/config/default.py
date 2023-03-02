from functools import lru_cache
from itertools import chain

from cli.runtime import proteus


class DefaultConfig(object):
    """
    Define the default config object with common methods
    Args:
        cases (list): the list with all the cases information
    """

    def __init__(self, cases, common_data=None):
        self.cases = cases
        self.endpoint = False
        self.common_data = common_data or {
            "max_pressure": -100000,
            "min_pressure": 100000,
        }

    """ Getters and setters """

    def _get_endpoint(self):
        return self.endpoint

    @lru_cache
    def _get_mapping(self):
        config = self._get_config()
        assert isinstance(config.get("cnn_pca_design").get("keywords"), (list,))
        return [x.setdefault("source", x["name"]) and x for x in config.get("cnn_pca_design").get("keywords")]

    @lru_cache
    def _get_config(self):
        case_url = self.cases[0].get("case_url")
        dataset_url = case_url.split("/cases")[0]
        dataset = proteus.api.get(dataset_url)
        return dataset.json().get("dataset").get("sampling").get("config")

    def _set_endpoint(self, endpoint):
        self.endpoint = endpoint

    def _get_common_data(self):
        return self.common_data

    def _set_common_data(self, common_data):
        self.common_data = common_data

    """ Methods """

    def properties(self):
        """
        List all object properties other than the common ones

        Args: -

        Returns:
            list: the list of properties
        """
        return list(
            filter(
                lambda prop: not prop.startswith("_")
                and not prop == "properties"
                and not prop == "return_iterator"
                and not prop == "number_of_steps",
                dir(self),
            )
        )

    def return_iterator(self):
        """
        This mehtod loops through all the properties and it generates
        an iterator calling all the functions. We will use it to recursively
        call all the config methods.

        Args: -

        Returns:
            iterator: iterator with the result of the functions
        """
        properties = self.properties()

        result = iter([])
        for prop in properties:
            func = getattr(self, prop)
            if not callable(func):
                continue

            result = chain(result, func())

        return result

    @classmethod
    def number_of_steps(cls):
        properties = cls.properties(cls)
        method_list = [step for step in properties if callable(getattr(cls, step))]

        return len(method_list)
