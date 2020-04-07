from util.webapi import get_json, parse_query
import numpy as np
from scipy.stats import norm
import itertools
import random

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
  def addPerson(self,person):
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
  def getSize(self):
    return len(self.people)

class Person:
    def __init__(self, age, income, gender):
      self.age = int(age)
      self.income = int(income)
      if income == -19999:
        self.income = None
      self.gender = 'm' if gender == 1 else 'f'
      self.household = 0
    def getAge(self):
      return self.age
    def getGender(self):
      return self.gender

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
  print("-- GENERATE POPULATION --")
  print("Sampling a population of size " + str(n) + "...")
  data, weights = import_person_data()
  samples = random.choices(data, k=n, weights=weights)
  population = list(map(lambda p : Person(p[1],p[3],p[2]), samples))

  print("Fetching household data...")
  sample_households, hh_weights = import_household_data()
  households = []

  # get adult population information
  adult_sample_households = list(filter(lambda hh : int(hh[1]) >= 18, sample_households))
  selectors = [int(hh[1]) >= 18 for hh in sample_households]
  adult_hh_weights = list(itertools.compress(hh_weights, selectors))
    
  rv = norm(scale=3) # normal distribution
  rv_weights = []
  for i in range(0,100):
    w = []
    for j in range(0,100):
      w.append(rv.pdf(i-j))
    rv_weights.append(w)

  wide_norm = norm(scale=50)
  ch_weights = []
  for i in range(0,100):
    ch_weights.append(rv.pdf(i-10))
  weightChildren = lambda x : ch_weights[x]

  print("Generating selection of households...")
  while len(population) > 0:
    # we take the list of people and select households
    # first, grab a household that we will select upon (filtered by adult presence)
    hh_sample = random.choices(adult_sample_households, k=1, weights=adult_hh_weights)[0]
    hh = Household()

    # generate each time, population is changing
    adult_population = list(filter(lambda p : p.getAge() >= 18, population))
    if len(adult_population) > 0:
      # -- PICK HEAD OF HOUSEHOLD --
      # head age of this household (with reference to the sample data)
      preferred_head_age = int(hh_sample[1])
      # get population weights and grab a sample that is closest to the selected age
      pop_weights = [rv_weights[preferred_head_age][p.getAge()] for p in adult_population]
      hh_head = random.choices(adult_population, k=1, weights=pop_weights)[0]
      population.remove(hh_head)
      hh.addHead(hh_head)

      # -- SELECT THE REMAINDER OF THE HOUSEHOLD BY SIZE --
      hht = hh_sample[2]
      if hht != 4 and hht != 6:
        if len(population) > 0:
          if hht == 1:
            # fetch spouse
            spouse = random.choices(adult_population, k=1, weights=pop_weights)[0]
            population.remove(spouse)
            hh.addSpouse(spouse)
          for i in range(int(hh_sample[2])-hh.getSize()):
            if len(population) > 0:
              child_weights = [weightChildren(p.getAge()) for p in population]
              p = random.choices(population, k=1, weights=child_weights)[0]
              population.remove(p)
              hh.addPerson(p)
      households.append(hh)
    else:
      if len(population) > 0:
        print("Didn't include " + len(population) + "people")
      break
  print("Generated " + str(len(households)) + " households.")








