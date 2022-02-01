import h5py
import os
import pickle

from ecl.grid import EclGrid
from ecl.eclfile import EclInitFile, EclFile
from ecl.summary import EclSum
from ecl.eclfile.ecl_restart_file import EclRestartFile

from preprocessing.modular.egrid import preprocess as preprocess_egrid
from preprocessing.modular.init import preprocess as preprocess_init
from preprocessing.modular.x import preprocess as preprocess_x
from preprocessing.modular.s import preprocess as preprocess_smry
from preprocessing.deck.runspec import preprocess as preprocess_runspec
from preprocessing.deck.ecl_deck import preprocess as preprocess_deck
from .utils import upload_file, find_ext, get_case_info

DEFAULT_COMMON_PROPERTIES = {
  "max_pressure": -100000,
  "min_pressure":  100000
}

def extract_casename(case_loc):
  return os.path.basename(case_loc)

def extract_base_name(case_loc):
  case_name = os.path.basename(case_loc)
  base_name = case_name.split("_")[:-1]
  base_name = "_".join(base_name)
  return base_name

def write_h5_from_dict(props, location):
  h5f = h5py.File(location, "w")
  for key, val in props.items():
    h5f.create_dataset(key, data=val)
  h5f.close()

def write_pickle_from_dict(props, location):
  with open(location, "wb") as handle:
    pickle.dump(props, handle, protocol=pickle.HIGHEST_PROTOCOL)

def export_common_properties(case_loc, get_common_data):
  src_loc = find_ext(case_loc=case_loc, ext="X????")
  base_name = extract_base_name(src_loc)

  if get_common_data:
    if callable(get_common_data):
      common_properties = get_common_data()
    else:
      common_properties = get_common_data
  else:
    common_properties = DEFAULT_COMMON_PROPERTIES
  common_properties["base_name"] = base_name
    
  common_loc = os.path.join(case_loc, "common.p")
  write_pickle_from_dict(common_properties, common_loc)

  return common_loc

def export_egrid_properties(case_loc, case_dest_loc, *args):
  grid_src_loc = find_ext(case_loc=case_loc, ext="EGRID")
  grid_dest_loc = os.path.join(case_dest_loc, "grid_props.h5")
  
  grid = EclGrid(str(grid_src_loc))
  props = preprocess_egrid(grid)
  write_h5_from_dict(props, grid_dest_loc)

  return None, grid_dest_loc, None

def export_init_properties(case_loc, case_dest_loc, *args):
  grid_src_loc = find_ext(case_loc=case_loc, ext="EGRID")
  init_src_loc = find_ext(case_loc=case_loc, ext="INIT")

  init_dest_loc = os.path.join(case_dest_loc, "init_props.h5")

  grid = EclGrid(str(grid_src_loc))
  init = EclInitFile(grid, str(init_src_loc))
  props = preprocess_init(init)
  write_h5_from_dict(props, init_dest_loc)

  return init_src_loc, init_dest_loc, None

def export_runspec(case_loc, case_dest_loc, input_src, source_url, *args):
  runspec_dest_loc = os.path.join(case_dest_loc, "runspec.p")
  data_src_loc = find_ext(case_loc, "DATA")
  
  def download_func(source_path, destination_path):
    from .utils import download_file
    download_file(source_path, destination_path, source_url)

  data = preprocess_runspec(data_src_loc, download_func)
  write_pickle_from_dict(data, runspec_dest_loc)

  return data_src_loc, runspec_dest_loc, None

def export_smry(case_loc, case_dest_loc, *args):
  grid_src_loc = find_ext(case_loc=case_loc, ext="EGRID")
  x_file = find_ext(case_loc=case_loc, ext="X????")

  smry_dest_loc = os.path.join(case_dest_loc, "smry.p")

  grid = EclGrid(str(grid_src_loc))
  case_name = extract_casename(case_loc)
  smry_src_loc = os.path.join(case_loc, case_name)
  smry = EclSum(smry_src_loc)
  
  rst_file = EclRestartFile(grid, str(x_file))

  props = preprocess_smry(smry, grid, rst_file)
  write_pickle_from_dict(props, smry_dest_loc)
  
  return f"{smry_src_loc}.S????", smry_dest_loc, None

def export_x_file(case_src_loc, _, input, *args):
  x_src_loc = os.path.join(case_src_loc, input.split("/")[-1])
  x_dest_loc = os.path.join(case_src_loc, input.split(".")[-1] + ".h5")
  
  rst = EclFile(x_src_loc)
  props = preprocess_x(rst)
  write_h5_from_dict(props, x_dest_loc)

  return x_src_loc, x_dest_loc, {
      "max_pressure": props["pressure"].max(),
      "min_pressure": props["pressure"].min(),
  }

def export_deck(case_loc, case_dest_loc, _, source_url, cases_url, group, number):
  ecl_deck_loc = os.path.join(case_dest_loc, "ecl_deck.p")

  case = get_case_info(f"{cases_url}/{group}/{number}")
  min = int(case.get("initialStep")) - 1
  max = case.get("finalStep")
  props = {
    "size": max - min,
    "min": min,
    "max": max
  }
  write_pickle_from_dict(props, ecl_deck_loc)

  return None, ecl_deck_loc, None

def postprocess_common_file(path, output, cases_url, get_common_data, set_common_data):
  common_data = get_common_data()

  max_p = common_data["max_pressure"]
  min_p = common_data["min_pressure"]
  max_pc = output["max_pressure"]
  min_pc = output["min_pressure"]

  if max_pc > max_p or min_pc < min_p:
    max_p = max_pc if max_pc > max_p else max_p
    min_p = min_pc if min_pc < min_p else min_p

    common_properties = {
      "max_pressure": max_p,
      "min_pressure": min_p,
    }

    location = export_common_properties(path, common_properties)
    upload_file("cases/common.p", location, cases_url)
    set_common_data(common_properties)

def noop(*args):
  return None, None, None