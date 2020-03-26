#!/usr/bin/python

import sys, getopt
import json

import population
import epidemic

def import_json(filename):
  with open(filename, 'r') as f:
    return json.load(f)

def main(argv):
  n = ''
  config_file = ''
  try:
    opts, args = getopt.getopt(argv,"hn:c:",['help','pop_size=','config='])
  except getopt.GetoptError:
      print('app.py -n <population size> [-c <config>]')
      sys.exit(2)
  for opt, arg in opts:
    if opt == '-h' or opt == '--help':
      print('app.py -n <population size> [-c <config>]')
      sys.exit(2)
    elif opt == "-n":
      n = arg
    elif opt == "-c" or opt == '--config':
      config_file = arg
  if n == '':
    print('app.py -n <population size> [-c <config>]')
    sys.exit(2)
  if config_file == '':
    config_file = './data/census_data.json'
  return n,config_file

n = ''
config = ''
if __name__ == "__main__":
  n, config = main(sys.argv[1:])
else:
  print("This file should not be imported. Please run from the command line.")
  sys.exit(2)

# n is set, config is set to name of census_data file
census_data = import_json(config)
population = population.generate(n, census_data)