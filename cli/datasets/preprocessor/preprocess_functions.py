import json
import os
import pickle
from threading import RLock
from typing import Callable, Sequence

import cwrap
import h5py
import numpy as np
from ecl.eclfile import EclInitFile, EclFile
from ecl.grid import EclGrid
from ecl.summary import EclSum

from cli.datasets.preprocessor.config.well_model import SMSPEC_WELL_KEYWORDS, SMSPEC_FIELD_KEYWORDS
from cli.utils.files import upload_file, find_ext, PathMeta
from preprocessing.deck import ecl_deck
from preprocessing.deck.runspec import preprocess as preprocess_runspec
from preprocessing.deck.section import find_section, get_includes
from preprocessing.modular import dat
from preprocessing.modular.data import WellSpecsProcessor
from preprocessing.modular.egrid import preprocess as preprocess_egrid
from preprocessing.modular.grdecl import preprocess as preprocess_grdecl
from preprocessing.modular.init import preprocess as preprocess_init
from preprocessing.modular.s import WellSummaryProcessor
from preprocessing.modular.x import preprocess as preprocess_x
from ..sources.local import LocalSource
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


def export_deck(case_loc, case_dest_loc, _, source, cases_url, group, number):
    root_folder = case_dest_loc.split("/cases/")[0]
    ecl_deck_loc = os.path.join(root_folder, "ecl_deck.p")

    case = proteus.api.get(f"{cases_url}/{group}/{number}").json().get("case")

    min_step = int(case.get("initialStep")) - 1
    max_step = case.get("finalStep")
    props = {"size": max_step - min_step, "min": min_step, "max": max_step}
    write_pickle_from_dict(props, ecl_deck_loc)

    return None, ecl_deck_loc, None


def export_runspec(
    download_func: Callable,
    output_source: LocalSource,
    data: PathMeta,
    init: PathMeta = None,
    egrid: PathMeta = None,
    smspec: PathMeta = None,
    allow_missing_files: Sequence[str] = tuple(),
    **_,
):
    runspec_dest_loc = os.path.join(output_source.uri, "runspec.p")

    data = preprocess_runspec(
        data.full_path,
        egrid_file_loc=egrid and egrid.full_path,
        smspec_file_loc=smspec and smspec.full_path,
        init_file_loc=init and init.full_path,
        download_func=download_func,
        allow_missing_files=allow_missing_files,
    )

    multout = data.get("multout")
    del data["multout"]
    if not multout:
        proteus.logger.warning("MULTOUT not found in RUNSPEC section. This can lead to issues.")

    write_pickle_from_dict(data, runspec_dest_loc)


""" Cases preprocessing """


def export_egrid_properties(
    download_func: Callable, output_source: LocalSource, data: PathMeta = None, egrid: PathMeta = None, **_
):
    if not data and not egrid:
        raise RuntimeError("Either data or egrid files are needed")

    if data:
        _export_egrid_properties_from_data(data.full_path, download_func=download_func, base_dir=output_source.uri)
    else:
        _export_egrid_properties_from_egrid(egrid.full_path, base_dir=output_source.uri)


def _export_egrid_properties_from_data(
    input_src,
    download_func,
    base_dir=None,
    allow_missing_files=tuple(),
):

    get_includes(input_src, download_func, allow_missing_files=allow_missing_files)

    grid = ecl_deck.extract_actnum(input_src.full_path)
    grid_dest_loc = os.path.join(base_dir, "grid.h5")
    props = preprocess_egrid(grid)
    write_h5_from_dict(props, grid_dest_loc)


def _export_egrid_properties_from_egrid(
    input_src,
    base_dir=None,
    allow_missing_files=tuple(),
):

    grid_dest_loc = os.path.join(base_dir, "grid.h5")

    grid = EclGrid(str(input_src))
    props = preprocess_egrid(grid)
    write_h5_from_dict(props, grid_dest_loc)


def export_init_properties(
    case_loc,
    case_dest_loc,
    input_src,
    source,
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

    dir_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dir_path, "init_keywords.json")) as file:
        init_keywords = json.load(file)

    for init_keyword in init_keywords:
        keywords = {k: props.get(k, []) for k in init_keyword.get("keywords")}
        file_dest_loc = os.path.join(case_dest_loc, init_keyword.get("filename"))
        write_h5_from_dict(keywords, file_dest_loc)


def export_well_init_properties(output_source: LocalSource, grid, init, **_):

    grid = EclGrid(str(grid.full_path))
    init = EclInitFile(grid, str(init.full_path))
    props = preprocess_init(init, False)

    dir_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dir_path, "well_init_keywords.json")) as file:
        init_keywords = json.load(file)

    for init_keyword in init_keywords:
        keywords = {k: props.get(k, []) for k in init_keyword.get("keywords")}
        file_dest_loc = os.path.join(output_source.uri, init_keyword.get("filename"))
        write_h5_from_dict(keywords, file_dest_loc)


