import random
import data

class Person:
  def __init__(self, age, gender):
    self.age = age
    self.gender = gender
    self.household = 0
  def __str__(self):
    return "foo"

# generate n samples from the provided population in data
def sample(n):
  result = []
  percents, ages, sexes = data.get_probs()
  # sample sex
  weights = []
  for s in sexes:
    weights.append(sum(percents[s]))
  print(weights)
  gender_samples = random.choices(sexes, k=n, weights=weights) 
  for s in sexes:
    num_for_s = gender_samples.count(s)
    age_samples = random.choices(ages[s], k=num_for_s, weights=percents[s])
    result.extend(list(map(lambda sample: Person(sample, s), age_samples)))
  return result

class UrbanActor:
  def __init__(self, person):
    self.demographic = {}
    self.demographic.update(person.__dict__)

def generate(n, config):
  print("-- GENERATE POPULATION --")
  print("Creating population of size", n)
  people = sample(n)
  
