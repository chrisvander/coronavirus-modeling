#!/usr/bin/python

import sys, getopt
# import json

import population
import epidemic

def import_json(filename):
  with open(filename, 'r') as f:
    return json.load(f)

def main(argv):
  n = ''
  try:
    opts, args = getopt.getopt(argv,"hn:",['help','pop_size='])
  except getopt.GetoptError:
      print('app.py -n <population size>')
      sys.exit(2)
  for opt, arg in opts:
    if opt == '-h' or opt == '--help':
      print('app.py -n <population size>')
      sys.exit(2)
    elif opt == "-n":
      n = arg
  if n == '':
    print('app.py -n <population size>')
    sys.exit(2)
  return n

n = ''
if __name__ == "__main__":
  n = main(sys.argv[1:])
else:
  print("This file should not be imported. Please run from the command line.")
  sys.exit(2)

print("\n-- COVID-19 EPIDEMIC SIMULATION --\n")
# n is set, config is set to name of census_data file
population = population.generate(int(n))