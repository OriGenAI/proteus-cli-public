from dataclasses import dataclass

from cli.api import proteus
from cli.datasets.preprocessor.config import BaseConfig


@dataclass(frozen=True)
class CnnPcaMapping:
    name: str
    source: str


class BaseCnnPcaCaseConfig(BaseConfig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        case_url = self.cases[0].get("case_url")
        dataset_url = case_url.split("/cases")[0]
        dataset = proteus.api.get(dataset_url)

        config = dataset.json().get("dataset").get("sampling").get("config")
        assert isinstance(config.get("cnn_pca_design").get("keywords"), (list,))

        raw_mapping = [
            CnnPcaMapping(**x.setdefault("source", x["name"]) and x)
            for x in config.get("cnn_pca_design").get("keywords")
        ]
        self.litho_input = next((x for x in raw_mapping if x.name == "LITHO_INPUT"), None)
        self.mapping = [x for x in raw_mapping if x.name not in ("LITHO_INPUT", "ACTNUM")]
        self.actnum_mapping = next((x for x in raw_mapping if x.name == "ACTNUM"), None)
