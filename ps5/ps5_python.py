# %%
# Initialize Otter
import otter
grader = otter.Notebook("ps5.ipynb")


# %% [markdown]
# ### Question 1
# This question will continue where we left off in lecture, by using the MapReduce class to perform data processing.

# %%
from functools import reduce
import itertools
import gzip


class MapReduce:
    @property
    def reduce_init(self):
        # override as necessary if the init parameter needs to change
        return None

    def mapper(self, x):
        raise NotImplementedError()

    def reducer(self, accum, x):
        raise NotImplementedError()

    def postprocess(self, reduced):
        # override if necessary
        return reduced

    def run(self, iterable):
        mapped = map(self.mapper, iterable)
        reduced = reduce(self.reducer, mapped, self.reduce_init)
        processed = self.postprocess(reduced)
        return processed


# %% [markdown]
# (To make things more flexible, we have also added an optional `.postprocess()` method that can be used to do additional processing after the reduction step.)

# %% [markdown]
# Questions 1(a)-1(c) concern the Enron dataset seen in lecture:

# %%
def enron(n=None):
    i1 = gzip.open("email-Enron.txt.gz", "rt")
    i2 = itertools.islice(i1, 4, None)  # slice off header
    return itertools.islice(i2, n)


# %% [markdown]
# 
# For each question below, implement a subclass of MapReduce such that calling `.run(enron(n))` produces the desired output. For example, if the question asked you to calcluate the total number of e-mails, your solution could be:

# %%
class NumEmails(MapReduce):
    @property
    def reduce_init(self):
        return 0

    def mapper(self, x):
        return 1

    def reducer(self, accum, x):
        return accum + x


NumEmails().run(enron(100))


# %% [markdown]
# **1(a)** (3 pts) Define a user's *importance* to be the number of unique people who e-mailed them (not including themself). Write a MapReduce class that returns a `collections.Counter` mapping each user ID to their importance when run.

# %%
class Importance(MapReduce):

    @property
    def reduce_init(self):
        return {}

    def mapper(self, line):
        return [int(x) for x in line.split("\t")]

    def reducer(self, accumulated, x):
        sender, receiver = x
        accumulated.setdefault(receiver, set())
        accumulated[receiver].add(sender)
        return accumulated

    def postprocess(self, reduced):
        from collections import Counter
        return Counter({k: len(v) for k, v in reduced.items()})


# %%
grader.check("q1a")


# %% [markdown]
# **1(b)** (4 pts) Define a user's *forgetfulness* to be the number of times they e-mailed themself. Write a MapReduce class that returns a `Counter` that maps each user who e-mailed themself at least once to their forgetfulness score.

# %%
class Forgetful(MapReduce):

    @property
    def reduce_init(self):
        return {}

    def mapper(self, line):
        return [int(x) for x in line.split("\t")]

    def reducer(self, accumulated, x):
        sender, receiver = x
        if sender == receiver:
            score = 1
        else:
            score = 0
        accumulated.setdefault(sender, 0)
        accumulated[sender] += score
        return accumulated

    def postprocess(self, reduced):
        from collections import Counter
        return Counter({k: v for k, v in reduced.items() if v != 0})


# %%
grader.check("q1b")


# %% [markdown]
# **1(c)** (5 pts) Define a user's *professor score* to be the number of unique individuals who e-mailed that user and never got a response back. Write a MapReduce class that returns the a `Counter()` mapping each user with a nonzero professor score to their score.

# %%
class ProfessorScore(MapReduce):
    @property
    def reduce_init(self):
        return {}

    def mapper(self, line):
        return [int(x) for x in line.split("\t")]

    def reducer(self, accumulated, x):
        key = tuple(x)
        if tuple(reversed(key)) not in accumulated.keys():
            accumulated.setdefault(key[0], -1)
            accumulated[key[0]] += 1
        return accumulated

    def postprocess(self, reduced):
        from collections import Counter
        return Counter({k: v for k, v in reduced.items()})


# %%
grader.check("1c")


# %% [markdown]
# Questions 1(d)-1(e) concern the following Facebook dataset:

