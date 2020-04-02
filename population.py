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


<< << << < HEAD
print("-- GENERATE POPULATION --")
p = Person(23, 50000, 'male')
ua = UrbanActor(p)


if __name__ == "__main__":
    # cols = ["PWGTP", "COW", "AGEP"]
    # url = "https://api.census.gov/data/2018/acs/acs5/pums"
    # query = {
    #     "get": cols,
    #     "ucgid": "7950000US4500103"
    # }

    url = "https://api.census.gov/data/2018/acs/acs1/pums?get=PWGTP,POWPUMA,AGEP,JWRIP,SEX,JWAP,JWDP&ucgid=7950000US3703001,7950000US3703002"
    res = get_json(url, {})

    data = np.array(res)[1:]
    print(data[:, 0].astype(int).sum())
== == == =
print("-- GENERATE POPULATION --")
print("Creating population of size", n)
people = sample(n)
>>>>>> > 2e754b92c5130e15bdf72809985f103f17609d6d
