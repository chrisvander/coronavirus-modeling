import math
import random
import pandas
from tqdm import tqdm
from population import generate
from util.webapi import cache, init_nhts
from gis import GastonCountyGIS as gcgis
import numpy as np
from scipy.spatial import distance_matrix

trip_purposes = {
    1: "Home",
    2: "Home (paid work from home)",
    3: "Work",
    4: "Work trip/meeting",
    5: "Volunteer activity",
    6: "Drop off/pick up",
    7: "",
    8: "School",
    9: "Child care",
    10: "Adult care",
    11: "Buy goods",
    12: "Buy services",
    13: "",
    14: "",
    15: "",
    16: "",
    17: "",
    18: "",
    19: ""
}

activity_type = {
    1: "H",
    2: "H",
    3: "W",
    4: "W",
    5: "O",
    6: "O",
    7: "O",
    8: "C",
    9: "O",
    10: "O",
    11: "S",
    12: "S",
    13: "O",
    14: "O",
    15: "O",
    16: "O",
    17: "O",
    18: "O",
    19: "O",
}

family_income = {
    1: "< $10,000",
    2: "$10,000 to $14,999",
    3: "$15,000 to $24,999",
    4: "$25,000 to 34,999",
    5: "35,000 to 49,999",
    6: "50,000 to 74,999",
    7: "75,000 to $99,999",
    8: "$100,000 to $124,999",
    9: "$125,000 to $149,999",
    10: "$150,000 to $199,999",
    11: "> $200,000"
}


def income_bracket(income):
    if income < 10000:
        return 1
    if income < 15000:
        return 2
    if income < 25000:
        return 3
    if income < 35000:
        return 4
    if income < 50000:
        return 5
    if income < 75000:
        return 6
    if income < 100000:
        return 7
    if income < 125000:
        return 8
    if income < 150000:
        return 9
    if income < 200000:
        return 10
    return 11


trip_cols = ["HOUSEID", "PERSONID", "HHFAMINC", "WHYTO",
             "WHYFROM", "STRTTIME", "ENDTIME", "TRPMILES", "R_AGE_IMP", "R_SEX_IMP"]


class Trip:
    '''A trip between two unspecified locations for one person.'''

    def __init__(self, st_time, end_time, whyfrom, whyto):
        self.start_time = st_time
        self.end_time = end_time
        self.whyfrom = whyfrom
        self.whyto = whyto

    def __str__(self):
        return ", ".join([f"{k}: {v}" for k, v in self.__dict__.items()])

    def deepcopy(self):
        trip = Trip(self.start_time, self.end_time, self.whyfrom, self.whyto)
        return trip

    @staticmethod
    def from_dfrow(dfrow):
        st = dfrow["STRTTIME"]
        et = dfrow["ENDTIME"]
        src = dfrow["WHYFROM"]
        dest = dfrow["WHYTO"]
        trip = Trip(st, et, src, dest)
        trip.household_id = dfrow["HOUSEID"]
        trip.person_id = dfrow["PERSONID"]
        return trip


class Activity:
    '''Data type used to represent where a person is and for how long.'''

    def __init__(self, start_time, end_time, loc_type):
        self.start_time = start_time
        self.end_time = end_time
        self.loc_type = loc_type

        self.location = None

    def assign_location(self, location):
        self.location = location

    def deepcopy(self):
        act = Activity(self.start_time, self.end_time, self.loc_type)
        act.location = self.location
        return act

    def attr_dict(self):
        return {"starttime": self.start_time,
                "endtime": self.end_time, "acttype": self.loc_type}


