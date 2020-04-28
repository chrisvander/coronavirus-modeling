import networkx as nx
import random
from tqdm import tqdm

'''
Responsible for converting the environment interaction graph 
into a peer-to-peer interaction graph.

We know where each actor is at particular timesteps - now we just
use probabilities and some assumptions to create a graph of 
interactions not dependent on the location.

This is built under the assumption that every day, an urban actor
follows the same routine unless modified by way of social
distancing, remote work, or anything else.

One edge indicates an urban actor is at a particular location.

generate_interactions generates ALL possible interactions

'''
def calculate_overlap(times1, times2):
  range1 = range(times1[0], times1[1])
  range2 = range(times2[0], times2[1])
  xs = set(range1)
  overlap = xs.intersection(range2)
  return list(overlap)

def convert_times(edgedata):
  starttime = edgedata['starttime']
  duration = edgedata['endtime'] - starttime
  # in case of interactions at midnight
  if duration < 0:
    duration = duration + 2400
  endtime = starttime + duration
  return starttime,endtime,duration

'''
Where G is an generated graph from epidemic.generate_graph
'''
def generate_interactions(G):
  interactions = []
  for person1 in tqdm(G.nodes()):
    if (str(person1).startswith('P_')):
      locations = [n for n in G.neighbors(person1)]
      for loc in locations:
        edge = G[person1][loc][0]
        p_data = convert_times(edge)
        people_at_loc = [n for n in G.neighbors(loc) if n is not person1]
        for person2 in people_at_loc:
          p2_data = convert_times(G[person2][loc][0])
          overlap = calculate_overlap(p_data, p2_data)
          if len(overlap) > 0:
            # we have a possible interaction!
            interactions.append((person1, person2, overlap, edge['acttype']))
  return interactions

def sample_interactions(sim, interactions, percent, distancing_protocol):
  # we randomly sample a number of interactions
  # after those are sampled, we choose times 
  # that each interaction will occur based on the overlap.
  def choose_overlap(element):
    return (element[0], element[1], random.choice(element[2]), element[3])

  states = nx.get_node_attributes(sim.G, 'state')
  sample = []
  removed = 0
  for i in range(len(interactions)):
    n = interactions[i-removed]
    if states[n[0]] == 'Q' \
      or states[n[0]] == 'R' \
      or states[n[0]] == 'D' \
      or states[n[1]] == 'Q' \
      or states[n[1]] == 'R' \
      or states[n[1]] == 'D':
      interactions.remove(n)
      removed += 1
      continue
    elif random.random() < percent:
      if distancing_protocol['enable_after_confirmed']:
        if sim.confirmed > 0:
          if distancing_protocol[n[3]] > random.random():
            sample.append(n)
        else:
          sample.append(n)
      elif distancing_protocol[n[3]] > random.random():
        sample.append(n)
      

  return sorted(list(map(choose_overlap, sample)), key=lambda el: el[2])




