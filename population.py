from util.webapi import get_json, parse_query
import numpy as np
import random
import data


class Person:
    def __init__(self, age, income, gender):
        self.age = age
        self.income = income
        self.gender = gender
        self.household = 0


# generate n samples from the provided population in data
def sample(n):
    result = []
    percents, ages, sexes = data.get_probs()
    weights = []
    for s in sexes:
        weights.append(sum(percents[s]))
    gender_samples = random.choices(sexes, k=n, weights=weights)
    for s in sexes:
        num_for_s = gender_samples.count(s)
        print(num_for_s, s)
        age_samples = random.choices(ages[s], k=num_for_s, weights=percents[s])
        result.extend(list(map(lambda sample: Person(sample, s), age_samples)))
    return result


class UrbanActor:
    def __init__(self, person):
        self.demographic = {}
        self.demographic.update(person.__dict__)


def generate(n, config):
  print("-- GENERATE POPULATION --")
  p = Person(23, 50000, 'male')
  ua = UrbanActor(p)

  # PWGTP - Weight, 
  # POWPUMA - Place of Work by subcounty (hotspot)
  # AGEP  - age
  # JWRIP - describes vehicle occupancy
  # JWAP  - time of arrival at work
  # JWDP  - time of departure for work
  # PINCP - personal income
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

