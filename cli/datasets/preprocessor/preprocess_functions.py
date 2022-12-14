import json
import os
import pickle

import cwrap
import h5py
import numpy as np
from ecl.eclfile import EclInitFile, EclFile
from ecl.grid import EclGrid
from ecl.summary import EclSum
from ecl.well import WellInfo
from preprocessing.deck.runspec import preprocess as preprocess_runspec
from preprocessing.deck.section import find_section
from preprocessing.modular.dat import preprocess as preprocess_dat
from preprocessing.modular.data import WellSpecsProcessor
from preprocessing.modular.egrid import preprocess as preprocess_egrid
from preprocessing.modular.grdecl import preprocess as preprocess_grdecl
from preprocessing.modular.init import preprocess as preprocess_init
from preprocessing.modular.s import WellSummaryProcessor
from preprocessing.modular.x import preprocess as preprocess_x

from .config.CaseConfig import SMSPEC_WELL_KEYWORDS, SMSPEC_FIELD_KEYWORDS
from .utils import upload_file, find_ext, find_file, get_case_info
from ... import proteus

DEFAULT_COMMON_PROPERTIES = {"max_pressure": -100000, "min_pressure": 100000}


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
        upload_file("common.p", location, cases_url)
        set_common_data(common_properties)


def noop(*args):
    return None, None, None


""" Common preprocessing """


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


def export_deck(case_loc, case_dest_loc, _, source_url, cases_url, group, number):
    root_folder = case_dest_loc.split("/cases/")[0]
    ecl_deck_loc = os.path.join(root_folder, "ecl_deck.p")

    case = get_case_info(f"{cases_url}/{group}/{number}")
    min = int(case.get("initialStep")) - 1
    max = case.get("finalStep")
    props = {"size": max - min, "min": min, "max": max}
    write_pickle_from_dict(props, ecl_deck_loc)

    return None, ecl_deck_loc, None


def export_runspec(
    case_loc,
    case_dest_loc,
    input_src,
    source_url,
    cases_url,
    set_endpoint,
    *args,
):
    root_folder = case_dest_loc.split("/cases/")[0]
    runspec_dest_loc = os.path.join(root_folder, "runspec.p")
    data_src_loc = find_ext(case_loc, "DATA")

    def download_func(source_path, destination_path):
        from .utils import download_file

        download_file(source_path, destination_path, source_url)

    data = preprocess_runspec(data_src_loc, download_func)
    multout = data.get("multout")
    del data["multout"]
    if not multout:
        proteus.logger.warning("MULTOUT not found in RUNSPEC section. This can lead to issues.")

    write_pickle_from_dict(data, runspec_dest_loc)

    set_endpoint(data.get("endscale"))

    return data_src_loc, runspec_dest_loc, None


""" Cases preprocessing """


def export_egrid_properties(case_loc, case_dest_loc, *args):
    grid_src_loc = find_ext(case_loc=case_loc, ext="EGRID")
    grid_dest_loc = os.path.join(case_dest_loc, "grid_props.h5")

    grid = EclGrid(str(grid_src_loc))
    props = preprocess_egrid(grid)
    write_h5_from_dict(props, grid_dest_loc)

    return None, grid_dest_loc, None


def export_init_properties(
    case_loc,
    case_dest_loc,
    input_src,
    source_url,
    cases_url,
    get_endpoint,
    *args,
):
    grid_src_loc = find_ext(case_loc=case_loc, ext="EGRID")
    init_src_loc = find_ext(case_loc=case_loc, ext="INIT")

    grid = EclGrid(str(grid_src_loc))
    init = EclInitFile(grid, str(init_src_loc))
    endpoint_scaling = get_endpoint()
    props = preprocess_init(init, endpoint_scaling)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, "init_keywords.json")) as file:
        init_keywords = json.load(file)

    for init_keyword in init_keywords:
        keywords = {k: props.get(k, []) for k in init_keyword.get("keywords")}
        file_dest_loc = os.path.join(case_dest_loc, init_keyword.get("filename"))
        write_h5_from_dict(keywords, file_dest_loc)

    return init_src_loc, case_dest_loc, None


def export_well_init_properties(
    case_loc,
    case_dest_loc,
    input_src,
    source_url,
    cases_url,
    get_endpoint,
    *args,
):
    grid_src_loc = find_ext(case_loc=case_loc, ext="EGRID")
    init_src_loc = find_ext(case_loc=case_loc, ext="INIT")

    grid = EclGrid(str(grid_src_loc))
    init = EclInitFile(grid, str(init_src_loc))
    endpoint_scaling = get_endpoint()
    props = preprocess_init(init, endpoint_scaling)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, "well_init_keywords.json")) as file:
        init_keywords = json.load(file)

    for init_keyword in init_keywords:
        keywords = {k: props.get(k, []) for k in init_keyword.get("keywords")}
        file_dest_loc = os.path.join(case_dest_loc, init_keyword.get("filename"))
        write_h5_from_dict(keywords, file_dest_loc)

    return init_src_loc, case_dest_loc, None


def export_litho(
    case_loc,
    case_dest_loc,
    input_src,
    source_url,
    cases_url,
    get_mapping,
    *args,
):
    grdecl_src_loc = find_ext(case_loc=case_loc, ext="GRDECL")
    mapping = filter(lambda x: x["name"] == "LITHO_INPUT", get_mapping())

    with cwrap.open(str(grdecl_src_loc), "r") as f:
        props = preprocess_grdecl(f, mapping)

    _write_keywords_to_h5(props, case_dest_loc)
    return grdecl_src_loc, case_dest_loc, None


