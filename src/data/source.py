from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..common import schema
from ..models import thermal_model


@dataclass
class SimulationData:
  dwelling:thermal_model.ThermalModel
  era5_data :pd.DataFrame
  sim_data: pd.DataFrame = field(init=False)
  timestep_simulation:int = 1
  CDD_ref_temperature:float = 24.
  HHD_ref_temperatre:float = 15.5
  resampling_timestep:int = 3600 # 3600s or one hour

  def __post_init__(self):
    cooling_weeks = self.get_cooling_weeks(self.CDD_ref_temperature)
    self.add_heating_season_flag(cooling_weeks)

  @property
  def all_months(self)->list[int]:
    return self.era5_data.index.month.unique().to_list()

  @property
  def all_years(self)->list[int]:
    return self.era5_data.index.year.unique().to_list()
  
  @property
  def all_weeks(self)->list[int]:
    return list(self.era5_data.index.isocalendar().week.unique())

  def filter_era5_data(self, list_weeks: list[int]|None=None, list_months:list[int]|None=None, list_years:list[int]|None=None)->pd.DataFrame:
    """Return a filtered copy of the data"""
    if list_weeks is None:
      list_weeks = self.all_weeks
    if list_months is None:
      list_months = self.all_months
    if list_years is None:
      list_years = self.all_years

    filt = (self.era5_data.index.year.isin(list_years) & self.era5_data.index.month.isin(list_months) & self.era5_data.index.isocalendar().week.isin(list_weeks))
    return self.era5_data.loc[filt, :].copy()


  def get_cooling_weeks(self, CDD_ref_temperature:float)->list[int]:
      """Return a list of the weeks for which cooling is required."""
      cdd_col = f"{schema.OutputDataSchema.CDD}_{CDD_ref_temperature}"
      cooling_seasons:list[int] = list(self.era5_data.loc[self.era5_data[cdd_col]>0].index.isocalendar().week.unique())
      cooling_seasons = list(np.arange(min(cooling_seasons), max(cooling_seasons)+1))
      return cooling_seasons

  def add_heating_season_flag(self, weeks_with_cooling:list[int]|None= None)->None:
    """Add heating/cooling season flag within the dataset"""
    self.era5_data[schema.OutputDataSchema.HEATINGSEASON] = 1
    self.era5_data.loc[self.era5_data.index.isocalendar().week.isin(weeks_with_cooling), schema.OutputDataSchema.HEATINGSEASON] = 0

  def create_simulation_data_skeleton(self, length_simulation:int)->pd.DataFrame:
      columns_dtypes = {
              schema.DataSchema.IAT: 'float64',
              schema.DataSchema.OAT: 'float64',
              schema.DataSchema.HEATINGOUTPUT: 'float64',
              schema.DataSchema.SOLARRADIATION: 'float64',
              schema.DataSchema.SOLARGAINS:'float64',
              schema.DataSchema.HEATINGSEASON: int
      }
      dataf = pd.DataFrame({col_name:pd.Series(dtype=col_type) for col_name, col_type in columns_dtypes.items()},
          index=np.arange(length_simulation))
      dataf.index = dataf.index.to_numpy()*self.timestep_simulation
      self.sim_data = dataf
      
      return dataf

  def create_default_simulation_data(self)->pd.DataFrame:
    """Create default data considering fixed indoor and outdoor air temperature, no heating output and no solar gains."""
    dataf = self.sim_data
    dataf.loc[0, schema.DataSchema.IAT] = self.dwelling.initial_indoor_air_temperature
    dataf.loc[:, schema.DataSchema.OAT] = self.dwelling.outdoor_air_temperature
    dataf.loc[:, schema.DataSchema.HEATINGOUTPUT] = 0.
    dataf.loc[:, schema.DataSchema.SOLARRADIATION] = 0.
    dataf.loc[:, schema.DataSchema.SOLARGAINS] = 0.
    dataf.loc[:, schema.DataSchema.HEATINGSEASON] = 1
    dataf = dataf.astype(float)
    return self.sim_data.copy()

  def add_heating_output(self, heating_output:float)->pd.DataFrame:
    """Add a constant heating output value to the simulation data. Return a copy of the simulation data."""
    self.sim_data.loc[:, schema.DataSchema.HEATINGOUTPUT] = heating_output
    return self.sim_data.copy()

  def estimate_solar_gains(self)->pd.DataFrame:
    """Estimate the solar gains of the building. Return a copy of the simulation data."""
    def solar_gains(solar_flux:float)->float:
      A = 0.25*self.dwelling.floor_area #Opening areas (including windows, roof windows, rooflights and doors), assumed to be 25% of total floor area
      g_t = 0.76 # transmittance factor for double glazed
      frame_factor = 0.7 
      summer_solar_access = 0.9 #summer_solar_access factor
      return 0.9*A*solar_flux*g_t*frame_factor*summer_solar_access/1000
    self.sim_data[schema.DataSchema.SOLARGAINS] = self.sim_data[schema.DataSchema.SOLARRADIATION].apply(lambda x: solar_gains(x))
    return self.sim_data.copy()

