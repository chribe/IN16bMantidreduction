#!/usr/bin/env python

# nxs_log.py
# Based on nxs_log by from Jacques Ollivier <ollivier@ill.fr> version 2020.01,27
# extended by Markus Appel with external YAML configuration file for flexible formatting

# Make a logbook without using Mantid
# Save optionally in .csv file
"""

# all runs of  this experiment:
 ./nxs_log.py

# From a given run of this experiment:
 ./nxs_log.py  95084

# Selected runs of this experiment:
 ./nxs_log.py  95060 95084


# all numbers  of a given experiment:
 ./nxs_log.py 183 in4 exp_TEST-2897

# From number xxx of a given experiment:
./nxs_log.py 183 in4 exp_TEST-2897  95084

# a selection of tum numbers of a given experiment:
./nxs_log.py 183 in4 exp_TEST-2897 95060 95084

or called from a shell alias:

nxs_log

nxs_log  95084

nxs_log 183 in4 exp_TEST-2897

etc.

"""

from __future__ import absolute_import, division, print_function

__version__ = "2020.07,11-MA"

# Correct the problem of wrong use of 2.7 pyparsing
# import sys
# try:
#     sys.path.remove("/usr/local/lib/python2.7/dist-packages")
# except:
#     pass

import argparse
import glob
import h5py
import os.path as ospth
import os
from scipy import constants
import pandas as pd
import yaml
import sys


def numors_in(directory):
    """Helper function: return a list of numors found in directory."""
    numors = list()
    files = glob.glob(path + "*.nxs")
    for fullPath in files:
        filename = os.path.split(fullPath)[1]
        try:
            numor = int(os.path.splitext(filename)[0])
        except ValueError:
            continue
        numors.append(numor)
    return numors


# Set up input argument parser to read the command line
parser = argparse.ArgumentParser(
    description="Print info on experiment's files.")
parser.add_argument("cycle", nargs="?", help="number of the reactor cycle")
parser.add_argument(
    "instrument", nargs="?", help="instrument name in lower case")
parser.add_argument(
    "experiment",
    nargs="?",
    help="experiment identifier, e.g. exp_0-01-2323 or internalUse or '*'",
)

parser.add_argument(
    "--first", "-f", type=int, nargs="?", help="first numor to start with")
parser.add_argument(
    "--last", "-l", type=int, nargs="?", help="last numor to print info")
parser.add_argument(
    "--save", "-s", action="store", nargs='?', const="", default=None, help="Save in .csv file (can give file name optionally)")
parser.add_argument(
    "--columnformat", "-c", help="log column format configuration file in YAML format")

# Parse entries
args = parser.parse_args()

# Determine path of nexus files to read
if (args.cycle is None) or (args.instrument is None) or (args.experiment is None):

    # Decompose the present path
    thispath = ospth.abspath(os.getcwd()).split(os.sep)

    # Find index of the "processed"
    try:
        pos = thispath.index("processed")
        # break
    except ValueError:
        print("ERROR: Path {} is not an experiment path!".format(ospth.abspath(os.getcwd())))
        print("       You need to give a valid cycle instrument and exp_number!\n \
            \n Example: \n \t nxs_log 183 in4 exp_TEST-2897")
        sys.exit(1)

    path = "/".join(thispath[0:pos]) + "/rawdata/"
else:
    path = "/net4/serdon/illdata/{cycle}/{instrument}/{experiment}/rawdata/".format(
        cycle=args.cycle,
        instrument=args.instrument,
        experiment=args.experiment)

# if not ospth.exists(path):
#     parser.error("cannot find path " + path)

# find YAML configuration file
confFile = args.columnformat

if not confFile:
    # try if 'nxs_log.yml' exists in current directory
    if os.path.exists("nxs_log.yml"):
        confFile = "nxs_log.yml"
    else:
        confFile = os.path.join( os.path.dirname(os.path.realpath(__file__)), "nxs_log.yml" )


# Read YAML log format configuration
with open(confFile, 'r') as stream:
    conf = yaml.safe_load(stream)

# add value list to configuration structure
for col in conf['columns']:
    col['values'] = [];

# see which numors are available
numors = numors_in(path)
if not numors:
    print("No numors found in rawdata")
    sys.exit()

firstRun = min([n for n in numors if n > 100])
lastRun = max(numors)

# apply user defined min/max run numbers
if args.first:
    firstRun = args.first

if args.last:
    lastRun = args.last

print("Reading from {} to {}".format(firstRun,lastRun))

# print title line
titles = [ col['titleFormat'].format(col['title']) for col in conf['columns'] ]
print( " ".join(titles) )


# go through all numors and collect data
for i in range(firstRun, lastRun + 1):
    filename = glob.glob( path + "{:06}".format(i) + ".nxs" )
    if not filename or not os.path.exists(filename[0]):
        # Ignore gaps in the numor range.
        continue

    try:
        with h5py.File(filename[0], "r") as h5:
            thisline = []
            # loop over log columns
            for col in conf['columns']:
                try:
                    idx = col.get('h5index',0)
                    thisvalue = h5.get(col['h5path'])[idx]
                except Exception as e:
                    print( "ERROR while reading from '{}' of numor {}".format(col['h5path'],i) )
                    print (e)
                    thisvalue = "???"
    
                # apply custom transformation
                if "expression" in col:
                    thisvalue = eval( col['expression'], {}, {"x": thisvalue} )
    
                # format the result
                try:
                    thisvalue = col['format'].format(thisvalue)
                except Exception as e:
                    print( "ERROR while formatting column '{}' of numor {} with value '{}'".format(col['title'],i,thisvalue) )
                    thisvalue = "???"
    
                # append to the value list
                col['values'].append( thisvalue )
    
                # append to the current line of output
                thisline.append( thisvalue )
    
            # print current log line
            print( " ".join(thisline) )
    except IOError:
        continue


if args.save is not None:
    # Preparing dat for a pandas object: a dict
    df = pd.DataFrame( data={ col['title']: col['values'] for col in conf['columns'] } )

    # Set then column order
    df = df[[ col['title'] for col in conf['columns'] ]]

    csvfile = args.save
    if not csvfile:
        csvfile = "log_" + str(firstRun) + "_" + str(lastRun) + ".csv"
    # Save in csv file
    df.to_csv(
        csvfile,
        encoding="utf-8",
        index=False,
    )

# - - - - -
