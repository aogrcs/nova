""" The MIT License (MIT)

    Copyright (c) 2015 Kyle Hollins Wray, University of Massachusetts

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to
    use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
    the Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
    FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
    COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
    IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
    CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import sys

thisFilePath = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(thisFilePath, "..", "..", "..", "..", "python"))
from nova.pomdp import *

from pylab import *


horizon = 50
numTrials = 10

fixedAlgorithm = 'pbvi'
processes = ['gpu', 'cpu']

files = [
        {'name': "tiger", 'filename': "domains/tiger_95.pomdp", 'filetype': "cassandra", 'numExpandSteps': 4},
        #{'name': "shuttle", 'filename': "domains/shuttle_95.pomdp", 'filetype': "cassandra", 'numExpandSteps': 4},
        #{'name': "paint", 'filename': "domains/paint_95.pomdp", 'filetype': "cassandra", 'numExpandSteps': 4},
        #{'name': "grid-4x3", 'filename': "domains/4x3_95.pomdp", 'filetype': "cassandra", 'numExpandSteps': 5},
        #{'name': "tiger-grid", 'filename': "domains/tiger_grid.pomdp", 'filetype': "cassandra",'numExpandSteps': 6},
        #{'name': "aloha-10", 'filename': "domains/aloha_10.pomdp", 'filetype': "cassandra", 'numExpandSteps': 6},
        #{'name': "hallway2", 'filename': "domains/hallway2.pomdp", 'filetype': "cassandra", 'numExpandSteps': 7},
        #{'name': "aloha-30", 'filename': "domains/aloha_30.pomdp", 'filetype': "cassandra", 'numExpandSteps': 7},
        #{'name': "tag", 'filename': "domains/tag.pomdp", 'filetype': "cassandra", 'numExpandSteps': 8},
        #{'name': "fourth", 'filename': "domains/fourth.pomdp", 'filetype': "cassandra", 'numExpandSteps': 8},
        #{'name': "rock-sample (7x8)", 'filename': "domains/rockSample_7_8.pomdp", 'filetype': "cassandra", 'numExpandSteps': 9},
        #{'name': "auv-navigation", 'filename': "domains/auvNavigation.pomdp", 'filetype': "cassandra", 'numExpandSteps': 10},

        #{'name': "drive_san_francisco", 'filename': "domains/drive_san_francisco.pomdp", 'filetype': "cassandra", 'numExpandSteps': 8},
        #{'name': "drive_seattle", 'filename': "domains/drive_seattle.pomdp", 'filetype': "cassandra", 'numExpandSteps': 9},
        #{'name': "drive_new_york_city", 'filename': "domains/drive_new_york_city.pomdp", 'filetype': "cassandra", 'numExpandSteps': 9},
        #{'name': "drive_boston", 'filename': "domains/drive_boston.pomdp", 'filetype': "cassandra", 'numExpandSteps': 10},
        ]


for f in files:
    print(f['name'])

    filename = os.path.join(thisFilePath, f['filename'])

    for p in processes:
        print(" - %s " % (p), end='')

        fileSuffix = "_".join([f['name'], p])

        with open(os.path.join(thisFilePath, "results", fileSuffix) + ".csv", "w") as out:
            out.write("n,m,z,r,ns,rz,time,V(b0)\n")

            for j in range(numTrials):
                print(".", end='')
                sys.stdout.flush()

                pomdp = POMDP()
                pomdp.load(filename, filetype=f['filetype'])
                pomdp.horizon = int(horizon)

                # Store the intial belief from this file.
                rzOriginal = pomdp.rz
                b0 = [pomdp.B[0 * pomdp.rz + k] for k in range(pomdp.rz)]
                z0 = [pomdp.Z[0 * pomdp.rz + k] for k in range(pomdp.rz)]

                # Do expansions using random exploration. This lets us control the exact number of beliefs for
                # CPU vs GPU. Note: The number of beliefs is likely to be way too small for random exploration.
                # This is just to get a sense of the speed, not the optimal value. Also, the horizon is much
                # too small for the larger domains.
                pomdp.expand(method='random', numBeliefsToAdd=(pow(2, f['numExpandSteps']) - 1))

                Gamma, piResult, timing = pomdp.solve(process=p, algorithm=fixedAlgorithm)

                #print(pomdp)
                #print(Gamma)
                #print(piResult)

                # Compute the value of the initial belief.
                Vb0 = pomdp.Rmin / (1.0 - pomdp.gamma)
                for q in range(Gamma.shape[0]):
                    Vb0q = 0.0

                    for k in range(rzOriginal):
                        s = z0[k]
                        if s < 0:
                            break
                        Vb0q += b0[k] * Gamma[q, s]

                    if Vb0 < Vb0q:
                        Vb0 = Vb0q

                # Note: use the time.time() function, which measures wall-clock time.
                out.write("%i,%i,%i,%i,%i,%i,%.5f,%.5f\n" % (pomdp.n, pomdp.m, pomdp.z, pomdp.r, pomdp.ns, pomdp.rz,
                                                            timing[0], Vb0))

        print()

