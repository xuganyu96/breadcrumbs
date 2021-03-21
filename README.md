# Python backtracker
Implementation of backtracking algorithm with some additional features for:
1. Performance tracking
2. Multithreading
3. Logging
4. Behavior modification such as defining maximal depth or iterations
5. (Maybe) visualization

The core of this package includes two implementations of backtracking and the abstract class `BacktrackableState` which the two implementations will take as input.

Here is an example of how to use this package:
```python
from backtracker.search import recursive_search, iterative_search
from backtracker.examples import NQueens

empty = NQueens(6, tuple())

isols = iterative_search(empty)
rsols = recursive_search(empty)

print(isols, rsols)
```