class SyntheticPerson:
    '''Sample individual, including demographic information and daily activity schedules'''

    def __init__(self, person_id):
        self.id = person_id

        self.household = None

        # Person demographic info
        self.income = 0
        self.age = 0
        self.sex = 0

        self.trips = []
        self.activities = []

    def _gen_activities(self):
        '''Generate persons daily activities using trip data.'''

        # Ensure that trips are ordered before generating activities
        self.trips.sort(key=lambda a: a.start_time)

        for i in range(len(self.trips)):
            trip = self.trips[i]
            last_trip = self.trips[i - 1]

            start_time = last_trip.end_time
            end_time = trip.start_time

            if start_time > end_time:
                # Activities should start at 0 and end at 2399
                self.activities.append(
                    Activity(0, end_time, activity_type[trip.whyfrom]))
                self.activities.append(
                    Activity(start_time, 2399, activity_type[trip.whyfrom]))
            else:
                self.activities.append(
                    Activity(start_time, end_time, activity_type[trip.whyfrom]))

    def __str__(self):
        s = f"Person {self.id}:\n"
        for trip in self.trips:
            s += "\t" + str(trip) + "\n"
        return s

    def attr_dict(self):
        return {"age": str(self.age), "income": str(self.income),
                "sex": str(self.sex), "hhsize": str(len(self.household.people)) if hasattr(self, 'household') and self.household is not None else 'NA'}

    def deepcopy(self):
        p = SyntheticPerson(self.id)
        p.trips = [trip.deepcopy() for trip in self.trips]
        p.activities = [activity.deepcopy() for activity in self.activities]
        p.age = self.age
        p.sex = self.sex
        p.income = self.income
        return p

    @staticmethod
    def from_nhts_df(pid, df):
        syn_person = SyntheticPerson(pid)
        syn_person.trips = [Trip.from_dfrow(row) for i, row in df.iterrows()]
        syn_person._gen_activities()
        syn_person.age = df.iloc[0]["R_AGE_IMP"]
        syn_person.sex = df.iloc[0]["R_SEX_IMP"]
        syn_person.income = 0
        return syn_person


class SyntheticHousehold:
    def __init__(self, household_id):
        self.id = household_id

        self.people = []
        self.income = 0

    @staticmethod
    def from_nhts_df(hhid, df):
        syn_hh = SyntheticHousehold(hhid)
        syn_hh.income = df.iloc[0]["HHFAMINC"]
        p_ids = df["PERSONID"].unique()
        p_trips = df.groupby(["PERSONID"])

        # Create people in household
        for pid, group in p_trips:
            syn_person = SyntheticPerson.from_nhts_df(pid, group)
            syn_hh.people.append(syn_person)

        return syn_hh

    def deepcopy(self):
        hh = SyntheticHousehold(self.id)
        hh.income = self.income
        hh.people = [person.deepcopy() for person in self.people]
        return hh

    def __str__(self):
        s = f"Household {self.id}:\n"
        for person in self.people:
            p_str = "\t".join(("\n" + str(person)).splitlines(True))
            s += p_str + "\n"
        return s


class Location:
    def __init__(self, loc_id, loc_type, coords):
        self.id = loc_id
        self.location_type = loc_type
        self.coordinates = coords

    def attr_dict(self):
        return {"coords": str(self.coordinates), "loctype": self.location_type}


def templates():
    print("Reading NHTS trip data.")
    init_nhts()
    df = pandas.read_csv("data/nhts/trippub.csv", ",")

    df.sort_values(by=["HOUSEID", "PERSONID", "STRTTIME"], inplace=True)

    # Filter out "other" trip purposes
    useable_trip_purposes = list(trip_purposes.keys())
    useable_fam_inc = list(family_income.keys())
    filtered = df.loc[(df["WHYFROM"].isin(useable_trip_purposes))
                      & (df["WHYTO"].isin(useable_trip_purposes))
                      & (df["HHFAMINC"].isin(useable_fam_inc))]

    # Split trips by household id
    hhids = filtered["HOUSEID"].unique()
    hh_trips = filtered.groupby(["HOUSEID"])

    # Create synthetic households from dataframe
    for hhid, group in tqdm(hh_trips, total=len(hhids)):
        synth_hh = SyntheticHousehold.from_nhts_df(hhid, group)
        yield synth_hh


def merge_census_data(census_hhs, template_hhs):
    def match(census_hh, template_hh):
        if len(census_hh.getPeople()) != len(template_hh.people):
            return False
        if income_bracket(census_hh.getHHIncome()) != template_hh.income:
            return False
        # Match individuals

        return True

    def matching_template_households(census_household):
        matching = []
        for template_hh in template_hhs:
            if match(census_household, template_hh):
                matching.append(template_hh)
        return matching

    # Select census_hh
    matches = []
    with tqdm(total=len(census_hhs)) as pbar:
        for census_hh in census_hhs:
            # Select matching template_hh
            matching = matching_template_households(census_hh)
            if len(matching) > 0:
                matches.append(random.choice(matching))
            pbar.update(1)

    return matches


