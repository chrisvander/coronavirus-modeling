import networkx as nx
import random

# the chance you'll interact with a given person at a location
# if you are both there at the same time
# this is a face-to-face interaction, less than 6 feet
percent_interaction=.6

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
  potential_interactions = {}
  interactions = []
  for person1 in G.nodes():
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
            if random.random() < percent_interaction:
              # we have an interaction!
              interactions.append((person1, person2, random.choice(overlap), edge['acttype']))
  # sorted interactions by timestep
  return sorted(interactions, key=lambda el: el[2])