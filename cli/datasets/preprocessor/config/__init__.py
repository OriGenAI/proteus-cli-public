from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Callable, Sequence

from cli import proteus
from cli.utils.files import PathMeta

PREPROCESSING_PHASE_COMMON = "common"
PREPROCESSING_PHASE_CASE = "case"
PREPROCESSING_PHASE_STEP = "step"

PREPROCESSING_PHASES = [PREPROCESSING_PHASE_COMMON, PREPROCESSING_PHASE_CASE, PREPROCESSING_PHASE_STEP]

CASE_TYPE_TRAINING = "training"
CASE_TYPE_TESTING = "testing"
CASE_TYPE_VALIDATION = "validation"

CASE_TYPES = [CASE_TYPE_TRAINING, CASE_TYPE_TESTING, CASE_TYPE_VALIDATION]


# Config object wrapping all properties
class BaseConfig:
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

        for prop in self.properties():
            func = getattr(self, prop)
            if not callable(func):
                continue

            base_step_name = (
                f'{"Config".join(self.__class__.__name__.split("Config")[:-1]) or "Config"}.{func.__name__}'
            )

            try:
                configs = func()

                digits_for_cases = (
                    len(str(max(max(x.case or 0 for x in configs), len(configs)))) if len(configs) > 0 else 0
                )

                for step_config in configs:
                    assert isinstance(step_config, (CommonStepConfig, CaseStepConfig, StepStepConfig))

                    preprocessing_phase = self.__module__.split(".")[-1]

                    if preprocessing_phase not in PREPROCESSING_PHASES or not self.__class__.__module__.startswith(
                        "cli.datasets.preprocessor.config."
                    ):
                        raise RuntimeError(
                            f"{self.__class__.__module__}.{self.__class__.__qualname__} is not placed "
                            f"in the proper path. Please follow the following path to organize the "
                            f"config: cli.datasets.preprocessor.config.<workflow_name>."
                            f"<preprocessing_phase>.MyConfigClass"
                        )

                    dict_config = deepcopy(step_config.__dict__)
                    dict_config.pop("name", None)

                    root = dict_config.pop("root")
                    if not root:
                        root = (
                            ""
                            if isinstance(step_config, CommonStepConfig)
                            else f"{step_config.split}/SIMULATION_{step_config.case}"
                        )

                    step_name = base_step_name
                    if step_config.name:
                        step_name = f"{step_name}.{step_config.name}"
                    if step_config.case:
                        step_name = f"{str(step_config.case).zfill(digits_for_cases)}." + step_name
                    if step_config.split:
                        step_name = f"{step_config.split[:2]}." + step_name

                    yield StepConfigWithMetadata(
                        step_name=step_name,
                        type=step_config.__class__,
                        preprocessing_phase=preprocessing_phase,
                        root=root,
                        **dict_config,
                    )
            except BaseException as e:
                raise RuntimeError(f"Error reading step {base_step_name}") from e

    @classmethod
    def number_of_steps(cls):
        properties = cls.properties(cls)
        method_list = [step for step in properties if callable(getattr(cls, step))]

        return len(method_list)


@dataclass(frozen=True)
class CommonStepConfig:
    input: Sequence[PathMeta]
    output: Sequence[PathMeta]
    preprocessing_fn: Optional[Callable]
    split: Optional[str] = None
    keep: Optional[bool] = False
    case: Optional[str] = None
    root: Optional[str] = None
    enabled: Optional[bool] = True
    name: Optional[str] = None


@dataclass(frozen=True)
class CaseStepConfig:

    input: Sequence[PathMeta]
    output: Sequence[PathMeta]
    split: str
    case: str
    root: str

    preprocessing_fn: Optional[Callable]
    keep: Optional[bool] = False
    enabled: Optional[bool] = True
    name: Optional[str] = None


@dataclass(frozen=True)
class StepStepConfig(CaseStepConfig):
    pass


@dataclass(frozen=True)
class StepConfigWithMetadata:
    input: Sequence[PathMeta]
    output: Sequence[PathMeta]

    step_name: str
    type: type = None

    preprocessing_fn: Optional[Callable] = None

    split: Optional[str] = None
    keep: Optional[bool] = False
    case: Optional[str] = None
    root: Optional[str] = None

    preprocessing_phase: Optional[str] = None
    step_name: Optional[str] = None
    enabled: Optional[bool] = True
