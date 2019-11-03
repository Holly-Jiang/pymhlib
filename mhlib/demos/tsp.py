"""Demo application solving the symmetric traveling salesman problem.

Given n cities and a symmetric distance matrix for all city pairs, find a shortest round trip through all cities.
"""

import random
import numpy as np
import math

from mhlib.permutation_solution import PermutationSolution


class TSPInstance:
    """An instance of the traveling salesman problem.

    This instance contains the distances between all city pairs.
    Starting from a solution in which the cities are visited in the order they are defined in the instance file,
    a local search in a 2-opt neighborhood using edge exchange is performed.

    Attributes
        - n: number of cities, i.e., size of incidence vector
        - distances: square matrix of integers representing the distances between two cities;
            zero means there is not connection between the two cities
    """

    def __init__(self, file_name: str):
        """Read an instance from the specified file."""
        coordinates = {}
        dimension = None

        with open(file_name, "r") as f:
            for line in f:
                if line.startswith("NAME") or line.startswith("COMMENT") or line.startswith("NODE_COORD_SECTION"):
                    pass
                elif line.startswith("EOF"):
                    break
                elif line.startswith("TYPE"):
                    assert (line.split()[-1] == "TSP")
                elif line.startswith("EDGE_WEIGHT_TYPE"):
                    assert (line.split()[-1] == "EUC_2D")
                elif line.startswith("DIMENSION"):
                    dimension = int(line.split()[-1])
                else:
                    split_line = line.split()
                    num = int(split_line[0]) - 1  # starts at 1
                    x = int(split_line[1])
                    y = int(split_line[2])

                    coordinates[num] = (x, y)

        assert (len(coordinates) == dimension)

        # building adjacency matrix
        distances = np.zeros((dimension, dimension))

        for i in range(0, dimension):
            for j in range(i + 1, dimension):
                x1, y1 = coordinates[i]
                x2, y2 = coordinates[j]
                dist = math.sqrt(math.pow(x2 - x1, 2) + math.pow(y2 - y1, 2))
                distances[i][j] = distances[j][i] = int(dist)

        self.distances = distances
        self.n = dimension

        # make basic check if instance is meaningful
        if not 1 <= self.n <= 1000000:
            raise ValueError(f"Invalid n: {self.n}")

    def __repr__(self):
        """Write out the instance data."""
        return f"n={self.n},\ndistances={self.distances!r}\n"


class TSPSolution(PermutationSolution):
    """Solution to a TSP instance.

    Attributes
        - inst: associated TSPInstance
        - x: order in which cities are visited, i.e., a permutation of 0,...,n-1
    """

    to_maximize = False

    def __init__(self, inst: TSPInstance):
        super().__init__(inst.n, inst=inst)
        self.obj_val_valid = False

    def copy(self):
        sol = TSPSolution(self.inst)
        sol.copy_from(self)
        return sol

    def calc_objective(self):
        distance = 0
        for i in range(self.inst.n - 1):
            distance += self.inst.distances[self.x[i]][self.x[i + 1]]
        distance += self.inst.distances[self.x[-1]][self.x[0]]
        return distance

    def check(self):
        """Check if valid solution.

        :raises ValueError: if problem detected.
        """
        if len(self.x) != self.inst.n:
            raise ValueError("Invalid length of solution")
        super().check()

    def construct(self, par, _result):
        """Scheduler method that constructs a new solution.

        Here we just call initialize.
        """
        self.initialize(par)

    def shaking(self, par, result):
        """Scheduler method that performs shaking by 'par'-times swapping a pair of randomly chosen cities."""
        for _ in range(par):
            a = random.randint(0, self.inst.n - 1)
            b = random.randint(0, self.inst.n - 1)
            self.x[a], self.x[b] = self.x[b], self.x[a]
        self.invalidate()
        result.changed = True

    def local_improve(self, _par, _result):
        self.two_opt_neighborhood_search(True)

    def two_opt_move_delta_eval(self, p1: int, p2: int) -> int:
        """ This method performs the delta evaluation for inverting self.x from position p1 to position p2.

        The function returns the difference in the objective function if the move would be performed,
        the solution, however, is not changed.
        """
        assert (p1 < p2)
        n = len(self.x)
        if p1 == 0 and p2 == n - 1:
            # reversing the whole solution has no effect
            return 0
        prev = (p1 - 1) % n
        nxt = (p2 + 1) % n
        x_p1 = self.x[p1]
        x_p2 = self.x[p2]
        x_prev = self.x[prev]
        x_next = self.x[nxt]
        d = self.inst.distances
        delta = d[x_prev][x_p2] + d[x_p1][x_next] - d[x_prev][x_p1] - d[x_p2][x_next]
        return delta

    # TODO implement the following two methods methods relevant for SA also for all other demo problems
    def propose_neighborhood_move(self):
        """This method returns a tuple (move, delta_f) to be used for SA."""
        return self.propose_random_2_opt_move()

    def apply_neighborhood_move(self, move):
        """This method applies a given neighborhood move accepted by SA."""
        self.apply_2_opt_move(move)

    def propose_random_2_opt_move(self):
        """Propose random move in 2-opt neighborhood by returning (move, delta_f)"""
        p1 = random.randint(0, len(self.x)-2)
        p2 = random.randint(p1+1, len(self.x)-1)
        move = (p1, p2)
        delta_f = self.two_opt_move_delta_eval(*move)
        return move, delta_f

    def apply_2_opt_move(self, move):
        p1 = move[0]
        p2 = move[1]
        self.x[p1:(p2 + 1)] = self.x[p1:(p2 + 1)][::-1]

    def crossover(self, other: 'TSPSolution') -> 'TSPSolution':
        """Perform edge recombination."""
        return self.edge_recombination(other)


if __name__ == '__main__':
    from mhlib.demos.common import run_optimization, data_dir
    from mhlib.settings import get_settings_parser
    parser = get_settings_parser()
    run_optimization('TSP', TSPInstance, TSPSolution, data_dir + "xqf131.tsp")
