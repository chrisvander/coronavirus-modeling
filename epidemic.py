import argparse
import networkx as nx
from actors import SyntheticHousehold, SyntheticPerson, generate_synthetic
from util.webapi import cache
from interaction import generate_interactions
import random

infection_on_interaction=.8

class EpidemicSim:
    '''
    This simulator is an extension of the actor-based SEIQRD epidemic model. It simulates
    the diffusion of a disease through an interaction network. For more info, see:
        https://en.wikipedia.org/wiki/Compartmental_models_in_epidemiology#The_SEIR_model

    We will use the following state graph to determine stages of disease in an individual.

            +----------------------------------------------------->
            |              +-------------------------------------->
            |              |           +--------------------------> Recovered
            |              |           |                       +-->
            |              |           |                       |
        Susceptible --> Exposed --> Infected --> Quarantined --+
                                       |                       |
                                       |                       +-->
                                       +--------------------------> Dead

    (S), (E), (I), (Q), (R), (D)

    Incubation time:
        After someone is exposedDiseased typically take between several hours and
        several days before a person begins to show symptoms. Here's some useful info:
            https://www.worldometers.info/coronavirus/coronavirus-incubation-period/

        You can simply use a random normal distribution. You can pick whatever mean
        and standard deviation, though the mean incubation period is 3-6 days and
        range is roughly 2-14 days. Resample if the sample point is too
        large/small.

    Death/recovery rate:
        There are are two statistically significant factors which can affect
        the death/recovery rate in people:
            - age:  "Older" people, and people with underlying conditions have statistically
                    statistically higher death rates than "younger" people
            - sex: Males have a statistically higher death rate.

        You could simply make a lookup table of the death rate using data from:
            https://www.worldometers.info/coronavirus/coronavirus-age-sex-demographics/

    Interaction chance:
        This is the probability that any two people will interact in a given location.
        This can simply be a constant, or it can proportional to the amount of time the two
        individuals have spent at the location together.
    '''

    def __init__(self):
        pass

    def get_people(self, G):
        return list(filter(lambda n : str(n).startswith('P_'), G.nodes()))

    def _run_one_iter(self, interactions):
        '''
        For each interaction in the graph

        acttype can be one of:
        (H)ome, (W)ork, (S)hop, s(C)hool, and (O)ther
        '''
        for u,v,time,acttype in interactions:
            pass
        pass

    def run_full_simulation(self, days):
        # Sort edges of graph by timestep
        for day in range(days):
            print(f"Day {day + 1}:")
            self._run_one_iter(generate_interactions(G))

    def run(self, G):
        print('\n-- EPIDEMIC SIMULATION --')
        nx.set_node_attributes(G, 'S', 'state')
        p_zero = random.choice(self.get_people(G))
        nx.set_node_attributes(G, { p_zero: {'state': 'I'}})
        print('Selected Patient Zero')

        days = 35
        print(f'\nSimulating {days} days')
        self.run_full_simulation(days)



def generate_graph(synth_hhs):
    '''
    Generate an undirected, multi-edge, bipartite graph using nx.MultiGraph().
    '''
    G = nx.MultiGraph()
    for syn_hh in synth_hhs:
        for person in syn_hh.people:
            for activity in person.activities:
                if not G.has_node(person.uid):
                    G.add_node(person.uid, **person.attr_dict())

                act_loc = activity.location
                if not G.has_node(act_loc.uid):
                    G.add_node(act_loc.uid, **act_loc.attr_dict())

                G.add_edge(person.uid, act_loc.uid, **activity.attr_dict())

    return G


def parse_args(argv=None):
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--graph-in', dest='graph_in')
    argparser.add_argument('--graph-out', dest='graph_out')
    argparser.add_argument('--population-size', '-n', dest='n', default=10000)
    # Simulation arguments
    return argparser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()

    G = None
    if args.graph_in:
        G = nx.read_gml(args.graph_in)
    else:
        synth_hhs = generate_synthetic(int(args.n))

        print("Generating environment interaction graph.")
        G = generate_graph(synth_hhs)

        if args.graph_out:
            print(f"Writing generated graph to {args.graph_out}")
            nx.write_gml(G, args.graph_out)

    # Run simulation
    sim = EpidemicSim()
    sim.run(G)
