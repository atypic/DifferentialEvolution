__author__ = 'odd rune'

import sys
sys.path.append('/Users/oddrune/mecobo/Thrift interface/gen-py/NascenseAPI_v01e')
import emEvolvableMotherboard

from ttypes import *
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol


from DifferentialEvolution import DifferentialEvolution
from collections import defaultdict
import random
import uuid

SEED = 42
NODES = 8
random.seed(SEED)

allFreqs = sorted(set([int(37500000.0/i) for i in xrange(1,65535)]))
#allCycles = [0, 25, 50, 75, 100]
#cycleIndices = range(0, len(allCycles)-1, 1)
freqIndices = range(0,len(allFreqs)-1,1)

class Individual:
    name = ""
    inputPin1 = -1
    inputPin2 = -1
    outputPin = -1
    #pinFrequencies = {}
    fitness = -1.0

    def __init__(self, in1=None, in2=None, out=None):
        self.name = str(uuid.uuid4())



        availableNodes = range(0, NODES)
        if in1 == None:
            self.inputPin1 = random.choice(availableNodes)
            availableNodes.remove(self.inputPin1)
            self.inputPin2 = random.choice(availableNodes)
            availableNodes.remove(self.inputPin2)
            self.outputPin = random.choice(availableNodes)
            availableNodes.remove(self.outputPin)
        else:
            self.inputPin1 = in1
            self.inputPin2 = in2
            self.outputPin = out
            availableNodes.remove(self.inputPin1)
            availableNodes.remove(self.inputPin2)
            availableNodes.remove(self.outputPin)

        #Initialize this individual with a uniform distribution
        self.pinFrequencyIndex = defaultdict(list)
        for node in availableNodes:
            self.pinFrequencyIndex[node] = random.sample(freqIndices, 1)[0]

        return

    def __str__(self):
        s = "In1: " + str(self.inputPin1) + " In2: " + str(self.inputPin2) + " Out: " + str(self.outputPin) + " | "
        for p in self.pinFrequencyIndex:
            s += str(p) + ": " + str(allFreqs[self.pinFrequencyIndex[p]]) + " "
        s += " Fit: " + str(self.fitness)
        return s


class Xorsearch:
    individuals = []
    inputPin1 = 0
    inputPin2 = 4
    outputPin = 8
    transport = None
    client = None
    hardware = False

    def __init__(self, numInds, in1, in2, out, hardware):
        self.inputPin1 = in1
        self.inputPin2 = in2
        self.outputPin = out

        self.wantedInputOutput = {
            (0,0) : 1,
            (0,1) : 0,
            (1,0) : 0,
            (1,1) : 1 }


        self.hardware = hardware
        if hardware:
            self.transport = TSocket.TSocket('192.168.2.6', 9090)
            self.transport = TTransport.TBufferedTransport(self.transport)

            prot = TBinaryProtocol.TBinaryProtocol(self.transport)
            self.client = emEvolvableMotherboard.Client(prot);
            self.transport.open();
            self.client.ping();


    def fitness(self, agent):
        #Use params + internal Xorsearch-state to setup the search
        if self.hardware:
            m = self.getSamplePointFromBoard(agent.params)
        else:
            m = self.getSamplePoint(agent.params)

        fitness = 0.0
        for k in m:
            correct = m[k].count(self.wantedInputOutput[k])
            fitness += (correct/float(len(m[k])))

        fitness /= len(self.wantedInputOutput)
        print "found fitness: ", fitness
        return fitness

    def getSamplePoint(self, individual):
        """
        This function gives the measured value at the given landscape.
        :param individual: this is a search vector
        :return:
        """
        measurements = {
            (0,0) : [],
            (0,1) : [],
            (1,0) : [],
            (1,1) : []
        }

        #This sets up the board and collects the sample buffers, for now it's just a dummy
        for i in measurements:
            measurements[i].extend([random.sample([0,1],1)[0] for _ in xrange(100)])
        return measurements

    def getSamplePointFromBoard(self, parms):

        measurements = {
            (0,0) : [],
            (0,1) : [],
            (1,0) : [],
            (1,1) : []
        }

        for case in self.wantedInputOutput:
            print "Running case ",  case
            self.client.reset()
            self.client.clearSequences()

            allPins = range(0,NODES)
            allPins.remove(self.outputPin)
            allPins.remove(self.inputPin1)
            allPins.remove(self.inputPin2)
             #Output setup
            rit = emSequenceItem()
            rit.pin = [self.outputPin]
            rit.startTime = 10
            rit.frequency = 10000
            rit.endTime = 110
            rit.waveFormType = emWaveFormType().PWM
            rit.operationType = emSequenceOperationType().RECORD
            self.client.appendSequenceAction(rit)

            it = emSequenceItem()
            it.pin = [self.inputPin1]
            it.frequency = case[0]
            it.cycleTime = 100
            it.startTime = 0
            it.endTime = 100
            it.operationType = emSequenceOperationType().DIGITAL
            self.client.appendSequenceAction(it)

            it = emSequenceItem()
            it.pin = [self.inputPin2]
            it.frequency = case[1]
            it.cycleTime = 100
            it.startTime = 0
            it.endTime = 100
            it.operationType = emSequenceOperationType().DIGITAL
            self.client.appendSequenceAction(it)

            for p,v in zip(allPins, parms):
                it = emSequenceItem()
                it.pin = [p]
                assert int(v) <= len(allFreqs)-1, "Passed value too high: %d, max is %d" % (int(v), len(allFreqs)-1)
                it.frequency = allFreqs[max(0,min(int(v),len(allFreqs)-1))]
                it.cycleTime = 50
                it.startTime = 0
                it.endTime = 100
                it.operationType = emSequenceOperationType().DIGITAL
                self.client.appendSequenceAction(it)

            self.client.runSequences()
            self.client.joinSequences()
            measurements[case].extend(self.client.getRecording(self.outputPin).Samples)

        return measurements

if __name__ == "__main__":
    numInds = 20
    hardware=True
    xor = Xorsearch(numInds, 0, 3, 5, hardware)
    lims = [(0, len(allFreqs)-1) for i in xrange(NODES-3)]
    search = DifferentialEvolution(0.9, 0.9, numInds, NODES-3, lims, xor, 0.9, 50)
    best = search.runOptimization()
    print "Best score: ", best.score, " for ", best.params
