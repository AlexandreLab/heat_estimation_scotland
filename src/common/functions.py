import itertools
from functools import partial
from pathlib import Path
from typing import Callable

import pandas as pd

from src.common import enums, schema

PATH_EPC_BY_LA = Path(
    r"C:\Users\sceac10\OneDrive - Cardiff University\04 - Projects\22 - Heat demand scotland\data\EPC_by_LAs"
)
PATH_GEO_LOOKUP = Path(
    r"C:\Users\sceac10\OneDrive - Cardiff University\04 - Projects\22 - Heat demand scotland\data\geo_lookup_tables\PCD_OA_LSOA_MSOA_LAD_AUG19_UK_LU\PCD_OA_LSOA_MSOA_LAD_AUG19_UK_LU.csv"
)

PATH_AREA_ROAD_LENGTH = Path(
    r"C:\Users\sceac10\OneDrive - Cardiff University\04 - Projects\22 - Heat demand scotland\data\GIS data\length_road_and_area.csv"
)

PATH_GEO_SCOT_LOOKUP = Path(
    r'C:\Users\sceac10\OneDrive - Cardiff University\04 - Projects\22 - Heat demand scotland\data\geo_lookup_tables\SPD_PostcodeIndex_Cut_23_1_CSV\SmallUser.csv'
)


def remove_duplicates(dataf: pd.DataFrame) -> pd.DataFrame:
  """Keep only the most uptodate EPC"""
  dataf = dataf.sort_values(
      [schema.EPCSchema.property_id, schema.EPCSchema.date_epc])
  dataf.drop_duplicates([schema.EPCSchema.property_id],
                        keep="last",
                        inplace=True)
  return dataf


def get_scottish_LAs_from(dataf: pd.DataFrame) -> list[str]:
  """Return the list of LAs in Scotland"""
  return list(dataf.loc[dataf[schema.geoLookupSchema.lsoa].str[0] == 'S',
                        schema.geoLookupSchema.ladnm].unique())


def standardise_str(dataf: pd.DataFrame, target_column: str) -> pd.DataFrame:
  dataf[target_column] = dataf[target_column].str.strip().str.lower(
  ).str.replace('-', '')
  dataf[target_column].fillna("uncategorized", inplace=True)
  return dataf


def strip_spaces(dataf: pd.DataFrame, target_column: str) -> pd.DataFrame:
  dataf[target_column] = dataf[target_column].str.replace(' ', '')
  dataf[target_column].fillna("uncategorized", inplace=True)
  return dataf


def assign_dwelling_type(dataf: pd.DataFrame) -> pd.DataFrame:
  """Assign dwelling type to each EPC record."""
  dataf[schema.outputEPCSchema.dwelling_type] = None
  dataf.loc[dataf[schema.EPCSchema.built_form] == 'Semi-Detached',
            schema.outputEPCSchema.
            dwelling_type] = enums.dwelling_types.SEMIDETACHED.value
  dataf.loc[dataf[schema.EPCSchema.built_form] == 'Detached',
            schema.outputEPCSchema.
            dwelling_type] = enums.dwelling_types.DETACHED.value
  dataf.loc[dataf[schema.EPCSchema.built_form] == 'End-Terrace',
            schema.outputEPCSchema.
            dwelling_type] = enums.dwelling_types.TERRACED.value
  dataf.loc[dataf[schema.EPCSchema.built_form] == 'Mid-Terrace',
            schema.outputEPCSchema.
            dwelling_type] = enums.dwelling_types.TERRACED.value
  dataf.loc[dataf[schema.EPCSchema.built_form] == 'Enclosed End-Terrace',
            schema.outputEPCSchema.
            dwelling_type] = enums.dwelling_types.TERRACED.value
  dataf.loc[dataf[schema.EPCSchema.built_form] == 'Enclosed Mid-Terrace',
            schema.outputEPCSchema.
            dwelling_type] = enums.dwelling_types.TERRACED.value

  dataf.loc[
      dataf[schema.EPCSchema.property_type] == 'Flat',
      schema.outputEPCSchema.dwelling_type] = enums.dwelling_types.FLAT.value
  dataf.loc[
      dataf[schema.EPCSchema.property_type] == 'Maisonette',
      schema.outputEPCSchema.dwelling_type] = enums.dwelling_types.FLAT.value
  return dataf