# %%
import gzip
import itertools


def fb(n=None):
    return itertools.islice(gzip.open("fb.txt.gz", "rt"), n)


# %% [markdown]
# Each line of the file contains a list of integers. The first integer is a user id, and the remaining integers and the ids of all that user's Facebook friends. User 0 has a lot of friends:

# %%
next(fb())


# %% [markdown]
# Notes:
# - It is *not* necessarily the case that the friend of every user is also present in the dataset.
# - In this dataset, friendship is symmetric: $A$ is a friend of $B$ implies that $B$ is a friend of $A$. However, this is only indicated *once* in the data: if $A$ is a friend of $B$ and $A < B$, then $B$ appears in the friend list of $A$.

# %% [markdown]
# **1(d)** (5 pts) Define a *triangle* to be any set of three users $(A, B, C)$ such that they are all friends. For example, `126` is friends with both `0` and `1`, so `{0, 1, 126}` is a triangle. Write a MapReduce class that returns the set of all triangles in the dataset. Each triangle should be represented as a `frozenset` of three user ids.

# %%
class Triangles(MapReduce):

    @property
    def reduce_init(self):
        return {}

    def mapper(self, line):
        return [int(x) for x in line.split(" ")]

    def reducer(self, accumulated, x):
        user_id = x[0]
        friend = x[1:]
        accumulated.setdefault(user_id, set())
        accumulated[user_id].update(int(e) for e in friend)
        return accumulated

    def postprocess(self, reduced):
        out = set()
        put = set()
        for v in reduced.keys():
            for k in reduced[v]:
                if k in reduced.keys():
                    for a in reduced[k]:
                        if a in reduced.keys():
                            if a in reduced[v] or v in reduced[a]:
                                c = (v, k, a)
                                out.update(tuple(sorted(c)))
                                put.add(frozenset(out))
                                out = set()
        return put


# %%
grader.check("1d")


# %% [markdown]
# **1(e)** (5 pts) Social networks love to remind you how many friends you have in common with other people. Write a MapReduce class that returns, for every pair friends in the dataset, the number of friends that they have in common (not including each other). The returned data structure should be a `dict` whose keys are `frozenset()`s containing two userids, and values are integers giving the number of friends in common.

# %%
class CommonFriends(MapReduce):

    @property
    def reduce_init(self):
        return {}

    def mapper(self, line):
        return [int(x) for x in line.split(" ")]

    def reducer(self, accumulated, x):
        user_id = x[0]
        friend = x[1:]
        accumulated.setdefault(user_id, set())
        accumulated[user_id].update(int(e) for e in friend)
        return accumulated

    def postprocess(self, reduced):
        common = {}
        num = 0
        for v in reduced.keys():
            for k in reduced[v]:
                if k in reduced.keys():
                    for a in reduced[k]:
                        if a in reduced[v] or (a in reduced.keys() and v in reduced[a]):
                            num += 1
                    c = (k, v)
                    put = (tuple(sorted(c)))
                    common.setdefault(frozenset(put), num)
                    num = 0
        return common


# %%
grader.check("1e")


# %% [markdown]
# ## Question 2: Conway's game of life
# 
# [Conway's Game of Life](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life) 
# is a game devised by the late mathematician John Conway.
# 
# The game is played on an $m$-by-$n$ board, which we
# will represent as an $m$-by-$n$ Numpy array. 
# Each cell of the board (i.e., entry of our matrix), is
# either alive (which we will represent as a $1$) or dead (which we will
# represent as a $0$). 
# 
# The game proceeds in steps. At each step of the game, the board evolves according to the following rules:
# 
# -   A live cell with fewer than two live neighbors becomes a dead cell.
# 
# -   A live cell with more than three live neighbors becomes a dead cell.
# 
# -   A live cell with two or three live neighbors remains alive.
# 
# -   A dead cell with *exactly* three live neighbors becomes alive.
# 
# -   All other dead cells remain dead.
# 
# The neighbors of a cell are the 8 cells adjacent to it, i.e., left,
# right, above, below, upper-left, lower-left, upper-right and
# lower-right. Thus, in a $5\times 5$ game of life, the neighors of the middle cell are (shown in black):
# ```
# ⬜⬜⬜⬜⬜
# ⬜⬛⬛⬛⬜
# ⬜⬛⬜⬛⬜
# ⬜⬛⬛⬛⬜
# ⬜⬜⬜⬜⬜
# ```
# For cells that are on the boundary, we will follow the convention that the board is 
# *toroidal*, meaning that it wraps around the other side. So the neighbors of the top-left most
# square are (again shown in black):
# ```
# ⬜⬛⬜⬜⬛
# ⬛⬛⬜⬜⬛
# ⬜⬜⬜⬜⬜
# ⬜⬜⬜⬜⬜
# ⬛⬛⬜⬜⬛
# ```
# In matrix notation, this means that the top-left neighbor of cell $(i,j)$ is $(i-1 \mod m, j-1 \mod n)$, etc.
# 
# Write a class `GameOfLife` that plays this game:

# %%
import numpy as np
import matplotlib.pyplot as plt


class GameOfLife():
    
    def __init__(self, num) :
        for i in range(len(num)) :
            for j in range(len(num[i])) :
                if num[i][j] != 0 and num[i][j] != 1:
                    raise ValueError("Invalid input")
        self.data = num
        
    def __str__ (self) :
        s = ""
        S = self.data
        for i in range(len(S)) :
            for j in range(len(S[i])) :    
                if S[i][j] == 0 :
                    s += "\u2b1c"
                else :
                    s += "\u2B1B"
            if i < (len(S) - 1) :
                s += "\n"
        return s
    
    def __iter__(self):
        return self
    
    def __next__(self) :
        S = self.data
        a, b = S.shape
        
        count = np.zeros_like(S)
        S2 = S.copy()

        # check the neighbors
        for i in range(a):
            for j in range(b):
                neighbor = [S[(i-1)%a][(j-1)%b], S[(i-1)%a][(j)%b], S[(i-1)%a][(j+1)%b], S[i%a][(j-1)%b], 
                            S[i%a][(j+1)%b], S[(i+1)%a][(j-1)%b], S[(i+1)%a][j%b], S[(i+1)%a][(j+1)%b]]
                tmp = [1 for x in neighbor if x == 1]
                count[i,j] = sum(tmp)
                # print(tmp)

         # check self
        # for i in range(a):
        #     for j in range(b):
        #         if S[i][j] == 1 :
        #             if count == 2 or count == 3 :
        #                 S2[i][j] = 1
        #         if S[i][j] == 0 :
        #             if count == 3 :
        #                 S2[i][j] = 1
        #         else :
        #             S2[i][j] = 0
        
        S2 =  (S==1)*(count==2) + (S==1)*(count==3) + (S==0)*(count==3)
        S2 = S2.astype(np.int)
        # check whether the game will terminate    
        if np.array_equal(S2, self.data) == True :
            raise StopIteration("game terminate")

        self.data = S2
        # return S2

        
blinker = np.zeros((5, 5), dtype=int) 
blinker[1:4, 2] = 1
g = GameOfLife(blinker)
print(g)
next(g)
print(g)

 

# %% [markdown]
# Instances of the class should behave as follows:

# %% [markdown]
# **2(a)** (2 pts) The constructor of `GameOfLife` should accept a single argument, which is a two-dimensional Numpy integer array, and perform validation. A starting board is valid if it contains only zero and ones. (You may assume that the input is a 2-d Numpy integer array, but your constructor should check the part about zeros and ones.)

# %%
grader.check("2a")


# %% [markdown]
# **2(b)** (3 pts) Instances of `GameOfLife` should return a string representation of the current state of the game:
# ```
# >>> I = np.eye(5, dtype=int)  # 5x5 identity matrix
# >>> g = GameOfLife(I)
# >>> print(g)
# ⬛⬜⬜⬜⬜
# ⬜⬛⬜⬜⬜
# ⬜⬜⬛⬜⬜
# ⬜⬜⬜⬛⬜
# ⬜⬜⬜⬜⬛
# ```
# In the string representation, use the Unicode characters "⬛" to denote a live cell and "⬜" to denote a dead cell. In Python, these can be inputted as:

# %%
"\u2b1c", "\u2B1B"


# %%
grader.check("2b")


# %% [markdown]
# **2(c)** (10 pts) `GameOfLife` instances should be iterable. Calling `next` on the instance should return the next state of the game, represented as a Numpy array, which is determined by applying the rules stated above. If the game terminates, meaning that the board remains the same from one turn to the next, then the iterator terminates (by raising a `StopIteration`).
# 
# Here is an example of the game played using a $5 \times 5$ grid and a pattern that oscillates back and forth:
# 
# ```
# >>> blinker = np.zeros((5, 5), dtype=int) 
# >>> blinker[1:4, 2] = 1
# >>> g = GameOfLife(blinker)
# >>> print(g)
# ⬜⬜⬜⬜⬜
# ⬜⬜⬛⬜⬜
# ⬜⬜⬛⬜⬜
# ⬜⬜⬛⬜⬜
# ⬜⬜⬜⬜⬜
# >>> next(g)
# [[0 0 0 0 0]
#  [0 0 0 0 0]
#  [0 1 1 1 0]
#  [0 0 0 0 0]
#  [0 0 0 0 0]]
# >>> print(g)
# ⬜⬜⬜⬜⬜
# ⬜⬜⬜⬜⬜
# ⬜⬛⬛⬛⬜
# ⬜⬜⬜⬜⬜
# ⬜⬜⬜⬜⬜
# >>> next(g)
# [[0 0 0 0 0]
#  [0 0 1 0 0]
#  [0 0 1 0 0]
#  [0 0 1 0 0]
#  [0 0 0 0 0]]
# >>> print(g)
# ⬜⬜⬜⬜⬜
# ⬜⬜⬛⬜⬜
# ⬜⬜⬛⬜⬜
# ⬜⬜⬛⬜⬜
# ⬜⬜⬜⬜⬜
# ```
# 
# *Hint*: the main challenge to this exercise is in dealing with the toroidal matrix. To avoid having to consider special cases, use the fact that the neighbors of cell $(i,j)$ are $(i\pm 1 \mod m, j\pm 1 \mod n)$ where $a \mod b$ denotes the modulus (i.e. `a % b` in Python.)

# %%
grader.check("2c")


# %% [markdown]
# **2(d)** (just for fun) The following code will print out a Game of Life as it runs:

# %%
import ipywidgets as widgets
import time
import itertools

out = widgets.Output()


def play_gol(game, stop=None, wait=0.5):
    "play game of life for stop steps and show the output, waiting wait between each frame."
    for step in itertools.islice(game, stop):
        with out:
            print(game)
            out.clear_output(wait=True)
        time.sleep(wait)


out


# %% [markdown]
# Example:

# %%
glider = np.zeros((10, 10), dtype=int)
glider[5, 3:6] = 1
glider[4, 5] = 1
glider[3, 4] = 1
g = GameOfLife(glider)
# uncomment next line to view game
# play_gol(g, 10, 0.1)


# %% [markdown]
# Try running it with your own invented initial state. Can you make anything interesting happen? Some people have developed extremely elaborate games, for example:

# %%
tr = str.maketrans(".X", "01")
gosper = np.array(
    [list(map(int, row.strip().translate(tr)))
     for row in open("gosper-glider-gun.txt")]
)
# uncomment next line to view game
# play_gol(GameOfLife(gosper), 100, wait=0.01)


# %% [markdown]
# ---
# 
# To double-check your work, the cell below will rerun all of the autograder tests.

# %%
grader.check_all()


# %% [markdown]
# ## Submission
# 
# Make sure you have run all cells in your notebook in order before running the cell below, so that all images/graphs appear in the output. The cell below will generate a zip file for you to submit. **Please save before exporting!**
# 
# Upload this .zip file to Gradescope for grading.

# %%
# Save your notebook first, then run this cell to export your submission.
grader.export(pdf=False)


# %% [markdown]
#  


