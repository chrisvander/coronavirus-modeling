import csv
import re
import json

with open('census_ests.csv', newline='') as csvfile:
  reader = csv.reader(csvfile)
  header_row = next(reader)
  reg = re.compile("^est72018sex[1,2]_age[0-9]+")
  filtered_headers = list(filter(reg.match, header_row))

with open('census_ests.csv', newline='') as csvfile:
  document = csv.DictReader(csvfile)
  # skip first row
  for row in document:
    break
  # get US totals
  for row in document:
    for h in filtered_headers:
      print(h)
      print(row[h])
    break

file = open("raw_counts.txt", "r")
data = {'male': {}, 'female': {}}
for line in file:
  name,count = line.split(',')
  age = name[2:]
  if name[0] == '1':
    data['male'][age] = int(count)
  elif name[0] == '2':
    data['female'][age] = int(count)

print(json.dumps(data).replace("plus", "+").replace("to", "-").replace("\"999\"", "\"total\""))

file.close()