def unassigned_epc(dataf: pd.DataFrame) -> pd.DataFrame:
  filt = (dataf[schema.outputEPCSchema.dwelling_type]
          == None) | (dataf[schema.outputEPCSchema.heating_system]
                      == enums.heating_systems.UNCATEGORIZED.value)
  return dataf.loc[filt]


def assign_heating_system(dataf: pd.DataFrame) -> pd.DataFrame:
  """Assign the heating system to each EPC record"""
  dataf[schema.EPCSchema.heating_system] = dataf[
      schema.EPCSchema.heating_system].str.split('|').str[0].str.lower()
  dataf[schema.outputEPCSchema.
        heating_system] = enums.heating_systems.UNCATEGORIZED.value

  resistance_heaters_keywords = [
      "portable electric", 'electric storage', 'electric', 'b30k',
      'room heaters'
  ]
  oil_boiler_keywords = ['oil']
  solid_fuel_boilers_keywords = [
      'biomass', 'wood', 'coal', 'smokeless fuel', 'anthracite',
      'liquid biofuel'
  ]
  gas_boiler_keywords = ["mains gas", "lpg"]
  hp_keywords = ["heat pump"]
  dh_keywords = ['community']

  def get_filter(dataf: pd.DataFrame, list_keywords: list[str]) -> list[bool]:
    filt = dataf[schema.EPCSchema.heating_system].str.contains(
        '|'.join(list_keywords)).to_list()
    return filt

  dataf.loc[get_filter(dataf, oil_boiler_keywords), schema.outputEPCSchema.
            heating_system] = enums.heating_systems.OILBOILER.value
  dataf.loc[get_filter(dataf, solid_fuel_boilers_keywords),
            schema.outputEPCSchema.
            heating_system] = enums.heating_systems.SOLIDFUELBOILER.value
  dataf.loc[get_filter(dataf, resistance_heaters_keywords),
            schema.outputEPCSchema.
            heating_system] = enums.heating_systems.RESISTANCE.value
  dataf.loc[get_filter(dataf, gas_boiler_keywords), schema.outputEPCSchema.
            heating_system] = enums.heating_systems.GASBOILER.value
  dataf.loc[
      get_filter(dataf, hp_keywords),
      schema.outputEPCSchema.heating_system] = enums.heating_systems.HP.value
  dataf.loc[
      get_filter(dataf, dh_keywords),
      schema.outputEPCSchema.heating_system] = enums.heating_systems.DH.value
  return dataf


def get_dwelling_category(dwelling_type: str, heating_system: str) -> str:

  return f'{dwelling_type} {heating_system}'


def get_LA_code_to_name_lookup() -> pd.DataFrame:
  geo_lookup = pd.read_csv(PATH_GEO_LOOKUP,
                           encoding='ISO-8859-1',
                           low_memory=False)
  geo_lookup = standardise_str(geo_lookup, schema.geoLookupSchema.ladnm)
  columns_to_keep = [
      schema.geoLookupSchema.ladcd, schema.geoLookupSchema.ladnm
  ]
  geo_lookup = geo_lookup.loc[:, columns_to_keep].copy()
  return geo_lookup.drop_duplicates().reset_index(drop=True)


