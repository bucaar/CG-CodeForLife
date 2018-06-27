import sys
import math
from itertools import permutations

#prints to stderr
def debug(*msg):
    msg = [str(x) for x in msg]
    print(' '.join(msg), file=sys.stderr)

#prints the sample in a nice way
def print_sample(sample):
    if sample["health"] < 0:
        debug("{}: ? Rank {}".format(sample["id"], sample["rank"]))
    else:
        debug("{}: {}A {}B {}C {}D {}E {} {}".format(sample["id"], sample["cost_a"], sample["cost_b"], sample["cost_c"], sample["cost_d"], sample["cost_e"], sample["health"], sample["gain"]))

#used for keeping track of all the turn information    
PLAYER = []
AVAILABLE = []
RETURNING = [0,0,0,0,0]
SAMPLE = []
SCIENCE = []
LETTERS = "abcde"
TURN = 0

def opponent_hoarding():
    pass

#returns how many of each sample we should be carrying
def get_ideal_sample_ranks():
    total_expertise = sum(PLAYER[0]["expertise_" + x] for x in LETTERS)
    if TURN > 140 and PLAYER[0]["score"] < PLAYER[1]["score"]:
        return [0,0,3]
    if total_expertise < 6:
        return [3,0,0]
    if total_expertise < 9:
        return [1,2,0]
    if total_expertise < 12:
        return [0,3,0]
    
    return [0,2,1]
    
#returns the total number of molecules we would be holding if we were to get the minimum requirement
def get_total_storage_for_samples(samples):
    if type(samples) != list:
        samples = [samples]
    storage = [PLAYER[0]["storage_" + x] for x in LETTERS]
    expertise = [PLAYER[0]["expertise_" + x] for x in LETTERS]
    cost = get_required_molecules(samples)
    total = sum(storage)
    for i in range(5):
        extra = cost[i] - (storage[i] + expertise[i])
        if extra > 0:
            total += extra
    return total

#returns true if we are storing enough molecules for the sample
def carry_enough_molecules(sample):
    return all(PLAYER[0]["storage_" + x] + PLAYER[0]["expertise_" + x] >= sample["cost_" + x] for x in LETTERS)
    
#returns true if there are enough molecules to produce this sample
def exists_enough_molecules(samples):
    if type(samples) != list:
        samples = [samples]
        
    return all(PLAYER[0]["storage_" + LETTERS[i]] + PLAYER[0]["expertise_" + LETTERS[i]] + AVAILABLE[i] + RETURNING[i] >= sum(s["cost_" + LETTERS[i]] for s in samples) for i in range(5))
    
#returns a list of every permutation of lst
def powerset(lst):
    s = list(lst)
    ps = []
    for r in range(1, min(len(s)+1, 4)):
        c = permutations(s, r)
        for x in c:
            ps.append(list(x))
        
    return ps

#returns a list of total molecules we can use: (storage + expertise)
def get_actual_molecules():
    return [PLAYER[0]["storage_" + x] + PLAYER[0]["expertise_" + x] for x in LETTERS]

#returns a list of total number of molecules we would need to produce the samples 
def get_required_molecules(samples, gain=True):
    if type(samples) != list:
        samples = [samples]
    required_molecules = [0,0,0,0,0]
    gain = [0,0,0,0,0]
    for sample in samples:
        for i in range(5):
            required_molecules[i] += max((sample["cost_" + LETTERS[i]] - gain[i]), 0)
        if sample["gain"].lower() in LETTERS and gain:
            gain[LETTERS.index(sample["gain"].lower())] += 1
    return required_molecules
    
#returns the best combination of sampels such that we can produce them all
def get_best_combination(samples):
    ps = powerset(samples)
    ps = sorted(ps, key=lambda x: get_total_storage_for_samples(x))
    ps = sorted(ps, key=lambda x: sum(y["health"] for y in x), reverse=True)
    #for p in ps:
        #debug([x["id"] for x in p], sum(y["health"] for y in p), get_total_storage_for_samples(p), get_required_molecules(p))
    for best in ps:
        total_cost = sum(x["total_cost"] for x in best)
        total_health = sum(x["health"] for x in best)
        if get_total_storage_for_samples(best) <= 10 and exists_enough_molecules(best) and all(b["health"] > 0 for b in best):
            return best
            
    return None

