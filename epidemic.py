import argparse
import networkx as nx
from actors import SyntheticHousehold, SyntheticPerson, generate_synthetic
from util.webapi import cache
from interaction import generate_interactions, sample_interactions
import random
from tqdm import tqdm
import numpy as np
from scipy.stats import norm
import pprint

'''
    activity types include
    (H)ome, (W)ork, (S)hop, s(C)hool, and (O)ther
'''

default_config = {
    'infection_on_interaction': 0.8,
    'social_distancing_infection_rate': 0.08,
    'social_distancing': False,
    'percent_interaction': 0.3,  # if two people are at a location, how likely is it they'll interact
    'test_rate': 0.06,  # percent of people that get tested after showing symptoms
    'death_ratio_gender': {
        '1': 0.62,  # male
        '2': 0.38  # female
    },
    'deaths_by_age': {  # if you have covid, what's the chance you'll die?
        80: .148,  # 80+
        70: .08,  # 70-79
        60: .036,  # etc
        50: .013,
        40: .004,
        30: .002,
        20: .002,
        10: .002,
        0: 0.0001,
    },
    'distancing': {  # percent of activities occurring
        'H': 1, # percent of activities within the household occurring
        'W': 0.3, # percent of activities at work (30% essential)
        'S': 0, # percent of activities at shopping areas
        'C': 0, # percent of activities at school
        'O': 0.02, # percent of other activities
        'enable_after_confirmed': True  # enables only after first detected "quarantined" case
    },
    'days': 1000
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

    def will_die(self, age, gender):
        multiplier = self.config['death_ratio_gender'][gender] * 2
        for k in self.config['deaths_by_age'].keys():
            if int(age) > int(k):
                break
        return random.random() < (self.config['deaths_by_age'][int(k)] * multiplier)

    def get_infection_on_interaction(self):
        if self.config['social_distancing']:
            return self.config['infection_on_interaction'] * self.config['social_distancing_infection_rate']
        return self.config['infection_on_interaction']

    def __init__(self, graph, plot, config={}):
        self.config = {**default_config, **config}
        self.G = graph
        self.plot = plot
        self.days = config['days']

        rv = norm(scale=3)
        weights = []
        for i in range(2, 14):
            weights.append(rv.pdf(i - 8))
        self.sampleIncubation = lambda: random.choices(
            list(range(2, 14)), k=1, weights=weights)[0]

        rv = norm(scale=6)
        weights = []
        for i in range(14, 26):
            weights.append(rv.pdf(i - 20))
        self.sampleInfectionLength = lambda: random.choices(
            list(range(14, 26)), k=1, weights=weights)[0]

        self.people = list(filter(lambda n: str(n).startswith('P_'), self.G.nodes()))
        self.confirmed = 0

    def update_state(self, node, state):
        nx.set_node_attributes(self.G, {node: {'state': state}})
        # if they're exposed, we want a timeline until they show symptoms, and estimates
        # on virus length and death
        if state == 'E':
            death = self.will_die(self.get_attr(node, 'age'), self.get_attr(node, 'sex'))
            nx.set_node_attributes(self.G, {node: {
                'incubation': self.sampleIncubation(),
                'time_infected': 0,
                'will_die': death,
                'infection_length': self.sampleInfectionLength(),
            }})
        if state == "I":
            nx.set_node_attributes(self.G, {node: {
                'test_submitted': False,
                'days_since_submitted_test': 0,
                'test_turnaround': random.randint(1, 4)
            }})

    def increment_time(self, node):
        self.G.nodes[node]['time_infected'] += 1

    def get_attr(self, node, attr):
        return self.G.nodes[node][attr]

    def get_attrs(self, node):
        return self.G.nodes[node]

    def set_attr(self, node, attr, val):
        self.G.nodes[node][attr] = val

    def get_state(self, node):
        return self.G.node[node]['state']

    def get_people(self):
        return self.people

    def get_all_states(self):
        attr = nx.get_node_attributes(self.G, 'state')
        nodes = self.get_people()
        return [attr[n] for n in nodes]

    def _run_one_iter(self, interactions):
        '''
        For each interaction in the graph

        acttype can be one of:
        (H)ome, (W)ork, (S)hop, s(C)hool, and (O)ther
        '''
        for n in self.get_people():
            n_attrs = self.get_attrs(n)
            state = self.get_state(n)
            if state is 'E' or state is 'I' or state is 'Q':
                self.increment_time(n)
                if n_attrs['infection_length'] <= n_attrs['time_infected']:
                    if n_attrs['will_die']:
                        self.update_state(n, 'D')
                    else:
                        self.update_state(n, 'R')
            if state == 'E' and \
                    n_attrs['incubation'] == n_attrs['time_infected']:
                self.update_state(n, 'I')
            elif state == 'I':  # determine whether they should quarantine
                if n_attrs['test_submitted']:
                    self.set_attr(n, 'days_since_submitted_test',
                                  n_attrs['days_since_submitted_test'] + 1
                                  )
                    if n_attrs['days_since_submitted_test'] == n_attrs['test_turnaround']:
                        self.update_state(n, 'Q')
                        self.confirmed += 1
                elif random.random() < self.config['test_rate']:
                    self.set_attr(n, 'test_submitted', True)

        # after checking all states, we iterate through interactions
        for u, v, time, acttype in interactions:
            u_state = self.get_state(u)
            v_state = self.get_state(v)

            # if one is susceptible, then we may want to infect
            if u_state != 'S' and v_state != 'S':
                continue

            if random.random() < self.get_infection_on_interaction():
                if u_state == 'I' and v_state == 'S':
                    self.update_state(v, 'E')
                elif u_state == 'S' and v_state == 'I':
                    self.update_state(u, 'E')

    def run_full_simulation(self, days, totalPeople):
        # Sort edges of graph by timestep

        potential_interactions = generate_interactions(self.G)
        finished = False
        infected = []
        recovered = []
        dead = []
        for day in range(days):
            states = np.array(self.get_all_states())
            interactions = sample_interactions(
                self,
                potential_interactions,
                self.config['percent_interaction'],
                self.config['distancing'])
            print(f"Day {day + 1}\t" +
                  f"S: {(states == 'S').sum()}" +
                  f"\tE: {(states == 'E').sum()}" +
                  f"\tI: {(states == 'I').sum()}" +
                  f"\tQ: {(states == 'Q').sum()}" +
                  f"\tR: {(states == 'R').sum()}" +
                  f"\tD: {(states == 'D').sum()}")
            infected.append((states == 'E').sum() + (states == 'I').sum() + (states == 'Q').sum())
            recovered.append((states == 'R').sum())
            dead.append((states == 'D').sum())
            if ((states == 'E').sum() + (states == 'I').sum() + (states == 'Q').sum()) == 0:
                finished = True
                break
            self._run_one_iter(interactions)

        states = np.array(self.get_all_states())
        if finished:
            D = (states == 'D').sum()
            R = (states == 'R').sum()
            S = (states == 'S').sum()
            print('\nSummary:')
            print(f'\tDays to End: \t\t{day}')
            print(f'\tPeak Infections: \t{max(infected)}')
            print(f'\tInfected Death Rate: \t{(D/(R+D)) * 100:.2f}%')
            print(f'\tPop Death Rate: \t{(D/totalPeople) * 100:.2f}%')
            print(f'\tRecovery Rate: \t\t{(R/(R+D)) * 100:.2f}%')
            print(f'\tUninfected: \t\t{(S/totalPeople) * 100:.2f}%')

            if self.plot:
                import matplotlib.pyplot as plt
                days = list(range(day + 1))
                plt.plot(days, infected, days, recovered, days, dead)
                plt.legend(['Infected', 'Recovered', 'Dead'])
                plt.ylabel('Number of People')
                plt.xlabel('Days')
                plt.show()
        else:
            print(f'Did not remove COVID-19 in {days} days')

    def run(self):
        print('\n-- EPIDEMIC SIMULATION --')
        print("Config:")
        pprint.pprint(self.config)
        nx.set_node_attributes(self.G, 'S', 'state')
        nx.set_node_attributes(self.G, 0, 'time_infected')

        if self.config['social_distancing']:
            print("\nSOCIAL DISTANCING ENABLED. Infection rate multipler = " + str(self.config['social_distancing_infection_rate']))

        total = len(self.get_people())
        # infect the first person
        patient_zero = random.choice(self.get_people())
        self.update_state(patient_zero, 'E')
        self.update_state(patient_zero, 'I')

        print(f'\nGenerating daily routines...')
        self.run_full_simulation(self.days, total)


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
    argparser.add_argument('--graph-in', '-i', dest='graph_in', 
        help='import a previously-generated synthetic population')
    argparser.add_argument('--graph-out', '-o', dest='graph_out',
        help='export the to-be-generated synthetic population to a file')
    argparser.add_argument('--population-size', '-n', dest='n', type=int, default=1000,
        help='the size of the population')
    argparser.add_argument(
        '--social-distancing',
        '-s',
        dest='sd',
        action='store_true',
        help='enable social distancing',
        default=False)
    argparser.add_argument('--test-rate', '-t', dest='t', type=float, default=0.05,
        help='the percent of the population who can get access to a test if they are infected')
    argparser.add_argument('--plot', '-p', dest='p', action='store_true', default=False,
        help='use matplotlib to plot the final data')
    argparser.add_argument('--max-days', dest='maxdays', type=int, default=1000,
        help='the max number of days for the simulation to last')
    argparser.add_argument('--sd-infection-rate', '-sr', dest='sdrate', type=float, default=0.08,
        help='with social distancing enabled, this is the multiplier for infection rate')
    argparser.add_argument('--infection-rate', '-ir', dest='ir', type=float, default=0.8,
        help='rate of infection upon interaction (w/o mask or distancing)')
    argparser.add_argument('--percent-interaction', '-pi', dest='pi', type=float, default=0.3,
        help='chance of interaction if two people are at the same location')
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
    sim = EpidemicSim(G, args.p, {
        'infection_on_interaction': args.ir,
        'percent_interaction': args.pi,
        'social_distancing_infection_rate': args.sdrate,
        'social_distancing': args.sd,
        'test_rate': args.t,
        'days': args.maxdays
    })
    sim.run()
    
