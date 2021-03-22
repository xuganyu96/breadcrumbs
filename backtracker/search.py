from collections import namedtuple
import multiprocessing as mp
import typing as ty
import uuid
from backtracker.backtrackable import Backtrackable


Node = namedtuple("Node", ['depth', 'state'])


def parallelized_search(states,
    max_worker_count: int = 1) -> ty.Set[Backtrackable]:
    """Use multiprocessing to parallelize the search"""
    def worker(wid, backlog: mp.Queue, results: mp.Queue, 
               wsize: mp.Value, wlock: mp.Lock,
               qsize: mp.Value, qlock: mp.Lock):
        """Takes two queues. Receive the state to search from backlog, then 
        put next state into results. Once all "next" states have been put into
        results, acquire the lock on the number of active workers and decrement 
        it before exiting
        """
        current: Node = None
        qlock.acquire()
        try:
            current: Node = backlog.get(timeout=1)
            qsize.value -= 1
        except:
            pass
        finally:
            qlock.release()
        
        if current:
            for next in current.state.next():
                results.put(Node(current.depth+1, next))
        
        wlock.acquire()
        try:
            wsize.value -= 1
        finally:
            wlock.release()

    if isinstance(states, Backtrackable):
        states = [states]
    # Initialize the two queues
    backlog = mp.Queue()
    results = mp.Queue()
    wsize = mp.Value('i', 0) # the number of active workers
    wlock = mp.Lock() # the lock for the number of active workers
    qsize = mp.Value('i', 0) # the number of backlog jobs
    qlock = mp.Lock() # the lock for updating the backlog job number
    footprints: ty.Dict[Backtrackable, bool] = dict()
    solutions: ty.Set[Backtrackable] = set()
    
    # Stuff the backlog with the initial states
    for s in states:
        qlock.acquire()
        try:
            backlog.put(Node(0, s))
            qsize.value += 1
            footprints[s] = True
        finally:
            qlock.release()
    
    while qsize.value > 0 or wsize.value > 0:
        # If backlog is not empty, start assigning workers until the number of 
        # workers reach max capacity
        if not backlog.empty():
            wlock.acquire()
            try:
                wid = str(uuid.uuid4())[:5]
                mp.Process(target=worker, 
                    args=(wid, backlog, results, wsize, wlock, qsize, 
                          qlock)).start()
                wsize.value += 1
            finally:
                wlock.release()
        
        # Harvest the result
        while not results.empty():
            result: Node = results.get()
            if footprints.get(result.state, False):
                continue
            elif result.state.is_solution():
                solutions.add(result.state)
            else:
                qlock.acquire()
                try:
                    backlog.put(result)
                    qsize.value += 1
                    footprints[result.state] = True
                finally:
                    qlock.release()
        print(f"Backlog size: {qsize.value}, footprint size: {len(footprints)}")

    return solutions

def iterative_search(
    states: ty.Union[Backtrackable, ty.Iterable[Backtrackable]],
    dfs: bool = True, max_depth: int = None, n_sols: int = None
    ) -> ty.Set[Backtrackable]:
    """Given a state, search all nodes that can be reached from the given state
    that are solutions

    :param state: the initial set of nodes to start the search from. Can accept 
    a single state or an iterable of states
    :type state: BackTrackable
    :param dfs: if True, search using DFS, otherwise search with BFS. DFS is 
    recommended in most situations
    :param max_depth: the maximal depth of search; if the next node is beyond 
    the maximal depth, it will not be added into the backlog. If none is 
    supplied, the search will go as deep as needed
    :param n_sols: the maximal number of solutions found before the search is 
    terminated. If none is supplied, all solutions will be found.
    :return: A Pythonic set of Backtrackable state instances that are solutions
    according to the user's implementation
    """
    if isinstance(states, Backtrackable):
        states = [states]
    
    # Initialize the backlog with the input states
    backlog = []
    for s in states:
        assert isinstance(s, Backtrackable), \
            f"Expected to search Backtrackable, found {type(s)}"
        backlog.append(Node(0, s))

    footprints: ty.Dict[Backtrackable, bool] = dict()
    solutions: ty.Set[Backtrackable] = set()

    while len(backlog) > 0:
        print(f"Backlog size is {len(backlog)}, footprint size {len(footprints)}")
        current = backlog.pop()

        too_deep = False
        if max_depth:
            # If the current node's depth is at max_depth, then all its children
            # are by definition greater than max_depth and thus not to be 
            # searched
            too_deep = current.depth >= max_depth
        
        if not too_deep:
            # If the current node is already in the footprints, then do not 
            # search; otherwise, add it to the footprints, and obtain all of its
            # immediate neighbors, some being solutions, and others being 
            # next node(s) to search
            for next in current.state.next():
                if next.is_solution() and not next in solutions:
                    solutions.add(next)

                    # If the current solution count has reached the specified
                    # number, terminate search and return solutions
                    early_term = False
                    if n_sols:
                        early_term = len(solutions) >= n_sols
                    if early_term:
                        return solutions
                elif not footprints.get(next, False):
                    if dfs:
                        # If using DFS, then the children of the currently 
                        # searched node will be searched first before other
                        # nodes
                        backlog.append(Node(current.depth+1, next))
                    else:
                        # Otherwise, will use BFS, which means all nodes of 
                        # the same depth will be searched first before their 
                        # children
                        backlog.insert(0, Node(current.depth+1, next))
            footprints[current.state] = True    
    
    return solutions

def recursive_search(state: Backtrackable) -> ty.Set[Backtrackable]:
    """Given a state, search all nodes that can be reached from the given state
    that are solutions

    :param state: [description]
    :type state: Backtrackable
    :return: [description]
    :rtype: ty.Set[Backtrackable]
    """
    if state.is_solution():
        return {state}
    else:
        solutions = set()
        for next in state.next():
            for sub_solution in recursive_search(next):
                solutions.add(sub_solution)
        return solutions
