# Time between successful PoW solutions
POW_SOLUTION_TIME = 10
# Time for a block to traverse the network
TRANSIT_TIME = 10
# Max uncle depth
UNCLE_DEPTH = 4
# Uncle block reward (normal block reward = 1)
UNCLE_REWARD_COEFF = 30/32.
# Reward for including uncles
NEPHEW_REWARD_COEFF = 1/64.
# Rounds to test
ROUNDS = 200000

import random

all_miners = {}


class Miner():
    def __init__(self, p):
        self.hashpower = p
        self.id = random.randrange(10000000)
        # Set up a few genesis blocks (since the algo is grandpa-dependent,
        # we need two genesis blocks plus some genesis uncles)
        self.blocks = {}
        self.children = {}
        for i in range(UNCLE_DEPTH + 2):
            self.blocks[i] = \
                {"parent": i-1, "uncles": {}, "miner": -1, "height": i,
                 "score": i, "id": i}
            self.children[i-1] = {i: True}
        # ID of "latest block"
        self.head = UNCLE_DEPTH + 1

    # Hear about a block
    def recv(self, block):
        # Add the block to the set if it's valid
        addme = True
        if block["id"] in self.blocks:
            addme = False
        if block["parent"] not in self.blocks:
            addme = False
        if addme:
            self.blocks[block["id"]] = block
            if block["parent"] not in self.children:
                self.children[block["parent"]] = {}
            if block["id"] not in self.children[block["parent"]]:
                self.children[block["parent"]][block["id"]] = block["id"]
            if block["score"] > self.blocks[self.head]["score"]:
                self.head = block["id"]

    # Mine a block
    def mine(self):
        HEAD = self.blocks[self.head]
        H = HEAD
        h = self.blocks[self.blocks[self.head]["parent"]]
        # Select the uncles. The valid set of uncles for a block consists
        # of the children of the 2nd to N+1th order grandparents minus
        # the parent and said grandparents themselves and blocks that were
        # uncles of those previous blocks
        u = {}
        notu = {}
        for i in range(UNCLE_DEPTH):
            for c in self.children.get(h["id"], {}):
                u[c] = True
            notu[H["id"]] = True
            for c in H["uncles"]:
                notu[c] = True
            H = h
            h = self.blocks[h["parent"]]
        for i in notu:
            if i in u:
                del u[i]
        block = {"parent": self.head, "uncles": u, "miner": self.id,
                 "height": HEAD["height"] + 1, "score": HEAD["score"]+1+len(u),
                 "id": random.randrange(1000000000000)}
        self.recv(block)
        global all_miners
        all_miners[block["id"]] = block
        return block


# If b1 is the n-th degree grandchild and b2 is the m-th degree grandchild
# of nearest common ancestor C, returns min(m, n)
def cousin_degree(miner, b1, b2):
    while miner.blocks[b1]["height"] > miner.blocks[b2]["height"]:
        b1 = miner.blocks[b1]["parent"]
    while miner.blocks[b2]["height"] > miner.blocks[b1]["height"]:
        b2 = miner.blocks[b2]["parent"]
    t = 0
    while b1 != b2:
        b1 = miner.blocks[b1]["parent"]
        b2 = miner.blocks[b2]["parent"]
        t += 1
    return t

# Set hashpower percentages here
percentages = [1]*25 + [5, 5, 5, 5, 5, 10, 15, 25]
miners = []
for p in percentages:
    miners.append(Miner(p))

miner_dict = {}
for m in miners:
    miner_dict[m.id] = m

listen_queue = []

for t in range(ROUNDS):
    if t % 5000 == 0:
        print t
    for m in miners:
        R = random.randrange(POW_SOLUTION_TIME * sum(percentages))
        if R < m.hashpower and t < ROUNDS - TRANSIT_TIME * 3:
            b = m.mine()
            listen_queue.append([t + TRANSIT_TIME, b])
    while len(listen_queue) and listen_queue[0][0] <= t:
        t, b = listen_queue.pop(0)
        for m in miners:
            m.recv(b)

h = miners[0].blocks[miners[0].head]
profit = {}
total_blocks_in_chain = 0
length_of_chain = 0
ZORO = {}
print "### PRINTING BLOCKCHAIN ###"

while h["id"] > UNCLE_DEPTH + 2:
    # print h["id"], h["miner"], h["height"], h["score"]
    # print "Uncles: ", list(h["uncles"])
    total_blocks_in_chain += 1 + len(h["uncles"])
    ZORO[h["id"]] = True
    length_of_chain += 1
    profit[h["miner"]] = profit.get(h["miner"], 0) + \
        1 + NEPHEW_REWARD_COEFF * len(h["uncles"])
    for u in h["uncles"]:
        ZORO[u] = True
        u2 = miners[0].blocks[u]
        profit[u2["miner"]] = profit.get(u2["miner"], 0) + UNCLE_REWARD_COEFF
    h = miners[0].blocks[h["parent"]]

print "### PRINTING HEADS ###"

for m in miners:
    print m.head


print "### PRINTING PROFITS ###"

for p in profit:
    print miner_dict[p].hashpower, profit[p]

print "### PRINTING RESULTS ###"

groupings = {}
counts = {}
for p in profit:
    h = miner_dict[p].hashpower
    counts[h] = counts.get(h, 0) + 1
    groupings[h] = groupings.get(h, 0) + profit[p]

for c in counts:
    print c, groupings[c] / counts[c] / (groupings[1] / counts[1])

print " "
print "Total blocks produced: ", len(all_miners) - UNCLE_DEPTH
print "Total blocks in chain: ", total_blocks_in_chain
print "Efficiency: ", \
    total_blocks_in_chain * 1.0 / (len(all_miners) - UNCLE_DEPTH)
print "Average uncles: ", total_blocks_in_chain * 1.0 / length_of_chain - 1
print "Length of chain: ", length_of_chain
print "Block time: ", ROUNDS * 1.0 / length_of_chain
