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
  print("Creating population of size", n)
  p = Person(23, 50000, 'male')
  ua = UrbanActor(p)
