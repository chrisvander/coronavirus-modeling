import pandas
from tqdm import tqdm

trip_purposes = {
    -7: "",
    -8: "",
    -9: "",
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

activity_types = {
    1: "Home",
    2: "Home",
    3: "Work",
    4: "Work",
    5: "Other",
    6: "Other",
    7: "Other",
    8: "School",
    9: "School",
    10: "Other",
    11: "Shop",
    12: "Shop"
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

trip_cols = ["HOUSEID", "PERSONID", "HHFAMINC", "WHYTO",
             "WHYFROM", "STRTTIME", "ENDTIME", "TRPMILES"]


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


class Activity:
    def __init__(self, start_time, end_time, loc_type):
        self.start_time = start_time
        self.end_time = end_time
        self.loc_type = loc_type


class SyntheticPerson:
    def __init__(self, person_id, trips):
        self.id = person_id
        self.trips = trips
        self.activities = []

        self._gen_activities()

    def _gen_activities(self):
        for trip in self.trips:
            self.activities.append(Activity(trip.start_time, trip.end_time, ))

    def __str__(self):
        s = f"Person {self.id}:\n"
        for trip in self.trips:
            s += "\t" + str(trip) + "\n"
        return s

    @staticmethod
    def from_nhts_df(pid, df):
        trips = [Trip.from_dfrow(row) for i, row in df.iterrows()]
        syn_person = SyntheticPerson(pid, trips)
        return syn_person


class SyntheticHousehold:
    def __init__(self, household_id):
        self.id = household_id

        self.people = []
        self.income = 0

    @staticmethod
    def from_nhts_df(hhid, df):
        syn_hh = SyntheticHousehold(hhid)
        p_ids = df["PERSONID"].unique()
        p_trips = df.groupby(["PERSONID"])

        for pid, group in p_trips:
            syn_person = SyntheticPerson.from_nhts_df(pid, group)
            syn_hh.people.append(syn_person)

        return syn_hh

    def __str__(self):
        s = f"Household {self.id}:\n"
        for person in self.people:
            p_str = "\t".join(("\n" + str(person)).splitlines(True))
            s += p_str + "\n"
        return s


def templates(df):
    df.sort_values(by=["HOUSEID", "PERSONID", "STRTTIME"], inplace=True)

    # Filter out "other" trip purposes
    # useable_trip_purposes = list(trip_purposes.keys())
    # filtered = df.loc[(df["WHYFROM"].isin(useable_trip_purposes))
    #                   & (df["WHYTO"].isin(useable_trip_purposes))]

    # Split trips by household id
    hhids = df["HOUSEID"].unique()
    hh_trips = df.groupby(["HOUSEID"])

    # Create synthetic households from dataframe
    for hhid, group in tqdm(hh_trips, total=len(hhids)):
        synth_hh = SyntheticHousehold.from_nhts_df(hhid, group)
        yield synth_hh


def merge_census_data(census_hhs, template_hhs):
    pass


def assign_locations(households):
    pass


if __name__ == "__main__":
    print("Reading trip data.")
    trips_df = pandas.read_csv("data/nhts/trippub.csv", ",")

    # Create household templates from nhts data
    nhts_hh_templates = [hhtmp for hhtmp in templates(trips_df)]

    # Pull census households
    census_hhs = None

    # Match census households to template households
    synthetic_households = merge_census_data(census_hhs)

    # Assign activity locations to trip destinations
    assign_locations(synthetic_households)
