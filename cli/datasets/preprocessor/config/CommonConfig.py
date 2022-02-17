from .defaultConfig import DefaultConfig


class CommonConfig(DefaultConfig):
    """Configuration generator for the common files"""

    def step_1_common(self):
        """
        Generate the common properties iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """
        return {
            "input": [],
            "output": ["common.p"],
            "preprocessing": "noop",
            "additional_info": {
                "get_common_data": self._get_common_data,
            },
        }
