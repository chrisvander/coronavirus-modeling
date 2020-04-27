import argparse
import networkx as nx
from actors import SyntheticHousehold, SyntheticPerson, generate_synthetic
from util.webapi import cache
from interaction import generate_interactions
import random

default_config = {
    'infection_on_interaction': 0.8
}


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

    def __init__(self, graph, config={}):
        self.config = {**default_config, **config}
        self.G = graph

    def update_state(self, node, state):
        nx.set_node_attributes(self.G, {node: {'state': state, 'time_in_state': 0}})

    def get_state(self, node):
        return nx.get_node_attributes(self.G, 'state')[node]

    def get_people(self):
        return list(filter(lambda n: str(n).startswith('P_'), self.G.nodes()))

    def get_all_states(self):
        return list(nx.get_node_attributes(self.G, 'state').values())

    def number_infected(self):
        return len([n for n in self.get_all_states() if n == 'E'])

    def _run_one_iter(self, interactions):
        '''
        For each interaction in the graph

        acttype can be one of:
        (H)ome, (W)ork, (S)hop, s(C)hool, and (O)ther
        '''

        print(f"Number infected {self.number_infected()}")

        # after checking all states, we iterate through interactions
        print(len(interactions))
        for u, v, time, acttype in interactions:
            # if random.random() < self.config['infection_on_interaction']:
            if self.get_state(u) == 'I' and self.get_state(v) == 'S':
                self.update_state(v, 'E')
            elif self.get_state(u) == 'S' and self.get_state(v) == 'I':
                self.update_state(u, 'E')
            if self.get_state(u) == 'I':
                print(self.get_state(u))

    def run_full_simulation(self, days):
        # Sort edges of graph by timestep
        for day in range(days):
            print(f"Day {day + 1}:")
            self._run_one_iter(generate_interactions(self.G))

    def run(self):
        print('\n-- EPIDEMIC SIMULATION --')
        print("Using config " + str(self.config))
        nx.set_node_attributes(self.G, 'S', 'state')
        # infect the first person
        patient_zero = random.choice(self.get_people())
        print(patient_zero)

        self.update_state(patient_zero, 'I')
        print(f"Number infected {self.number_infected()}")
        days = 35
        print(f'\nSimulating {days} days')
        self.run_full_simulation(days)


def generate_graph(synth_hhs):
    '''
    Generate an undirected, multi-edge, bipartite graph using nx.MultiGraph().
    '''
    person_count = 0
    G = nx.MultiGraph()
    for syn_hh in synth_hhs:
        for person in syn_hh.people:

            # Add person to graph
            person_id = f"P_{person_count}"
            G.add_node(person_id, **person.attr_dict())
            person_count += 1

            # Add edge between person and location for each activity
            for activity in person.activities:
                act_loc = activity.location
                loc_id = f"L_{act_loc.id}"

                # Add location to graph
                if not G.has_node(act_loc.id):
                    G.add_node(loc_id, **act_loc.attr_dict())

                G.add_edge(person_id, loc_id, **activity.attr_dict())

    return G


def parse_args(argv=None):
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--graph-in', dest='graph_in')
    argparser.add_argument('--graph-out', dest='graph_out')
    argparser.add_argument('--population-size', '-n', dest='n', type=int, default=10000)
    # Simulation arguments
    return argparser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()

    G = None
    if args.graph_in:
        G = nx.read_gml(args.graph_in)
    else:
        synth_hhs = generate_synthetic(args.n)

        print("Generating environment interaction graph.")
        G = generate_graph(synth_hhs)

        if args.graph_out:
            print(f"Writing generated graph to {args.graph_out}")
            nx.write_gml(G, args.graph_out)

    # Run simulation
    sim = EpidemicSim(G, {
        'infection_on_interaction': 0.7
    })
    sim.run()
