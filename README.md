# Coronavirus Modeling
Final Project for Graph Mining, utilizing Python 3 and NetworkX.

Clone the project or otherwise pull down. Run by using `python epidemic.py`. There are different command line flags to help you out. Check `python epidemic.py --help` for more.

Recommended use case is to build a graph via `python epidemic.py -o data/graph.txt` and then import it multiple times later with `python epidemic.py -i data/graph.txt`.

Note that this application will download and parse a lot of information from the NHTS and the U.S. Census at the beginning. This information will be cached for future runs of the app.

# Installation
Clone the repository and `cd` into the root directory. To download all dependencies, run: 
```
pip3 install -r requirements.txt
``` 

Note that this depends on an active Python 3 installation on your computer.

# Running
```
# View all parameters
python epidemic.py --help
# Save a population with 1000 people
python epidemic.py -n 1000 -o data/graph.txt
# Run a simulation using the previous graph as input
python epidemic.py -i data/graph.txt
# Enact social distancing
python epidemic.py -i data/graph.txt --social-distancing
# Decrease infectivity on social distancing to 5%
python epidemic.py -i data/graph.txt --social-distancing -sr 0.05
# Change percent infection on interaction to 75%
python epidemic.py -i data/graph.txt -pi .75
# Plot the result
python epidemic.py -i data/graph.txt --plot
```