def export_litho(
    case_loc,
    case_dest_loc,
    input_src,
    source,
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
    source,
    cases_url,
    get_mapping,
    *args,
):
    mapping = [*filter(lambda x: x["name"] == "ACTNUM", get_mapping())]
    grdecl_src_loc = find_ext(case_loc=case_loc, ext="GRDECL", required=False, one=True)

    if mapping and grdecl_src_loc:
        with cwrap.open(str(grdecl_src_loc), "r") as f:
            props = preprocess_grdecl(f, mapping)

        _write_keywords_to_h5(props, case_dest_loc)

    return grdecl_src_loc, case_dest_loc, None


EXPORT_DAT_PROPERTIES_LOCK = RLock()


def export_dat_properties(output_source: LocalSource, input_files: Sequence[PathMeta], **_):
    dat_src_locs = {f"{f.full_path}": f"{f.download_name}" for f in input_files}

    # Loading dat files can be heavy and consume a lot of memory. Ensure 2 steps are not loading
    # dat data in memory at the same time
    with EXPORT_DAT_PROPERTIES_LOCK:
        case_dest_loc = []
        # Dat files can be very big. Write them individually to reduce memory usage
        for source, col_name, df in dat.preprocess(dat_src_locs):
            case_dest_loc.append(_write_keywords_to_h5({col_name: df.to_numpy()}, output_source.uri)[0])

    return dat_src_locs, case_dest_loc, None


def _write_keywords_to_h5(props, dest_loc):
    locations = []
    for k, v in props.items():
        file_dest_loc = os.path.join(dest_loc, f"{k}.h5")
        write_h5_from_dict({k: v}, file_dest_loc)
        locations.append(file_dest_loc)

    return locations


def export_wellspec(data: PathMeta, download_func, output_source: LocalSource, allow_missing_files=tuple(), **_):
    # Read and download data includes
    find_section(data.full_path, "RUNSPEC", download_func, allow_missing_files=allow_missing_files)

    wellspec_dest_loc = os.path.join(output_source.uri, "well_spec.p")

    preprocessor = WellSpecsProcessor(data.full_path)
    wellspec_data = preprocessor.process()

    write_pickle_from_dict(wellspec_data, wellspec_dest_loc)

    return data.full_path, wellspec_dest_loc, None


def export_smry(case_loc, case_dest_loc, _, source, *args, allow_missing_files=tuple(), base_dir=None):
    preprocessed_smry_dest_loc = os.path.join(case_dest_loc, "preprocessed_smry.h5")
    raw_smry_dest_loc = os.path.join(case_dest_loc, "raw_smry.h5")
    data_src_loc = find_ext(case_loc, "DATA")

    def download_func(source_path, destination_path):
        from cli.utils.files import download_file

        download_file(source_path, destination_path, source)

    # Read and download data includes
    find_section(data_src_loc, "RUNSPEC", download_func, allow_missing_files=allow_missing_files, base_dir=base_dir)

    case_name = extract_casename(case_loc)
    smry_src_loc = os.path.join(case_loc, case_name)
    preprocessor = WellSummaryProcessor(smry_src_loc)
    preprocessed_smry, raw_smry = preprocessor.process()

    preprocessed_smry.to_hdf(preprocessed_smry_dest_loc, key="df", format="fixed", mode="w")
    raw_smry.to_hdf(raw_smry_dest_loc, key="df", format="fixed", mode="w")

    return f"{smry_src_loc}.S????", preprocessed_smry_dest_loc, None


def export_smspec(output_source: LocalSource, smspec, **_):

    smry = EclSum(str(smspec.full_path))

    wnames = np.array(list(smry.wells()))

    for key in SMSPEC_WELL_KEYWORDS:
        with h5py.File(os.path.join(output_source.uri, f"{key}.h5"), "w") as h5f:
            for i, w in enumerate(wnames):
                try:
                    data = smry.numpy_vector(f"{key}:{w}", report_only=True)
                    h5f.create_dataset(w, data=data)
                except KeyError:
                    # Some keywords may be missing, the correct behaviour is to not create a dataset
                    pass

    for key in SMSPEC_FIELD_KEYWORDS:
        with h5py.File(os.path.join(output_source.uri, f"{key}.h5"), "w") as h5f:
            try:
                data = smry.numpy_vector(key, report_only=True)
                h5f.create_dataset(key, data=data)
            except KeyError:
                pass

    return smspec, None, None


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
