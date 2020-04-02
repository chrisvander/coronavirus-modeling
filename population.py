from util.webapi import get_json, parse_query
import numpy as np


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


def generate(n, config):
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