def export_actnum(
    case_loc,
    case_dest_loc,
    input_src,
    source_url,
    cases_url,
    get_mapping,
    *args,
):
    grdecl_src_loc = find_ext(case_loc=case_loc, ext="GRDECL")
    mapping = filter(lambda x: x["name"] == "ACTNUM", get_mapping())

    with cwrap.open(str(grdecl_src_loc), "r") as f:
        props = preprocess_grdecl(f, mapping)

    _write_keywords_to_h5(props, case_dest_loc)
    return grdecl_src_loc, case_dest_loc, None


def _extract_dat_mappings(mapping):
    return [*filter(lambda f: f["name"].lower() not in ["litho", "actnum"], mapping)]


def export_dat_properties(
    case_loc,
    case_dest_loc,
    input_src,
    source_url,
    cases_url,
    get_mapping,
    *args,
):
    dat_src_locs = [str(find_file(case_loc, src.split("/")[-1])) for src in input_src]

    mapping = _extract_dat_mappings(get_mapping())

    dat_files = {}
    for keyword in mapping:
        file = next(
            filter(lambda f: keyword["source"].lower() in f, dat_src_locs),
            None,
        )
        if file:
            dat_files[keyword["source"].lower()] = file

    props = preprocess_dat(dat_files, mapping)

    _write_keywords_to_h5(props, case_dest_loc)

    return dat_src_locs, case_dest_loc, None


def _write_keywords_to_h5(props, dest_loc):
    for k, v in props.items():
        file_dest_loc = os.path.join(dest_loc, f"{k}.h5")
        write_h5_from_dict({k: v}, file_dest_loc)


def export_wellspec(case_loc, case_dest_loc, _, source_url, *args):
    runspec_dest_loc = os.path.join(case_dest_loc, "well_spec.p")
    data_src_loc = find_ext(case_loc, "DATA")

    def download_func(source_path, destination_path):
        from .utils import download_file

        download_file(source_path, destination_path, source_url)

    # Read and download data includes
    find_section(data_src_loc, "RUNSPEC", download_func)

    preprocessor = WellSpecsProcessor(data_src_loc)
    data = preprocessor.process()

    write_pickle_from_dict(data, runspec_dest_loc)

    return data_src_loc, runspec_dest_loc, None


def export_smry(case_loc, case_dest_loc, _, source_url, *args):
    preprocessed_smry_dest_loc = os.path.join(case_dest_loc, "preprocessed_smry.h5")
    raw_smry_dest_loc = os.path.join(case_dest_loc, "raw_smry.h5")
    data_src_loc = find_ext(case_loc, "DATA")

    def download_func(source_path, destination_path):
        from .utils import download_file

        download_file(source_path, destination_path, source_url)

    # Read and download data includes
    find_section(data_src_loc, "RUNSPEC", download_func)

    case_name = extract_casename(case_loc)
    smry_src_loc = os.path.join(case_loc, case_name)
    preprocessor = WellSummaryProcessor(smry_src_loc)
    preprocessed_smry, raw_smry = preprocessor.process()

    preprocessed_smry.to_hdf(preprocessed_smry_dest_loc, key="df", format="fixed", mode="w")
    raw_smry.to_hdf(raw_smry_dest_loc, key="df", format="fixed", mode="w")

    return f"{smry_src_loc}.S????", preprocessed_smry_dest_loc, None


def export_smspec(case_loc, case_dest_loc, input_src, source_url, *args):
    grid_src_loc = find_ext(case_loc=case_loc, ext="EGRID")
    last_x = sorted([*filter(lambda x: ".X" in x, input_src)])[-1]
    restart_path = find_ext(case_loc=case_loc, ext=last_x.split(".")[-1])
    smspec_path = find_ext(case_loc=case_loc, ext="SMSPEC")
    grid = EclGrid(str(grid_src_loc))
    winfo = WellInfo(grid, str(restart_path))
    smry = EclSum(str(smspec_path))

    wnames = np.array(list(smry.wells()))

    well_types = []
    for w in wnames:
        wtimeline = winfo[w]
        wstate = wtimeline[0]
        well_types.append(str(wstate.wellType()))

    for key in SMSPEC_WELL_KEYWORDS:
        with h5py.File(os.path.join(case_dest_loc, f"{key}.h5"), "w") as h5f:
            for i, w in enumerate(wnames):
                if "INJECTOR" not in well_types[i]:
                    try:
                        data = smry.numpy_vector(f"{key}:{w}", report_only=True)
                        h5f.create_dataset(w, data=data)
                    except KeyError:
                        # Some keywords may be missing, the correct behaviour is to not create a dataset
                        pass

    for key in SMSPEC_FIELD_KEYWORDS:
        with h5py.File(os.path.join(case_dest_loc, f"{key}.h5"), "w") as h5f:
            data = smry.numpy_vector(key, report_only=True)
            h5f.create_dataset(key, data=data)

    return smspec_path, None, None


""" Steps preprocessing """


def export_x_file(case_src_loc, _, input, *args):
    x_src_loc = os.path.join(case_src_loc, input.split("/")[-1])
    x_pressure_dest_loc = os.path.join(case_src_loc, input.split(".")[-1] + "_pressure.h5")
    x_swat_dest_loc = os.path.join(case_src_loc, input.split(".")[-1] + "_swat.h5")

    rst = EclFile(x_src_loc)
    props = preprocess_x(rst)
    write_h5_from_dict({"pressure": props.get("pressure")}, x_pressure_dest_loc)
    write_h5_from_dict({"swat": props.get("swat")}, x_swat_dest_loc)

    return (
        x_src_loc,
        x_pressure_dest_loc,
        {
            "max_pressure": props["pressure"].max(),
            "min_pressure": props["pressure"].min(),
        },
    )
