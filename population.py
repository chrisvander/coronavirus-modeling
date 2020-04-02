from util.webapi import get_json, parse_query
import numpy as np
import random

# must have fields:
#   household income
#   household population density (sq mile)
#   
class Household:
  def __init__(self):
    pass

class Person:
    def __init__(self, age, income, gender):
      self.age = age
      self.income = income
      self.gender = gender
      self.household = 0

class UrbanActor:
    def __init__(self, person):
        self.demographic = {}
        self.demographic.update(person.__dict__)

def generate(n):
  print("-- GENERATE POPULATION --")

  # PWGTP - Weight, 
  # POWPUMA - Place of Work by subcounty (hotspot)
  # AGEP  - age
  # JWRIP - describes vehicle occupancy
  # JWAP  - time of arrival at work
  # JWDP  - time of departure for work
  # PINCP - personal income
  # PUMA  - (ignore) region of no less than 10,000 people
  # ST    - State
  url = "https://api.census.gov/data/2018/acs/acs1/pums?get=PWGTP,AGEP,SEX,PINCP&ucgid=7950000US3703001,7950000US3703002"
  res = get_json(url, {})

  headers = np.array(res)[0]
  print(headers)
  data = np.array(res)[1:]
  print(data)
  print(data[:, 0].astype(int).sum())

  # print("-- GENERATE POPULATION --")
  # print("Creating population of size", n)
  # people = sample(n)

