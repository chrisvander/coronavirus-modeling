from util.webapi import get_json, parse_query
import numpy as np
import random

base_url = "https://api.census.gov/data/2018/acs/acs1/pums?get="

def_region = "7950000US3703001,7950000US3703002"

def get_household_json(region):
  url = base_url + 'PWGTP,AGEP,HHT,HUPAC,NOC'
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
    pass

class Person:
    def __init__(self, age, income, gender):
      self.age = int(age)
      self.income = int(income)
      if income == -19999:
        self.income = None
      self.gender = gender
      self.household = 0
    def getAge(self):
      return self.age

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
  data, weights = import_person_data()
  samples = random.choices(data, k=n, weights=weights)
  people = map(lambda p : Person(p[1],p[3],p[2]), samples)

  sample_households, hh_weights = import_household_data()

  # we take the list of people and select households
  hh = random.choices(sample_households, k=1, weights=hh_weights)[0]
  hh_age = int(hh[1])
  print(hh_age)
  head_hh = list(filter(lambda p: p.getAge() == hh_age, people))
  print(head_hh)









