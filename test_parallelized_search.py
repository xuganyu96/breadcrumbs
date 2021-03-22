from backtracker.search import parallelized_search
from backtracker.examples import NQueens

if __name__ == "__main__":
    empty = NQueens(6, tuple())
    solutions = parallelized_search(empty)
    print(solutions)
