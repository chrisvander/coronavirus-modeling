import math
import random
import pandas
from tqdm import tqdm
from population import generate
from util.webapi import cache

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
    19: "",
    97: ""
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
    97: "O"

}

family_income = {
    -7: "Prefer not to answer",
    -8: "I don't know",
    -9: "Not ascertained",
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
             "WHYFROM", "STRTTIME", "ENDTIME", "TRPMILES", "R_AGE", "R_SEX_IMP"]


class Trip:
    def __init__(self, st_time, end_time, whyfrom, whyto):
        self.start_time = st_time
        self.end_time = end_time
        self.whyfrom = whyfrom
        self.whyto = whyto

    def __str__(self):
        return ", ".join([f"{k}: {v}" for k, v in self.__dict__.items()])

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


class Location:
    def __init__(self):
        self.uid = 0

    def attr_dict(self):
        return {"coords": "None", "type": "None"}


class Activity:
    def __init__(self, start_time, end_time, loc_type):
        self.start_time = start_time
        self.end_time = end_time
        self.loc_type = loc_type

        self.location = None

    def assign_location(self, location):
        self.location = Location()
        self.location.uid = location

    def attr_dict(self):
        return {"starttime": self.start_time, "endtime": self.end_time}


class SyntheticPerson:
    def __init__(self, person_id, trips):
        self.id = person_id
        self.trips = trips
        self.activities = []
        self.uid = ""

        self.income = 0
        self.age = 0
        self.sex = 0

        self._gen_activities()

    def _gen_activities(self):
        for trip in self.trips:
            self.activities.append(
                Activity(trip.start_time, trip.end_time, activity_type[trip.whyto]))

    def set_uid(self, uid):
        self.uid = uid

    def __str__(self):
        s = f"Person {self.id}:\n"
        for trip in self.trips:
            s += "\t" + str(trip) + "\n"
        return s

    def attr_dict(self):
        return {"age": str(self.age), "income": str(self.income),
                "sex": str(self.sex), "householdsize": str(0)}

    @staticmethod
    def from_nhts_df(pid, df):
        trips = [Trip.from_dfrow(row) for i, row in df.iterrows()]
        syn_person = SyntheticPerson(pid, trips)
        syn_person.age = df.iloc[0]["R_AGE"]
        syn_person.sex = df.iloc[0]["R_SEX_IMP"]
        syn_person.income = 0
        return syn_person


class SyntheticHousehold:
    def __init__(self, household_id):
        self.id = household_id

        self.people = []
        self.income = 0
        self.uid = ""

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

    def set_uid(self, uid):
        self.uid = uid

    def __str__(self):
        s = f"Household {self.id}:\n"
        for person in self.people:
            p_str = "\t".join(("\n" + str(person)).splitlines(True))
            s += p_str + "\n"
        return s


def templates():
    print("Reading NHTS trip data.")
    df = pandas.read_csv("data/nhts/trippub.csv", ",")

    df.sort_values(by=["HOUSEID", "PERSONID", "STRTTIME"], inplace=True)

    # Filter out "other" trip purposes
    useable_trip_purposes = list(trip_purposes.keys())
    filtered = df.loc[(df["WHYFROM"].isin(useable_trip_purposes))
                      & (df["WHYTO"].isin(useable_trip_purposes))]

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


def assign_dummy_locations(households, num_locations):
    for hh in households:
        for person in hh.people:
            for activity in person.activities:
                activity.assign_location(random.randint(0, num_locations))


def assign_locations(households):
    '''
    First, we generate a probability matrix to represent the transition between
    activity locations. There are 4 anchor activity types: H (home), W (work),
    S (shop), C (school).

    Each index i, j in the matrix will represent a probability proportional to:
        P(j|i) = A_aj * e^(b_w * D_ij)
    where:
        A_aj:   Attractiveness of location j for destination activity a.
                Either 0 or 1. This is essentially a boolean mask (b/c you don't go
                shopping at home a home location or to school at a work location).
        e_b:    Calibration constant.
        D_ij:   distance between locations i and j
    '''
    raise NotImplementedError()


def assign_uids(households):
    p_count = 0
    hh_count = 0
    for hh in households:
        for person in hh.people:
            person.set_uid(f"P_{p_count}")
            p_count += 1


def generate_synthetic(n):
    print("Creating template households.")
    nhts_hh_templates = cache('template_households', lambda: [hhtmp for hhtmp in templates()])

    print("Generating sample population.")
    census_hhs = cache(str(n) + '_population', lambda: generate(n))

    print("Matching population households to template households.")
    synthetic_households = cache(str(n) + '_synthetic', lambda: merge_census_data(census_hhs, nhts_hh_templates))

    print("Assigning unique IDs")
    assign_uids(synthetic_households)

    print("Assigning activity locations.")
    assign_dummy_locations(synthetic_households, 5000)
    # assign_locations(synthetic_households)

    return synthetic_households


if __name__ == "__main__":
    generate_synthetic(3000)