# def estimate_cooling_demand(R:float, degree_days:float, COP:float)->float:
#     """Estimate the number of energy to heat/cool a dwelling based on the number of degree days.
#     -R in [kW/K]
#     -degree_days [K]
#     -COP: efficient of heating/cooling system"""
#     return R*degree_days*24/COP

  def create_era5_based_simulation_data(self,estimate_solar_gains:bool|None=True, list_weeks: list[int]|None=None, list_months:list[int]|None=None, list_years:list[int]|None=None):
    filtered_era5_data = self.filter_era5_data(list_weeks=list_weeks, list_months=list_months, list_years=list_years)
    filtered_era5_data.reset_index(inplace=True, drop=True)
    filtered_era5_data.index = filtered_era5_data.index.values*60*60 # convert index to seconds
    length_simulation = filtered_era5_data.index.values[-1]/self.timestep_simulation+1
    simulation_data = self.create_simulation_data_skeleton(length_simulation)
    self.sim_data = simulation_data
    self.create_default_simulation_data()

    self.sim_data.loc[:, schema.DataSchema.OAT] = np.nan
    self.sim_data.loc[filtered_era5_data.index, schema.DataSchema.OAT] = filtered_era5_data.loc[filtered_era5_data.index, schema.OutputDataSchema.OAT].values
    self.sim_data[schema.DataSchema.OAT].fillna(self.sim_data[schema.DataSchema.OAT].interpolate(), inplace=True)

    self.sim_data.loc[:, schema.DataSchema.HEATINGSEASON] = np.nan
    self.sim_data.loc[filtered_era5_data.index, schema.DataSchema.HEATINGSEASON] = filtered_era5_data.loc[filtered_era5_data.index, schema.OutputDataSchema.HEATINGSEASON].values
    self.sim_data[schema.DataSchema.HEATINGSEASON].fillna(method='ffill', inplace=True)


    if estimate_solar_gains:
      self.sim_data.loc[:, schema.DataSchema.SOLARRADIATION] = np.nan
      self.sim_data.loc[filtered_era5_data.index, schema.DataSchema.SOLARRADIATION] = filtered_era5_data.loc[filtered_era5_data.index, schema.OutputDataSchema.SOLARRADIATION].values
      self.sim_data[schema.DataSchema.SOLARRADIATION].fillna(self.sim_data[schema.DataSchema.SOLARRADIATION].interpolate(), inplace=True)
      self.estimate_solar_gains()
    return simulation_data.copy()

    # filtered_index = filtered_era5_data.index
    # filtered_index = filtered_index[filtered_index<=rcmodel_dataf.index[-1]]
    # rcmodel_dataf.loc[0, schema.DataSchema.IAT] = initial_indoor_air_temperature

    # rcmodel_dataf.loc[filtered_index, schema.DataSchema.OAT] = input_data.loc[filtered_index, schema.OutputDataSchema.OAT].values
    # rcmodel_dataf[schema.DataSchema.OAT].fillna(rcmodel_dataf[schema.DataSchema.OAT].interpolate(), inplace=True)

    # rcmodel_dataf.loc[filtered_index, schema.DataSchema.SOLARRADIATION] = input_data.loc[filtered_index, schema.OutputDataSchema.SOLARRADIATION].values
    # rcmodel_dataf[schema.DataSchema.SOLARRADIATION].fillna(rcmodel_dataf[schema.DataSchema.SOLARRADIATION].interpolate(), inplace=True)

    # rcmodel_dataf.loc[filtered_index, schema.DataSchema.HEATINGSEASON] = input_data.loc[filtered_index, schema.OutputDataSchema.HEATINGSEASON].values
    # rcmodel_dataf[schema.DataSchema.HEATINGSEASON].fillna(method='ffill', inplace=True)

    # rcmodel_dataf.loc[:, schema.DataSchema.HEATINGOUTPUT] = 0.
    # rcmodel_dataf.head()

  def resample_modelling_results(self, simulation_results:pd.DataFrame)->pd.DataFrame:
    """Resample the results to decrease amount of data and for visualisation purposes."""
    simulation_results[schema.DataSchema.TIME] = simulation_results.index.values//self.resampling_timestep
    return simulation_results.groupby(schema.DataSchema.TIME).mean()


