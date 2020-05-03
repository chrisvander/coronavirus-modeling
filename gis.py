from typing import Tuple, Sequence
import geopandas as gpd
from tqdm import tqdm

Coordinates = Sequence[float]
LandUse = str

simple_parcel_use = {
    '1010': 'Residential',
    '1020': 'Residential',
    '1030': 'Residential',
    '1040': 'Residential',
    '1050': 'Residential',
    '1060': 'Residential',
    '1070': 'Residential',
    '1080': 'Residential',
    '1090': 'Residential',
    '2007': 'Residential',
    '2010': 'Commercial',
    '2020': 'Retail',
    '2020': 'Retail',
    '2030': 'Retail',
    '2040': 'Retail',
    '2050': 'Restaurant',
    '2060': 'Commercial',
    '2070': 'Medical',
    '2090': 'Pet',
    '2100': 'Residential',
    '2110': 'Gas',
    '2120': 'Hotel',
    '2130': 'Retail',
    '4020': 'School',
    '4030': 'Organization',
    '4040': 'Religious',
    '4080': 'Medical',
    '4090': 'Volunteer'
}


class Location:
    def __init__(self, loc_id, loc_type, coords):
        self.id = loc_id
        self.location_type = loc_type
        self.coordinates = coords

    def attr_dict(self):
        return {"coords": str(self.coordinates), "loctype": self.location_type}


class GastonCountyGIS:
    workplaces = [
        '2000', '2010', '2020', '2030', '2040',
        '2050', '2060', '2070', '2090', '2110',
        '2120', '2130', '2140', '2150', '2160',
        '2170', '2180', '2190', '2200', '2210',
        '2230', '2240', '2270', '2280', '3000',
        '3001', '3002', '3003', '3005', '3006',
        '3010', '3020', '3030', '3040', '3050',
        '4010', '4015', '4020', '4040', '4050',
        '4080', '4090']
    homes = [
        '1010', '1020', '1030', '1040', '1050',
        '1060', '1070', '1080', '1130', '2007']
    schools = ['4020']
    shopping = [
        '2020', '2030', '2040', '2110']
    locations = list(set(workplaces + homes + schools + shopping))

    shape_file = "data/ncgis/nc_gaston_parcels_pt.shp"
    _geodataframe = None

    @staticmethod
    def _load_data():
        if GastonCountyGIS._geodataframe is None:
            GastonCountyGIS._geodataframe = gpd.read_file(GastonCountyGIS.shape_file)

    @staticmethod
    def get_locations():
        GastonCountyGIS._load_data()
        df = GastonCountyGIS._geodataframe
        filtered = df[(df["PARUSECODE"].isin(GastonCountyGIS.locations))]
        for i, row in tqdm(filtered.iterrows(), total=filtered.shape[0]):
            parno = row["PARNO"]
            use = row["PARUSECODE"]
            coords = row["geometry"]
            yield Location(parno, use, list(coords.coords)[0])

    @staticmethod
    def get_work_locations():
        GastonCountyGIS._load_data()
        df = GastonCountyGIS._geodataframe
        filtered = df[(df["PARUSECODE"].isin(GastonCountyGIS.workplaces))]
        for i, row in tqdm(filtered.iterrows(), total=filtered.shape[0]):
            parno = row["PARNO"]
            use = row["PARUSECODE"]
            coords = row["geometry"]
            yield Location(parno, use, list(coords.coords)[0])

    @staticmethod
    def get_home_locations():
        GastonCountyGIS._load_data()
        df = GastonCountyGIS._geodataframe
        filtered = df[(df["PARUSECODE"].isin(GastonCountyGIS.homes))]
        for i, row in tqdm(filtered.iterrows(), total=filtered.shape[0]):
            parno = row["PARNO"]
            use = row["PARUSECODE"]
            coords = row["geometry"]
            yield Location(parno, use, list(coords.coords)[0])

    @staticmethod
    def get_shoping_locations():
        GastonCountyGIS._load_data()
        df = GastonCountyGIS._geodataframe
        filtered = df[(df["PARUSECODE"].isin(GastonCountyGIS.shopping))]
        for i, row in tqdm(filtered.iterrows(), total=filtered.shape[0]):
            parno = row["PARNO"]
            use = row["PARUSECODE"]
            coords = row["geometry"]
            yield Location(parno, use, list(coords.coords)[0])

    @staticmethod
    def get_school_locations():
        GastonCountyGIS._load_data()
        df = GastonCountyGIS._geodataframe
        filtered = df[(df["PARUSECODE"].isin(GastonCountyGIS.schools))]
        for i, row in tqdm(filtered.iterrows(), total=filtered.shape[0]):
            parno = row["PARNO"]
            use = row["PARUSECODE"]
            coords = row["geometry"]
            yield Location(parno, use, list(coords.coords)[0])

    @staticmethod
    def get_other_locations():
        GastonCountyGIS._load_data()
        df = GastonCountyGIS._geodataframe
        filtered = df[~(df["PARUSECODE"].isin(GastonCountyGIS.locations))]
        for i, row in tqdm(filtered.iterrows(), total=filtered.shape[0]):
            parno = row["PARNO"]
            use = row["PARUSECODE"]
            coords = row["geometry"]
            yield Location(parno, use, list(coords.coords)[0])
