from util.webapi import get_json, parse_query
import numpy as np
import random

region_url = "https://api.census.gov/data/2018/acs/acs1/pums?get=PWGTP,AGEP,SEX,PINCP&ucgid=7950000US3703001,7950000US3703002"
us_url = "https://api.census.gov/data/2018/acs/acs1/pums?get=PWGTP,AGEP,SEX,PINCP"

# must have fields:
#   household income
#   household population density (sq mile)

class Household:
  def __init__(self):
    pass

class Person:
    def __init__(self, age, income, gender):
      self.age = age
      self.income = income
      if income == -19999:
        self.income = None
      self.gender = gender
      self.household = 0

class UrbanActor:
    def __init__(self, person):
        self.demographic = {}
        self.demographic.update(person.__dict__)

def import_data():
  # PWGTP - Weight, 
  # POWPUMA - Place of Work by subcounty (hotspot)
  # AGEP  - age
  # JWRIP - describes vehicle occupancy
  # JWAP  - time of arrival at work
  # JWDP  - time of departure for work
  # PINCP - personal income
  # PUMA  - (ignore) region of no less than 10,000 people
  # ST    - State
  res = get_json(region_url, {})

  headers = res[0]
  print(headers)
  data = res[1:]
  weights = np.array(data)[:, 0].astype(int)
  return data, weights

def generate(n):
  print("-- GENERATE POPULATION --")
  data, weights = import_data()
  samples = random.choices(data, k=n, weights=weights)
  print(np.array(samples))

  people = map(lambda p : Person(p[1],p[3],p[2]), samples)

