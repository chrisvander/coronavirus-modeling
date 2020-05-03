# Coronavirus Modeling
Final Project for Graph Mining, utilizing Python 3 and NetworkX.

Clone the project or otherwise pull down. Run by using `python epidemic.py`. There are different command line flags to help you out. Check `python epidemic.py --help` for more.

Recommended use case is to build a graph via `python epidemic.py -o data/graph.txt` and then import it multiple times later with `python epidemic.py -i data/graph.txt`.

Note that this application will download and parse a lot of information from the NHTS and the U.S. Census at the beginning. This information will be cached for future runs of the app.

# Installation
Clone the repository and `cd` into the root directory. Then, run 
```pip install -r requirements.txt```