import argparse
import networkx as nx
from actors import SyntheticHousehold, SyntheticPerson


class EpidemicSim:
    '''
    This simulator is an extension of the actor-based SEIRD epidemic model. It simulates
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

    def __init__(self):
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


def generate_digraph(synth_hhs):
    '''
    This function will generate an undirected, multi-edge, bipartite graph using
    nx.MultiGraph().
    '''

    '''
    First, we generate a probability matrix to represent the transition between
    activity locations. There are 4 anchor activity types: H (home), W (work),
    S (shop), C (school).

    Each index i, j in the matrix will represent a probability proportional to:
        P(j|i) = A_aj * e^(b_w * D_ij)
    where:
        A_aj:   Attractiveness of location j for destination activity a.
                Either 0 or 1. This is essentially a boolean mask (b/c you don't go
                shopping at home a home location or to school at a work location).
        e_b:    Calibration constant.
        D_ij:   distance between locations i and j
    '''

    for syn_hh in synth_hhs:
        for person in syn_hh.people:
            for activity in person.activities:
                '''
                If the person doesn't already exist in the graph, create a person
                node / vertex in the following way:
                    - Create attr_dict for node: {age, hh_size, gender, income}
                    - Use nx.Graph.add_node(n, attr_dict)

                If the location doesn't already exist in the graph, create a
                location node / verted in the following way:
                    - Create attr_dict for node: {business_type}
                    - Use nx.Graph.add_node(n, attr_dict)
                '''
                # Location is determined using the formula:
                # Generate some
                # Create an edge between the person and location
                pass


def parse_args(argv=None):
    argparser = argparse.ArgumentParser()
    # Graph-builer arguments
    # Simulation arguments
    return argparser.parse_args(argv)


if __name__ == "__main__":
    # Generate/load urban actor data
    synth_hhs = None

    # Create graph
    g = generate_digraph(synth_hhs)

    # Run simulation
    sim = EpidemicSim()
    sim.run()