def assign_locations(households, n):
    print("Loading location data:")
    locations = [loc for loc in gcgis.get_locations()]

    print("Shopping...")
    shopping = [loc for loc in gcgis.get_shoping_locations()]

    print("Homes...")
    home = [loc for loc in gcgis.get_home_locations()]

    print("Schools...")
    schools = [loc for loc in gcgis.get_school_locations()]

    print("Workplaces...")
    work = [loc for loc in gcgis.get_work_locations()]

    print("Other...")
    other = [loc for loc in gcgis.get_other_locations()]

    num_locations = len(locations)
    num_homes = len(home)
    num_shops = len(shopping)
    num_schools = len(schools)
    num_workplaces = len(work)
    num_other = len(other)

    random.shuffle(shopping)
    random.shuffle(schools)
    random.shuffle(home)
    random.shuffle(other)
    random.shuffle(work)

    # Downscale lists
    scale = n / num_locations
    shopping = shopping[:math.ceil(scale * num_shops)]
    schools = schools[:math.ceil(scale * num_schools)]
    work = work[:math.ceil(scale * num_workplaces)]
    home = home[:math.ceil(scale * num_homes)]
    other = other[:math.ceil(scale * num_other)]
    num_homes = len(home)
    num_shops = len(shopping)
    num_schools = len(schools)
    num_workplaces = len(work)
    num_other = len(other)

    print(f"Sampling from roughly {n} locations:")
    print(f"\tHome: {num_homes}")
    print(f"\tWork: {num_workplaces}")
    print(f"\tSchool: {num_schools}")
    print(f"\tShop: {num_shops}")
    print(f"\tOther: {num_other}")

    for hh in households:
        hh_loc = home[random.randint(0, num_homes - 1)]
        for person in hh.people:
            for activity in person.activities:
                act_type = activity.loc_type
                if act_type == "H":
                    activity.assign_location(hh_loc)
                elif act_type == "W":
                    work_loc = work[random.randint(0, num_workplaces - 1)]
                    activity.assign_location(work_loc)
                elif act_type == "C":
                    school_loc = schools[random.randint(0, num_schools - 1)]
                    activity.assign_location(school_loc)
                elif act_type == "S":
                    shop_loc = shopping[random.randint(0, num_shops - 1)]
                    activity.assign_location(shop_loc)
                else:
                    other_loc = other[random.randint(0, num_other - 1)]
                    activity.assign_location(other_loc)


def assign_dummy_locations(households, num_locations):
    locations = [Location(i, "?", (0, 0, 0)) for i in range(num_locations)]

    for hh in households:
        for person in hh.people:
            for activity in person.activities:
                activity.assign_location(locations[random.randint(0, num_locations - 1)])


def generate_locations():
    def distance(a, b):
        return np.linalg.norm(a - b)

    print("Creating location data")
    locations = [loc for loc in gcgis.get_locations()]
    coords = np.array([np.array(loc.coordinates) for loc in locations])
    print(coords.shape)
    l = len(locations)

    # # Calculate distance matrix
    # dist_mat = distance_matrix(coords, coords)
    # print(dist_mat)

    attractiveness = np.zeros((l, 5))
    for i in range(l):
        use = locations[i].location_type
        if use in gcgis.homes:
            attractiveness[i, 0] = 1
        if use in gcgis.workplaces:
            attractiveness[i, 1] = 1
        if use in gcgis.shopping:
            attractiveness[i, 2] = 1
        if use in gcgis.schools:
            attractiveness[i, 3] = 1

    b_w = 1

    probs = np.zeros((l, 5))

    for i in tqdm(range(l)):
        for j in range(l):
            attractiveness[j, 0] * np.exp(b_w * distance(coords[i], coords[j]))


def generate_synthetic(n):
    print("Creating template households.")
    nhts_hh_templates = cache(
        'template_households', lambda: [
            hhtmp for hhtmp in templates()],
        folder='nhts_templates')

    print("Generating sample population.")
    census_hhs = generate(n)

    print("Matching population households to template households.")
    synthetic_households = cache(
        str(n) + '_synthetic',
        lambda: merge_census_data(
            census_hhs,
            nhts_hh_templates), folder='synthetic_hh')

    print("Assigning activity locations.")
    # 4 people to a location avg (work, home, etc)
    assign_locations(synthetic_households, int(n / 4))
    # assign_locations(synthetic_households)

    return synthetic_households


if __name__ == "__main__":
    generate_synthetic(3000)
