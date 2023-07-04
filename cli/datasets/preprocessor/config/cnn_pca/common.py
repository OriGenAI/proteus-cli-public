from cli.datasets.preprocessor.config import CommonStepConfig
from cli.datasets.preprocessor.config.cnn_pca import BaseCnnPcaCaseConfig
from cli.datasets.preprocessor.preprocess_functions import export_runspec, export_wellspec, \
    export_dat_properties, export_actnum
from cli.datasets.preprocessor.utils import RequiredFilePath


class CnnPcaCommonConfig(BaseCnnPcaCaseConfig):
    """Configuration generator for the common files"""

    # def step_1_runspec(self):
    #     """
    #     List all cases and its steps to generate the .DATA iterator
    #
    #     Args: -
    #
    #     Returns:
    #         iterator: the list of steps to preprocess
    #     """
    #     first_case = self.cases[0]
    #     return iter(
    #         [
    #             {
    #                 "input": [RequiredFilePath(f'{str(first_case["root"]).rstrip("/")}/*.DATA', download_name="data")],
    #                 "output": ["runspec.p"],
    #                 "preprocessing": "export_runspec",
    #                 "case": first_case["number"],
    #                 "keep": True,
    #                 "additional_info": {"set_endpoint": self._set_endpoint},
    #             }
    #         ]
    #     )

    def step_1_runspec(self):
        first_case = self.cases[0]
        return (
            CommonStepConfig(
                input=[RequiredFilePath(f'{str(first_case["root"]).rstrip("/")}/*.DATA', download_name="data")],
                output=[RequiredFilePath('runspec.p')],
                preprocessing_fn=export_runspec,
                keep=True,
                enabled=True
            ),
        )

    # def step_2_wellspec(self):
    #     """
    #     List all cases and its steps to generate the Summaries iterator
    #
    #     Args: -
    #
    #     Returns:
    #         iterator: the list of steps to preprocess
    #     """
    #     first_case = self.cases[0]
    #     return iter(
    #         [
    #             {
    #                 "input": [RequiredFilePath(f'{str(first_case["root"]).rstrip("/")}/*.DATA', download_name="data")],
    #                 "output": ["well_spec.p"],
    #                 "preprocessing": "export_wellspec",
    #                 "keep": True,
    #                 "case": first_case["number"],
    #             }
    #         ]
    #     )
    def step_2_wellspec(self):
        first_case = self.cases[0]
        return (
            CommonStepConfig(
                input=[RequiredFilePath(f'{str(first_case["root"]).rstrip("/")}/*.DATA', download_name="data")],
                output=[RequiredFilePath("well_spec.p")],
                preprocessing_fn=export_wellspec,
                keep=True,
                enabled=True
            ),
        )


    # def step_3_dat_files(self):
    #     """
    #     Generate .dat iterator
    #
    #     Args: -
    #
    #     Returns:
    #         iterator: the list of steps to preprocess
    #     """
    #
    #     mapping = [*filter(lambda x: x["name"] not in ["LITHO_INPUT", "ACTNUM"], self._get_mapping())]
    #     return iter(
    #         [
    #             {
    #                 "input": [RequiredFilePath(f'{f.get("source") or f.get("name")}.dat') for f in mapping],
    #                 "output": [f'{f["name"]}.h5' for f in mapping],
    #                 "preprocessing": "export_dat_properties",
    #                 "keep": True,
    #                 "additional_info": {"get_mapping": lambda: mapping},
    #             }
    #         ]
    #     )

    def step_3_dat_files(self):
        return (
            CommonStepConfig(
                input=tuple(RequiredFilePath(f'{m.source or m.name}.dat', download_name=m.name) for m in self.mapping),
                output=tuple(RequiredFilePath(f'{m.name}.h5') for m in self.mapping),
                preprocessing_fn=export_dat_properties,
                keep=False
            ),
        )

    # def step_4_actnum_prop(self):
    #     """
    #     List all cases and its steps to generate the .DATA iterator
    #
    #     Args: -
    #
    #     Returns:
    #         iterator: the list of steps to preprocess
    #     """
    #     first_case = self.cases[0]
    #     mapping = [*filter(lambda x: x["name"] == "ACTNUM", self._get_mapping())]
    #
    #     if len(mapping) == 0:
    #         return iter([])
    #
    #     return iter(
    #         [
    #             {
    #                 "input": [
    #                     RequiredFilePath(
    #                         f'{str(first_case["root"]).rstrip("/")}/' f"*ACTNUM.GRDECL", download_name="actnum"
    #                     )
    #                 ],
    #                 "output": ["actnum.h5"],
    #                 "preprocessing": "export_actnum",
    #                 "case": first_case["number"],
    #                 "keep": True,
    #                 "additional_info": {"get_mapping": self._get_mapping},
    #             }
    #         ]
    #     )

    def step_4_actnum_prop(self):
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
                input=(RequiredFilePath(
                                f'{str(first_case["root"]).rstrip("/")}/' f"*ACTNUM.GRDECL", download_name="actnum"
                            ),),
                output=(RequiredFilePath('actnum.h5'),),
                preprocessing_fn=export_actnum
            ),
        )
