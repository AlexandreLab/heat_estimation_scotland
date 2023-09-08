class EPCSchema:
  property_id = "Property_UPRN"
  postcode = "Postcode"
  date_epc = "Date of Certificate"
  space_heating = "Space Heating"
  hot_water = "Water Heating"
  current_space_heating_cost = "Current heating costs over 3 years (£)"
  potential_space_heating_cost = "Potential heating costs over 3 years (£)"
  current_hot_water_cost = "Current hot water costs over 3 years (£)"
  potential_hot_water_cost = "Potential hot water costs over 3 years (£)"
  improvements = "Improvements"
  local_authority = "Local Authority"
  built_form = "Built Form"
  property_type = "Property Type"
  heating_system = "MAINHEAT_DESCRIPTION"
  floor_area = "Total floor area (m²)"
  current_EPC = "Current energy efficiency rating band"
  current_EPC_rating = "Current energy efficiency rating"
  potential_EPC = "Potential Energy Efficiency Rating"
  potential_EPC_rating = "Potential energy efficiency rating band"

class censusSchema:
  detached = 'Detached'
  semi_detached = 'Semi-detached'
  terraced = 'Terraced'
  flat = 'Flat, maisonette or apartment, or mobile/temporary accommodation'
  no_central_heating = 'No central heating'
  gas_heating = '     Gas central heating'
  electric_heating = '     Electric (including storage heaters) central heating'
  oil_heating = '     Oil central heating'
  solid_fuel_heating = '     Solid fuel (for example wood, coal) central heating'
  other = '     Other central heating'


class finalCensusSchema:
  dwelling_type = "Dwelling type"
  heating_system = "Heating system"
  dwelling_category = "Dwelling category"
  number = "Number of dwellings"
  oa_code = "OA_code"
  lsoa = "lsoa11cd"


class skeletonSchema:
  lsoa = "lsoa11cd"
  msoa = "msoa11cd"
  ladcd = "ladcd"
  ladnm = "ladnm"
  dwelling_category = "Dwelling category"
  total_number_dwelling = "Total number of dwellings in 2011"

class geoLookupSchema: 
  """Schema for England and Wales geocodes"""
  postcode = "pcds"
  oa = "oa11cd"
  lsoa = "lsoa11cd"
  msoa = "msoa11cd"
  ladcd = "ladcd"
  ladnm = "ladnm"

class ukercSchema:
  lsoa = "LSOA11CD"
  ladnm = "Local authority (2011)"
  road_length = 'Road length (m)'
  area = 'Area (km2)'

class geoLookupScotSchema: 
  """Schema for Scotland geocodes"""
  postcode = 'Postcode'
  oa = 'OutputArea2011Code'
  lsoa = 'DataZone2011Code'
  msoa = 'IntermediateZone2011Code'
  ladcd = "RegistrationDistrict2007Code"
  ladnm = "ladnm"

class outputEPCSchema:
  dwelling_type = "Dwelling type"
  heating_system = "Heating system"
  dwelling_category = "Dwelling category"
  current_total_heating = "Current annual heat demand (kWh)"
  potential_total_heating = "Potential annual heat demand (kWh)"
  floor_area = "Total floor area (m²)"
  postcode = "Postcode"
  lsoa = "lsoa11cd"
  local_authority = "Local Authority"
  current_EPC = "Current energy efficiency rating band"
  current_EPC_rating = "Current energy efficiency rating"
  potential_EPC = "Potential Energy Efficiency Rating"
  potential_EPC_rating = "Potential energy efficiency rating band"
