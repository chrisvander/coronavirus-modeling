import argparse
import networkx as nx
from actors import SyntheticHousehold, SyntheticPerson, generate_synthetic
from util.webapi import cache


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

    def __init__(self, G):
        self.G = G
        pass

    def _run_one_iter(self):
        '''
        For each person in the graph
        '''
        pass

    def run_full_simulation(self, days):
        # Sort edges of graph by timestep
        for day in range(days):
            self._run_one_iter()

    def run(self):
        print('\n-- EPIDEMIC SIMULATION --')


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
        synth_hhs = cache('synthetic_pop_' + str(args.n),
                          lambda: generate_synthetic(args.n))

        print("Generating graph.")
        G = generate_graph(synth_hhs)

        if args.graph_out:
            print(f"Writing generated graph to {args.graph_out}")
            nx.write_gml(G, args.graph_out)

    # Run simulation
    sim = EpidemicSim(G)
    sim.run()