#returns the best action based on the game state
def get_action():
    global RETURNING
    target = PLAYER[0]["target"]
    eta = PLAYER[0]["eta"]
    carried_samples = [x for x in SAMPLE if x["carried_by"] == 0]
    opponent_carried = [x for x in SAMPLE if x["carried_by"] == 1]
    undiagnosed = [x for x in carried_samples if x["health"] < 0]
    carried_unproducable = [x for x in carried_samples if any(x["cost_" + l] > PLAYER[0]["expertise_" + l] + 5 for l in LETTERS)]
    cloud = [x for x in SAMPLE if x["carried_by"] == -1]
    usable_cloud = [x for x in cloud if exists_enough_molecules(x)]
    best_combo = get_best_combination(carried_samples)
    best_including_cloud = get_best_combination(carried_samples + usable_cloud)
    best_including_cloud_not_carried = None
    
    actual_carried = None
    required_for_best = None
    needed_molecule = None
    
    debug("Cloud:", str(len(usable_cloud)) + "/" + str(len(cloud)))
    debug("Carried:", len(carried_samples))
    for x in carried_samples:
        print_sample(x)
    
    if best_combo:
        actual_carried = get_actual_molecules()
        required_for_best = get_required_molecules(best_combo)
        opponent_needed = get_required_molecules(opponent_carried, gain=False)
        total_needed = [a+b for a, b in zip(required_for_best, opponent_needed)]
        debug("Best:", [x["id"] for x in best_combo])
        #debug("A:", actual_carried)
        #debug("R:", required_for_best)
        #debug("T:", total_needed)
        order = [(LETTERS[i].upper(), actual_carried[i], required_for_best[i], total_needed[i]) for i in range(5)]
        order = sorted(order, key=lambda x: (x[3], x[2]), reverse=True)
        debug("O:", ''.join([o[0] for o in order]))
        for o in order:
            if o[1] < o[2]:
                needed_molecule = o[0]
                break
        debug("N:", needed_molecule)
        
    if best_including_cloud:
        best_including_cloud_not_carried = [x for x in best_including_cloud if x not in carried_samples]
        debug("Best (cloud):", [x["id"] for x in best_including_cloud])
    
    if eta > 0:
        return "ETA: " + str(eta)
    
    #DEFENSE:
    opponent_could_win = [x for x in opponent_carried if x["health"] + PLAYER[1]["score"] > PLAYER[0]["score"] and all(x["cost_" + LETTERS[i]] <= PLAYER[1]["storage_" + LETTERS[i]] + PLAYER[1]["expertise_" + LETTERS[i]] + AVAILABLE[i] + RETURNING[i] for i in range(5))]
    if PLAYER[0]["score"] > PLAYER[1]["score"] and opponent_could_win and TURN > 175:
        opponent_could_win = sorted(opponent_could_win, key=lambda x: get_required_molecules(x))
        debug("WIN:", len(opponent_could_win), opponent_could_win[0]["id"])
        if target != "MOLECULES":
            return "GOTO MOLECULES"
        defense = get_required_molecules(opponent_could_win[0])
        debug("DEFENSE:", defense)
        for i in range(5):
            if defense[i] > 0 and sum(PLAYER[0]["storage_"+l] for l in LETTERS) < 10 and AVAILABLE[i] > 0:
                return "CONNECT " + LETTERS[i].upper()
    
    if target == "START_POS":
        return "GOTO SAMPLES"
    
    if target == "SAMPLES":
        if len(carried_samples) == 3 or best_including_cloud and len(carried_samples) + len(best_including_cloud_not_carried) >= 3:
            return "GOTO DIAGNOSIS"
        
        ideal = get_ideal_sample_ranks()
        carried_by_rank = [len([x for x in carried_samples if x["rank"] == r]) for r in [1,2,3]]
        for i in range(3):
            if carried_by_rank[i] < ideal[i]:
                return "CONNECT " + str(i+1)
            
    if target == "DIAGNOSIS":
        #TODO: We have all producable samples, but there arent molecules available
        if undiagnosed:
            return "CONNECT " + str(undiagnosed[0]["id"])
        if carried_unproducable:
            return "CONNECT " + str(carried_unproducable[0]["id"])
        if best_including_cloud and best_including_cloud != best_combo:
            if len(carried_samples) == 3:
                #need to store one we are holding
                unwanted = [x for x in carried_samples if x not in best_including_cloud]
                return "CONNECT " + str(unwanted[0]["id"])
            else:
                #grab one from the cloud
                needed = [x for x in usable_cloud if x not in carried_samples]
                return "CONNECT " + str(needed[0]["id"])
        if len(carried_samples) < 3 and usable_cloud:
            best = sorted(usable_cloud, key=lambda x: get_total_storage_for_samples(x))
            best = sorted(best, key=lambda x: x["health"], reverse=True)
            for b in best:
                if get_total_storage_for_samples(b) <= 10:
                    return "CONNECT " + str(b["id"])
                        
        if needed_molecule:
            return "GOTO MOLECULES"
        if best_combo:
            return "GOTO LABORATORY"
        if len(carried_samples) < 3:
            return "GOTO SAMPLES"
        return "GOTO MOLECULES"

    if target == "MOLECULES":
        if best_including_cloud is not None and best_including_cloud != best_combo:
            return "GOTO DIAGNOSIS"
        if needed_molecule:
            return "CONNECT " + needed_molecule
        if best_combo and (len(carried_samples) > 1 or TURN > 180):
            return "GOTO LABORATORY"
        #if best_combo and PLAYER[1]["target"] in "MOLECULESLABORATORY":
        #    return "WAIT"
        #TODO: We have a combo, but no longer have enough molecules - wait for them to replenish
        if not best_combo:
            if len(carried_samples) > 1:
                return "GOTO DIAGNOSIS"
        return "GOTO SAMPLES"
    
    if target == "LABORATORY":
        can_produce = [x for x in carried_samples if carry_enough_molecules(x)]
        if len(can_produce) == 1:
            return "CONNECT " + str(can_produce[0]["id"])
        if best_combo:
            for x in best_combo:
                if carry_enough_molecules(x):
                    RETURNING = [max(x["cost_" + l] - PLAYER[0]["expertise_" + l], 0) for l in LETTERS]
                    return "CONNECT " + str(x["id"])
            if needed_molecule:
                RETURNING = [0,0,0,0,0]
                return "GOTO MOLECULES"
        elif best_including_cloud:
            RETURNING = [0,0,0,0,0]
            return "GOTO DIAGNOSIS"
        else:
            RETURNING = [0,0,0,0,0]
            return "GOTO SAMPLES"
            
        
    return "WAIT No Action."
            
