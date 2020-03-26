# using the census_data.json file in it's current format,
# parse out probabilities of generating each age/gender

import json
import re

def normalize(lst, total):
  return list(map(lambda x : x / total, lst))

def get_probs():
  with open('./data/census_data.json', 'r') as f:
    census_dict = json.load(f)
    sexes = ["male", "female"]
    ages = {}
    nums = {}
    total = 0
    for s in sexes:
      ages[s] = []
      nums[s] = []
      data = census_dict[s]
      total += data['total']
      for key, num in data.items():
        if key == 'total':
          continue
        n = re.match("([0-9]+)\-([0-9]+)", key)
        if n:
          num1,num2 = n.groups()
          new_ages = list(range(int(num1),int(num2)+1))
        else:
          n = re.match("([0-9]+)\+", key)
          new_ages = list(range(int(n.groups()[0]),101))
        num = num/len(new_ages)
        nums[s].extend([num] * len(new_ages))
        ages[s].extend(new_ages)
    for s in sexes:
      nums[s] = normalize(nums[s], total)
    return (nums, ages, sexes)


    