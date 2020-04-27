from util.webapi import get_json, parse_query
from tqdm import tqdm
import numpy as np
from scipy.stats import norm
import itertools
import random

'''
    Responsible for creating the population that the urban actor
    model will then ingest. Just creates raw households and people
    based on data from the U.S. Census.
    
'''

base_url = "https://api.census.gov/data/2018/acs/acs1/pums?get="

def_region = "7950000US3703001,7950000US3703002"


def get_household_json(region):
    url = base_url + 'PWGTP,AGEP,HHT,NP'
    if region is not None:
        url = url + '&ucgid=' + region
    return get_json(url, {})


def get_person_json(region):
    url = base_url + 'PWGTP,AGEP,SEX,PINCP'
    if region is not None:
        url = url + '&ucgid=' + region
    return get_json(url, {})

# must have fields:
#   household income
#   household population density (sq mile)


class Household:
    def __init__(self):
        self.people = []
        self.head = None
        self.spouse = None
        self.otherMembers = []

    def addPerson(self, person):
        self.people.append(person)
        self.otherMembers.append(person)

    def getPeople(self):
        return self.people

    def getOtherMembers(self):
        return self.otherMembers

    def addHead(self, person):
        self.people.append(person)
        self.head = person

    def addSpouse(self, person):
        self.people.append(person)
        self.spouse = person

    def getHead(self):
        return self.head

    def getSpouse(self):
        return self.spouse

    def getSize(self):
        return len(self.people)

    def getHHIncome(self):
        return sum([person.getIncome() for person in self.people])

    def print(self):
        print("All People: " + str(len(self.people)))
        print(", ".join([str(person.getAge()) + person.getGender()
                         for person in self.people]))
        print("HH Income: $" + str(self.getHHIncome()))
        print("")


class Person:
    def __init__(self, age, income, gender):
        self.age = int(age)
        self.income = int(income)
        if self.income == -19999:
            self.income = 0
        self.gender = 'm' if gender == '1' else 'f'
        self.household = 0

    def getAge(self):
        return self.age

    def getGender(self):
        return self.gender

    def getIncome(self):
        return self.income

    def print(self):
        print("Gender: " + self.gender)
        print("Age: " + str(self.age))
        print("Income: $" + str(self.income) + "\n")


class UrbanActor:
    def __init__(self, person):
        self.demographic = {}
        self.demographic.update(person.__dict__)


def import_person_data():
    # PWGTP - Weight,
    # POWPUMA - Place of Work by subcounty (hotspot)
    # AGEP  - age
    # JWRIP - describes vehicle occupancy
    # JWAP  - time of arrival at work
    # JWDP  - time of departure for work
    # PINCP - personal income
    # PUMA  - (ignore) region of no less than 10,000 people
    # ST    - State
    res = get_person_json(def_region)

    headers = res[0]
    data = res[1:]
    weights = np.array(data)[:, 0].astype(int)
    return data, weights


def import_household_data():
    res = get_household_json(def_region)
    data = list(filter(lambda x: int(x[1]) is not 0, res[1:]))
    headers = res[0]
    weight = np.array(data)[:, 0].astype(int)
    # htype = np.array(data)[:, 1].astype(int)
    return data, weight


def generate(n):
    print("\n-- GENERATE POPULATION --")
    print("Sampling a population of size " + str(n) + "...")
    data, weights = import_person_data()
    samples = random.choices(data, k=n, weights=weights)
    population = list(map(lambda p: Person(p[1], p[3], p[2]), samples))

    # print("Sample People: \n")
    # for i in range(3):
    #     person = random.choice(population)
    #     person.print()

    sample_households, hh_weights = import_household_data()
    households = []

    # get adult population information
    adult_sample_households = list(filter(lambda hh: int(hh[1]) >= 18, sample_households))
    selectors = [int(hh[1]) >= 18 for hh in sample_households]
    adult_hh_weights = list(itertools.compress(hh_weights, selectors))

    rv = norm(scale=3)  # normal distribution

    # weight children more heavily when selecting the rest of a household
    wide_norm = norm(scale=30)
    ch_weights = []
    for i in range(0, 100):
        ch_weights.append(rv.pdf(i - 10))

    def weightChildren(x): return ch_weights[x]
    chWeights = [weightChildren(p.getAge()) for p in population]

    adult_population = list(filter(lambda p: p.getAge() >= 24, population))

    # pdf is slow, so we precalculate results
    pdf_vals = []
    for i in range(-100, 100):
        pdf_vals.append(rv.pdf(i))

    print("Generating probability distributions...")
    rv_weights = []
    for i in tqdm(range(0, 100)):
        w = []
        for p in adult_population:
            w.append(pdf_vals[p.getAge() - i])
        rv_weights.append(w)

    def removePerson(p):
        if (p.getAge() >= 24):
            a_ind = adult_population.index(p)
            for w in rv_weights:
                w.pop(a_ind)
            adult_population.remove(p)
        p_ind = population.index(p)
        chWeights.pop(p_ind)
        population.remove(p)

    print("Generating selection of households...")
    t = len(population)
    with tqdm(total=t) as pbar:
        while len(population) > 0:
            before=len(population)
            # we take the list of people and select households
            # first, grab a household that we will select upon (filtered by adult presence)
            hh_sample = random.choices(
                adult_sample_households,
                k=1,
                weights=adult_hh_weights)[0]
            hh = Household()

            if len(adult_population) > 0:
                # -- PICK HEAD OF HOUSEHOLD --
                # head age of this household (with reference to the sample data)
                preferred_head_age = int(hh_sample[1])
                # get population weights and grab a sample that is closest to the selected age
                hh_head = random.choices(
                    adult_population,
                    k=1,
                    weights=rv_weights[preferred_head_age])[0]
                removePerson(hh_head)
                hh.addHead(hh_head)

                # -- SELECT THE REMAINDER OF THE HOUSEHOLD BY SIZE --
                hht = hh_sample[2]
                if hht != 4 and hht != 6:
                    if len(population) > 0:
                        if hht == 1:
                            # fetch spouse
                            spouse = random.choices(
                                adult_population, k=1, weights=rv_weights[preferred_head_age])[0]
                            removePerson(spouse)
                            hh.addSpouse(spouse)
                        for i in range(int(hh_sample[2]) - hh.getSize()):
                            if len(population) > 0:
                                p = random.choices(population, k=1, weights=chWeights)[0]
                                removePerson(p)
                                hh.addPerson(p)
                households.append(hh)
            else:
                if len(population) > 0:
                    print("Didn't include " + str(len(population)) + " people")
                break
            pbar.update(before-len(population))
    print("Generated " + str(len(households)) + " households.\n")
    # print("Sample Households: \n")
    # for i in range(3):
    #     household = random.choice(households)
    #     household.print()

    return households
