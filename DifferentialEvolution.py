import logging
import random
import numpy as np
import sys


class DifferentialEvolution:
    """
    This is an implementation of the Differential Evolution algorithm.
    The main source for the implementation is from the wikipedia article on DE.

    The "objective" that is taken in is an object that needs to have the function "fitness(Agent)" defined.
    The Agent class is defined in this file as well, and is a class that represents the score and the
    parameters (the search vector) that is being optimized currently.
    """
    def __init__(self,
        F=1.0,                      #F parameter sets scaling factor for differential vectors
        CR=0.5,                     #CR is the probability of setting the new position for an individual to a+F(b-c)
        NP=10,                      #NP is the population size
        D=3,                        #D is the number of dimensions in the problem
        limits=[],                  #Element i provides a tuple (min, max) for the value-range of elm. i in the individual vector. If empty, no limits.
        objective=None,               #Fitness function takes an individual and evaluates it's fitness
        minimumFitness=1.0,         #Termination criteria
        maxIterations=50,           #Stop after this number of iterations
    ):
        self.F = F
        self.CR = CR
        self.NP = NP
        self.D = D
        self.maxIterations = maxIterations
        self.minimumFitness = minimumFitness

        self.scores = {}
        self.population = []*NP

        assert (objective), "Please supply a fitness object"
        self.objective = objective

        #Limits
        if len(limits) > 0:
            assert type(limits) is list, "Limits is not a list!"
            self.limits = limits
        else:
            logging.warning("No limits on elements of individual vectors given. Initializing to (min,max) of python float.")
            #Initialize the limits to min and max of float value.
            for k in xrange(0, D):
                self.limits[k] = (sys.float_info.min, sys.float_info.max)

        self.population = self.initializePopulation(NP, D, self.limits, random.uniform)
        assert len(self.population) == NP, "Initialization produced too few individuals."
        #TODO: Should probably check that each individual is within bounds here and warn if not.


    def initializePopulation(self, n, d, limits, distribution):

        a = np.array([Agent(self.limits) for p in xrange(0,n)])
        return a

    def runOptimization(self):

        assert len(self.population) == self.NP, "Population size different from expected"
        achievedFitness = 0.0
        iterationsRun = 0

        while (achievedFitness < self.minimumFitness) and (iterationsRun < self.maxIterations):
            for x in self.population:

                p = []
                #Make sure we do not draw x -- we don't want degenerate cases
                while len(p) < 3:
                    t = random.choice(self.population)
                    if t is not x:
                        p.append(t)

                a, b,c = p[0], p[1], p[2]
                #Make the new trial vector
                R = random.randint(0, self.D)
                #y = [0]*self.D
                y = Agent(self.limits)
                for i in xrange(0,self.D):
                    #i == R ensures that y will /at least/ have one element from the mutant vector,
                    #so that y != mutant
                    if random.random() < self.CR or i == R:
                        y.params[i] = max(a.lims[i][0], min(a.lims[i][1], a.params[i] + self.F * (b.params[i] - c.params[i])))
                    else:
                        y.params[i] = x.params[i]

                #Evaluate
                y.score = self.objective.fitness(y)
                x.score = self.objective.fitness(x)
                if y.score >= x.score:
                    x = y  #Replace the reference with this new object
                    x.params = self.objective.fitness(y)

                #Find highest score now that we are done.
                maxi = 0.0
                for a in self.population:
                    if a.score > maxi:
                        maxi = a.score

            iterationsRun += 1
            print("%d iterations run out of %d, best fitness %f" % (iterationsRun, self.maxIterations, maxi))

        #Find highest score now that we are done.
        maxi = 0.0
        best = self.population[0]
        for a in self.population:
            if a.score > maxi:
                maxi = a.score
                best = a

        return best


class Agent:
    """
    This class represents an agent in the population, used in the DE.
    """
    params = np.array([])
    lims = []
    score = -1.0
    def __init__(self, limits):
        """Initialize the agent"""
        self.params = np.array([random.uniform(i[0], i[1]) for i in limits])
        self.lims = limits
        self.score = -1.0
        return
