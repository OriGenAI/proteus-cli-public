from cli.datasets.preprocessor.config import CommonStepConfig
from cli.datasets.preprocessor.config.cnn_pca import BaseCnnPcaCaseConfig
from cli.datasets.preprocessor.preprocess_functions import (
    export_runspec,
    export_wellspec,
    export_dat_properties,
    export_actnum,
)
from cli.utils.files import RequiredFilePath


class CnnPcaCommonConfig(BaseCnnPcaCaseConfig):
    """Configuration generator for the common files"""

    def step_1_runspec(self):
        first_case = self.cases[0]
        return (
            CommonStepConfig(
                input=[RequiredFilePath(f'{str(first_case["root"]).rstrip("/")}/*.DATA', download_name="data")],
                output=[RequiredFilePath("runspec.p")],
                preprocessing_fn=export_runspec,
                keep=True,
                enabled=True,
            ),
        )

    def step_2_wellspec(self):
        first_case = self.cases[0]
        return (
            CommonStepConfig(
                input=[RequiredFilePath(f'{str(first_case["root"]).rstrip("/")}/*.DATA', download_name="data")],
                output=[RequiredFilePath("well_spec.p")],
                preprocessing_fn=export_wellspec,
                keep=True,
                enabled=True,
            ),
        )

    def step_3_actnum_prop(self):
        """
        List all cases and its steps to generate the .DATA iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """
        if not self.actnum_mapping:
            return tuple()

        first_case = self.cases[0]

        return (
            CommonStepConfig(
                input=(
                    RequiredFilePath(
                        f'{str(first_case["root"]).rstrip("/")}/' f"*ACTNUM.GRDECL", download_name="actnum"
                    ),
                ),
                output=(RequiredFilePath("actnum.h5"),),
                preprocessing_fn=export_actnum,
                enabled=True,
            ),
        )

    def step_4_dat_files(self):
        return tuple(
            CommonStepConfig(
                input=(RequiredFilePath(f"{m.source or m.name}.dat", download_name=m.name),),
                output=(RequiredFilePath(f"{m.name}.h5"),),
                preprocessing_fn=export_dat_properties,
                keep=False,
                name=m.name,
                enabled=True,
            )
            for m in self.mapping
        )