#the science projects
SCIENCE = []
project_count = int(input())
for i in range(project_count):
    a, b, c, d, e = [int(j) for j in input().split()]
    SCIENCE.append({
        "cost_a": a,
        "cost_b": b,
        "cost_c": c,
        "cost_d": d,
        "cost_e": e
    })

# game loop
while True:
    TURN += 1
    debug("Turn", TURN)
    PLAYER = []
    for i in range(2):
        target, eta, score, storage_a, storage_b, storage_c, storage_d, storage_e, expertise_a, expertise_b, expertise_c, expertise_d, expertise_e = input().split()
        eta = int(eta)
        score = int(score)
        storage_a = int(storage_a)
        storage_b = int(storage_b)
        storage_c = int(storage_c)
        storage_d = int(storage_d)
        storage_e = int(storage_e)
        expertise_a = int(expertise_a)
        expertise_b = int(expertise_b)
        expertise_c = int(expertise_c)
        expertise_d = int(expertise_d)
        expertise_e = int(expertise_e)
        
        PLAYER.append({
            "target": target,
            "eta": eta,
            "score": score,
            "storage_a": storage_a,
            "storage_b": storage_b,
            "storage_c": storage_c,
            "storage_d": storage_d,
            "storage_e": storage_e,
            "total_storage": storage_a + storage_b + storage_c + storage_d + storage_e,
            "expertise_a": expertise_a,
            "expertise_b": expertise_b,
            "expertise_c": expertise_c,
            "expertise_d": expertise_d,
            "expertise_e": expertise_e
        })
        
    available_a, available_b, available_c, available_d, available_e = [int(i) for i in input().split()]
    
    AVAILABLE = [available_a, available_b, available_c, available_d, available_e]
    
    SAMPLE = []
    sample_count = int(input())
    for i in range(sample_count):
        sample_id, carried_by, rank, expertise_gain, health, cost_a, cost_b, cost_c, cost_d, cost_e = input().split()
        sample_id = int(sample_id)
        carried_by = int(carried_by)
        rank = int(rank)
        health = int(health)
        cost_a = int(cost_a)
        cost_b = int(cost_b)
        cost_c = int(cost_c)
        cost_d = int(cost_d)
        cost_e = int(cost_e)
        SAMPLE.append({
            'id': sample_id,
            'carried_by': carried_by,
            'rank': rank,
            'gain': expertise_gain,
            'health': health,
            'cost_a': cost_a,
            'cost_b': cost_b,
            'cost_c': cost_c,
            'cost_d': cost_d,
            'cost_e': cost_e,
            'total_cost': cost_a + cost_b + cost_c + cost_d + cost_e
        })
        
    action = get_action()
    print(action)