def get_postcode_lsoa_scotland_lookup() -> pd.DataFrame:
  la_lookup = get_LA_code_to_name_lookup()
  geo_lookup = pd.read_csv(PATH_GEO_SCOT_LOOKUP, low_memory=False)
  columns_to_keep = [
      schema.geoLookupScotSchema.postcode, schema.geoLookupScotSchema.oa,
      schema.geoLookupScotSchema.lsoa, schema.geoLookupScotSchema.msoa,
      schema.geoLookupScotSchema.ladcd
  ]
  geo_lookup = geo_lookup.loc[:, columns_to_keep].copy()
  geo_lookup[schema.geoLookupScotSchema.postcode] = geo_lookup[
      schema.geoLookupScotSchema.postcode].str.replace(' ', '')

  geo_lookup = pd.merge(geo_lookup,
                        la_lookup,
                        left_on=schema.geoLookupScotSchema.ladcd,
                        right_on=schema.geoLookupSchema.ladcd)
  geo_lookup = geo_lookup.drop(schema.geoLookupSchema.ladcd, axis=1)
  rename_dict = {
      schema.geoLookupScotSchema.postcode: schema.geoLookupSchema.postcode,
      schema.geoLookupScotSchema.oa: schema.geoLookupSchema.oa,
      schema.geoLookupScotSchema.lsoa: schema.geoLookupSchema.lsoa,
      schema.geoLookupScotSchema.msoa: schema.geoLookupSchema.msoa,
      schema.geoLookupScotSchema.ladcd: schema.geoLookupSchema.ladcd
  }
  geo_lookup = geo_lookup.rename(columns=rename_dict)
  return geo_lookup


def get_postcode_lsoa_lookup(target_LA: str) -> pd.DataFrame:
  geo_lookup = pd.read_csv(PATH_GEO_LOOKUP,
                           encoding='ISO-8859-1',
                           low_memory=False)
  geo_lookup = standardise_str(geo_lookup, schema.geoLookupSchema.ladnm)
  filt = [True] * len(geo_lookup)
  if len(target_LA) > 0:
    filt = filt & (geo_lookup[schema.geoLookupSchema.ladnm] == target_LA)
  columns_to_keep = [
      schema.geoLookupSchema.postcode, schema.geoLookupSchema.oa,
      schema.geoLookupSchema.lsoa, schema.geoLookupSchema.msoa,
      schema.geoLookupSchema.ladcd, schema.geoLookupSchema.ladnm
  ]
  geo_lookup = geo_lookup.loc[filt, columns_to_keep].copy()
  geo_lookup[schema.geoLookupSchema.postcode] = geo_lookup[
      schema.geoLookupSchema.postcode].str.replace(' ', '')
  return geo_lookup.drop_duplicates()


def assign_geography_codes(dataf: pd.DataFrame,
                           postcode_lsoa_lookup: pd.DataFrame) -> pd.DataFrame:
  dataf = pd.merge(dataf,
                   postcode_lsoa_lookup,
                   left_on=schema.outputEPCSchema.postcode,
                   right_on=schema.geoLookupSchema.postcode,
                   how="left")
  return dataf


def create_additional_columns(dataf: pd.DataFrame) -> pd.DataFrame:
  """Create the additional columns required and remove the unused columns."""
  dataf[schema.outputEPCSchema.dwelling_category] = dataf[
      schema.outputEPCSchema.dwelling_type] + " " + dataf[
          schema.outputEPCSchema.heating_system]
  dataf[schema.outputEPCSchema.current_total_heating] = dataf[
      schema.EPCSchema.space_heating] + dataf[schema.EPCSchema.hot_water]

  current_cost_columns = [
      schema.EPCSchema.current_space_heating_cost,
      schema.EPCSchema.current_hot_water_cost
  ]
  potential_cost_columns = [
      schema.EPCSchema.potential_space_heating_cost,
      schema.EPCSchema.potential_hot_water_cost
  ]
  dataf["Potential improvements"] = (dataf[potential_cost_columns].sum(
      axis=1) - dataf[current_cost_columns].sum(
          axis=1)) / dataf[current_cost_columns].sum(axis=1)

  dataf[schema.outputEPCSchema.potential_total_heating] = dataf[
      schema.outputEPCSchema.current_total_heating] * (
          1 + dataf["Potential improvements"])
  rename_dict = {
      schema.EPCSchema.floor_area:
      schema.outputEPCSchema.floor_area,
      schema.EPCSchema.current_EPC:
      schema.outputEPCSchema.current_EPC,
      schema.EPCSchema.current_EPC_rating:
      schema.outputEPCSchema.current_EPC_rating,
      schema.EPCSchema.potential_EPC:
      schema.outputEPCSchema.potential_EPC,
      schema.EPCSchema.potential_EPC_rating:
      schema.outputEPCSchema.potential_EPC_rating,
  }

  dataf.rename(columns=rename_dict, inplace=True)

  columns_to_keep = [
      schema.outputEPCSchema.dwelling_category,
      schema.outputEPCSchema.current_total_heating,
      schema.outputEPCSchema.potential_total_heating,
      schema.outputEPCSchema.dwelling_type,
      schema.outputEPCSchema.heating_system,
      schema.outputEPCSchema.postcode,
      schema.outputEPCSchema.local_authority,
      schema.outputEPCSchema.floor_area,
      schema.outputEPCSchema.current_EPC,
      schema.outputEPCSchema.current_EPC_rating,
      schema.outputEPCSchema.potential_EPC,
      schema.outputEPCSchema.potential_EPC_rating,
  ]
  dataf = dataf[columns_to_keep].copy()

  return dataf


