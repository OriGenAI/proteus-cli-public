from .defaultConfig import DefaultConfig

class CaseConfig(DefaultConfig):
  """ Configuration generator for the cases """

  def step_1_metadata(self):
    """
      List all cases and its steps to generate the Metadata iterator

      Args: -

      Returns:
          iterator: the list of steps to preprocess
    """
    return (
      {
        "input": [],
        "output": [f'{case["root"]}/ecl_deck.p'],
        "preprocessing": "export_deck",
        "split": case["group"],
        "case": case["number"],
        "additional_info": {
          "group": case["group"],
          "number": case["number"],
        }
      } for case in self.cases
    )
    

  def step_2_runspec(self):
    """
      List all cases and its steps to generate the .DATA iterator

      Args: -

      Returns:
          iterator: the list of steps to preprocess
    """
    return (
      {
        "input": [f'{case["root"]}/SIMULATION_{case["number"]}.DATA'],
        "output": [f'{case["root"]}/runspec.p'],
        "preprocessing": "export_runspec",
        "split": case["group"],
        "case": case["number"],
      } for case in self.cases
    )

  def step_3_grid_props(self):
    """
      List all cases and its steps to generate the .EGRID iterator

      Args: -

      Returns:
          iterator: the list of steps to preprocess
    """
    return (
      {
        "input": [f'{case["root"]}/SIMULATION_{case["number"]}.EGRID'],
        "output": [f'{case["root"]}/grid_props.h5', f'{case["root"]}/SIMULATION_{case["number"]}.EGRID'],
        "preprocessing": "export_egrid_properties",
        "split": case["group"],
        "case": case["number"],
        "keep": True
      } for case in self.cases
    )

  def step_4_init_props(self):
    """
      List all cases and its steps to generate the .INIT iterator

      Args: -

      Returns:
          iterator: the list of steps to preprocess
    """
    return (
      {
        "input": [f'{case["root"]}/SIMULATION_{case["number"]}.INIT', f'{case["root"]}/SIMULATION_{case["number"]}.EGRID'],
        "output": [f'{case["root"]}/init_props.h5', f'{case["root"]}/SIMULATION_{case["number"]}.INIT'],
        "preprocessing": "export_init_properties",
        "split": case["group"],
        "case": case["number"],
        "keep": True
      } for case in self.cases
    )


  def step_5_smry(self):
    """
      List all cases and its steps to generate the Summaries iterator

      Args: -

      Returns:
          iterator: the list of steps to preprocess
    """
    return (
      {
        "input": 
          [f'{case["root"]}/SIMULATION_{case["number"]}.X0000', f'{case["root"]}/SIMULATION_{case["number"]}.SMSPEC', f'{case["root"]}/SIMULATION_{case["number"]}.EGRID'] 
          + [f'{case["root"]}/SIMULATION_{case["number"]}.S{str(step).zfill(4)}' for step in range(case["initialStep"], case["finalStep"])],
        "output": [f'{case["root"]}/smry.p', f'{case["root"]}/SIMULATION_{case["number"]}.SMSPEC'],
        "preprocessing": "export_smry",
        "split": case["group"],
        "case": case["number"]
      } for case in self.cases
    )