def remove_energy_intensity_outliers(dataf: pd.DataFrame) -> pd.DataFrame:
  max_kwh_m2 = 200
  min_kwh_m2 = 15  # minimum intensity Passive House (Passivhaus) standard is at 15 kWh/m2
  filt = ((dataf[schema.outputEPCSchema.current_total_heating] /
           dataf[schema.outputEPCSchema.floor_area]) > min_kwh_m2)
  filt = filt & ((dataf[schema.outputEPCSchema.current_total_heating] /
                  dataf[schema.outputEPCSchema.floor_area]) < max_kwh_m2)
  return dataf[filt].copy()


def remove_floor_area_outliers(dataf: pd.DataFrame) -> pd.DataFrame:
  max_floor_area_m2 = 500
  filt = (dataf[schema.outputEPCSchema.floor_area] < max_floor_area_m2)
  return dataf[filt].copy()


def create_skeleton(dataf: pd.DataFrame) -> pd.DataFrame:
  skeleton_df = dataf[[
      schema.skeletonSchema.lsoa, schema.skeletonSchema.msoa,
      schema.skeletonSchema.ladcd, schema.skeletonSchema.ladnm
  ]].copy()
  skeleton_df = skeleton_df.drop_duplicates()
  skeleton_df.set_index(schema.skeletonSchema.lsoa, inplace=True, drop=True)
  return skeleton_df


def transform_dataf(dataf: pd.DataFrame, col_names_func: Callable[[list[str]],
                                                                  list[str]]):
  """Pivot dataframe and change the columns names"""
  dataf = dataf.unstack(0)
  dataf.columns = dataf.columns.droplevel(0)
  dataf.columns = col_names_func(dataf.columns)
  return dataf


def get_annual_heat_demand_from_EPCs(dataf: pd.DataFrame, geography_level: str,
                                     before_EE: bool) -> pd.DataFrame:
  if before_EE:
    temp_annual_heat_demand = (dataf.groupby([
        schema.outputEPCSchema.dwelling_category, geography_level
    ]).agg({schema.outputEPCSchema.current_total_heating: 'mean'}))
  else:
    temp_annual_heat_demand = (dataf.groupby([
        schema.outputEPCSchema.dwelling_category, geography_level
    ]).agg({schema.outputEPCSchema.potential_total_heating: 'mean'}))
  return temp_annual_heat_demand


def get_floor_area_from_EPCs(dataf: pd.DataFrame,
                             geography_level: str) -> pd.DataFrame:
  temp_floor_area = (dataf.groupby(
      [schema.outputEPCSchema.dwelling_category,
       geography_level]).agg({schema.outputEPCSchema.floor_area: 'mean'}))
  return temp_floor_area


def get_list_dwelling_categories() -> list[str]:
  list_heating_systems = [c.value for c in enums.heating_systems]
  list_dwelling_systems = [c.value for c in enums.dwelling_types]
  list_dwelling_categories = [
      " ".join(c)
      for c in itertools.product(list_dwelling_systems, list_heating_systems)
  ]
  return list_dwelling_categories


def get_floor_area_cols(list_dwelling_categories: list[str]) -> list[str]:
  list_floor_area_cols = [
      f"Average floor area of {dwel_cat} (m2)"
      for dwel_cat in list_dwelling_categories
  ]
  return list_floor_area_cols


def get_annual_heat_demand_cols(list_dwelling_categories: list[str],
                                before_EE: bool) -> list[str]:
  if before_EE:
    list_annual_heat_demand_cols = [
        f"Average heat demand before energy efficiency measures for {dwel_cat} (kWh)"
        for dwel_cat in list_dwelling_categories
    ]
  else:
    list_annual_heat_demand_cols = [
        f"Average heat demand after energy efficiency measures for {dwel_cat} (kWh)"
        for dwel_cat in list_dwelling_categories
    ]
  return list_annual_heat_demand_cols


def create_data_structure(geography_codes_lookup: pd.DataFrame,
                          geography_level: str) -> pd.DataFrame:
  """Return data structure with dwelling category and lsoas of the input dataf."""
  list_columns = get_list_dwelling_categories()
  list_lsoas = geography_codes_lookup[geography_level].unique()
  names = [schema.skeletonSchema.dwelling_category, geography_level]
  multi_index_data = pd.MultiIndex.from_product([list_columns, list_lsoas],
                                                names=names)
  data_structure_df = pd.DataFrame(index=multi_index_data)
  return data_structure_df


def get_annual_heat_demand(dataf: pd.DataFrame, geography_level: str,
                           epc_dataf: pd.DataFrame,
                           before_EE: bool) -> pd.DataFrame:
  """Extract current annual heat demand from epc and add it to the data structure."""
  extracted_epc_dataf = get_annual_heat_demand_from_EPCs(
      epc_dataf, geography_level, before_EE)
  dataf = dataf.merge(extracted_epc_dataf,
                      left_index=True,
                      right_index=True,
                      how="left")
  temp_func = partial(get_annual_heat_demand_cols, before_EE=before_EE)
  dataf = transform_dataf(dataf, temp_func)
  return dataf


def get_floor_area(dataf: pd.DataFrame, geography_level: str,
                   epc_dataf: pd.DataFrame) -> pd.DataFrame:
  extracted_epc_dataf = get_floor_area_from_EPCs(epc_dataf, geography_level)
  dataf = dataf.merge(extracted_epc_dataf,
                      left_index=True,
                      right_index=True,
                      how="left")
  dataf = transform_dataf(dataf, get_floor_area_cols)
  return dataf


def get_annual_heat_demand_and_fill_gaps(epc_dataf: pd.DataFrame,
                                         skeleton: pd.DataFrame,
                                         geo_code_df: pd.DataFrame,
                                         before_EE: bool) -> pd.DataFrame:
  final_df = pd.DataFrame()
  for geo_level in [
      schema.skeletonSchema.lsoa, schema.skeletonSchema.msoa,
      schema.skeletonSchema.ladcd
  ]:
    data_structure = create_data_structure(geo_code_df, geo_level)
    temp_annual_heat_demand = get_annual_heat_demand(data_structure.copy(),
                                                     geo_level,
                                                     epc_dataf,
                                                     before_EE=before_EE)
    temp_annual_heat_demand = skeleton.merge(temp_annual_heat_demand,
                                             left_on=geo_level,
                                             right_on=geo_level)
    temp_annual_heat_demand.sort_values(by="lsoa11cd", inplace=True)
    temp_annual_heat_demand.reset_index(inplace=True, drop=True)
    if len(final_df) == 0:
      final_df = temp_annual_heat_demand
    else:
      final_df.fillna(temp_annual_heat_demand, inplace=True)
  final_df.set_index([
      schema.skeletonSchema.lsoa, schema.skeletonSchema.msoa,
      schema.skeletonSchema.ladcd, schema.skeletonSchema.ladnm
  ],
                     inplace=True,
                     drop=True)
  return final_df


def get_floor_area_and_fill_gaps(epc_dataf: pd.DataFrame,
                                 skeleton: pd.DataFrame,
                                 geo_code_df: pd.DataFrame) -> pd.DataFrame:
  final_df = pd.DataFrame()
  for geo_level in [
      schema.skeletonSchema.lsoa, schema.skeletonSchema.msoa,
      schema.skeletonSchema.ladcd
  ]:
    data_structure = create_data_structure(geo_code_df, geo_level)
    temp_annual_floor_area = get_floor_area(data_structure.copy(), geo_level,
                                            epc_dataf)
    temp_annual_floor_area = skeleton.merge(temp_annual_floor_area,
                                            left_on=geo_level,
                                            right_on=geo_level)
    temp_annual_floor_area.sort_values(by="lsoa11cd", inplace=True)
    temp_annual_floor_area.reset_index(inplace=True, drop=True)
    if len(final_df) == 0:
      final_df = temp_annual_floor_area
    else:
      final_df.fillna(temp_annual_floor_area, inplace=True)
  final_df.set_index([
      schema.skeletonSchema.lsoa, schema.skeletonSchema.msoa,
      schema.skeletonSchema.ladcd, schema.skeletonSchema.ladnm
  ],
                     inplace=True,
                     drop=True)

  return final_df


def extract_epc_data_for_la(target_la: str,
                            geography_codes_lookup: pd.DataFrame):
  dataf = pd.read_csv(PATH_EPC_BY_LA / f"{target_la}.csv",
                      low_memory=False,
                      index_col=0)

  dataf = (dataf.pipe(assign_dwelling_type).pipe(assign_heating_system))

  unassigned_dataf = unassigned_epc(dataf)
  dataf = (dataf.pipe(create_additional_columns).pipe(assign_geography_codes,
                                                      geography_codes_lookup))
  geography_codes_lookup = dataf[geography_codes_lookup.columns].copy()
  epc_dataf = dataf.pipe(remove_energy_intensity_outliers).pipe(
      remove_floor_area_outliers)

  skeleton_df = create_skeleton(geography_codes_lookup).reset_index()

  current_annual_heat_demand = get_annual_heat_demand_and_fill_gaps(
      epc_dataf, skeleton_df, geography_codes_lookup, True)
  potential_annual_heat_demand = get_annual_heat_demand_and_fill_gaps(
      epc_dataf, skeleton_df, geography_codes_lookup, False)
  floor_area = get_floor_area_and_fill_gaps(epc_dataf, skeleton_df,
                                            geography_codes_lookup)
  temp_lsoa_data = pd.concat(
      [current_annual_heat_demand, potential_annual_heat_demand, floor_area],
      axis=1,
      sort=False)

  return temp_lsoa_data, unassigned_dataf


def add_road_length(dataf):
  road_df = pd.read_csv(PATH_AREA_ROAD_LENGTH).drop_duplicates()
  road_df.rename(columns={'LENGTH': schema.ukercSchema.road_length},
                 inplace=True)
  road_df[schema.ukercSchema.road_length].fillna(-1, inplace=True)

  dataf = pd.merge(dataf,
                   road_df[["DataZone", schema.ukercSchema.road_length]],
                   left_on=schema.skeletonSchema.lsoa,
                   right_on="DataZone",
                   how='left')
  dataf.drop('DataZone', axis=1, inplace=True)
  return dataf


def add_area_LSOA(dataf):
  area_df = pd.read_csv(PATH_AREA_ROAD_LENGTH).drop_duplicates()
  area_df[schema.ukercSchema.area] = area_df["Shape_Area"] / 1000000
  dataf = pd.merge(dataf,
                   area_df[["DataZone", schema.ukercSchema.area]],
                   left_on=schema.skeletonSchema.lsoa,
                   right_on="DataZone",
                   how='left')
  dataf[schema.ukercSchema.area].fillna(-1, inplace=True)
  dataf.drop('DataZone', axis=1, inplace=True)
  return dataf
