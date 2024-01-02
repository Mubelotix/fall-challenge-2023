import sys
import math
import copy

# Score points by scanning valuable fish faster than your opponent.

colors = {}
types = {}
positions = {}
speeds = {}
saved_scans = set()
foe_saved_scans = set()
drones = {}

class Drone:
    def __init__(self, x, y, emergency, battery):
        self.x = x
        self.y = y
        self.emergency = emergency
        self.battery = battery
        self.last_light = -math.inf
        self.scans = set()
        self.going_up = False

class PossibleFishPosition:
    def __init__(self, ty):
        self.min_x = 0
        self.max_x = 9999
        match ty:
            case -1:
                self.min_y = 2500
                self.max_y = 9999
            case 0:
                self.min_y = 2500
                self.max_y = 5000
            case 1:
                self.min_y = 5000
                self.max_y = 7500
            case 2:
                self.min_y = 7500
                self.max_y = 9999
            case _:
                print("Unknown fish type")

    def estimate(self):
        return [round((self.min_x+self.max_x)/2), round((self.min_y+self.max_y)/2)]
    
    def __str__(self):
        return f"[{self.min_x}..={self.max_x}, {self.min_y}..={self.max_y}]"

    def __repr__(self):
        return self.__str__()

creature_count = int(input())
for i in range(creature_count):
    creature_id, color, ty = [int(j) for j in input().split()]
    colors[creature_id] = color
    types[creature_id] = ty

# game loop
turn = 0
while True:
    my_score = int(input())
    foe_score = int(input())
    my_scan_count = int(input())
    for i in range(my_scan_count):
        creature_id = int(input())
        saved_scans.add(creature_id)
    foe_scan_count = int(input())
    for i in range(foe_scan_count):
        creature_id = int(input())
        foe_saved_scans.add(creature_id)
    my_drone_count = int(input())
    for i in range(my_drone_count):
        drone_id, drone_x, drone_y, emergency, battery = [int(j) for j in input().split()]
        if not drone_id in drones:
            drones[drone_id] = Drone(drone_x, drone_y, emergency, battery)
        else:
            drones[drone_id].x = drone_x
            drones[drone_id].y = drone_y
            drones[drone_id].emergency = emergency
            drones[drone_id].battery = battery
        if drone_y <= 500:
            drones[drone_id].going_up = False
        drones[drone_id].scans = set()
    foe_drone_count = int(input())
    for i in range(foe_drone_count):
        foe_drone_id, foe_drone_x, foe_drone_y, foe_emergency, foe_battery = [int(j) for j in input().split()]
    drone_scan_count = int(input())
    for i in range(drone_scan_count):
        drone_id, creature_id = [int(j) for j in input().split()]
        try:
            drones[drone_id].scans.add(creature_id)
        except:
            pass
    visible_creature_count = int(input())

    positions = {}
    any_monster_active = False
    for i in range(visible_creature_count):
        creature_id, creature_x, creature_y, creature_vx, creature_vy = [int(j) for j in input().split()]
        if types[creature_id] == -1 and (creature_vx != 0 or creature_vy != 0):
            any_monster_active = True
        positions[creature_id] = creature_x, creature_y
        speeds[creature_id] = creature_vx, creature_vy

    # Find out what the possible fish positions are
    possible_fish_positions = {}
    for creature_id in types.keys():
        if not creature_id in positions:
            possible_fish_positions[creature_id] = PossibleFishPosition(types[creature_id])
    radar_blip_count = int(input())
    for i in range(radar_blip_count):
        inputs = input().split()
        drone_id = int(inputs[0])
        creature_id = int(inputs[1])
        radar = inputs[2]
        if creature_id in possible_fish_positions:
            match radar:
                case "TL":
                    possible_fish_positions[creature_id].max_y = min(drones[drone_id].y, possible_fish_positions[creature_id].max_y)
                    possible_fish_positions[creature_id].max_x = min(drones[drone_id].x, possible_fish_positions[creature_id].max_x)
                case "TR":
                    possible_fish_positions[creature_id].max_y = min(drones[drone_id].y, possible_fish_positions[creature_id].max_y)
                    possible_fish_positions[creature_id].min_x = max(drones[drone_id].x+1, possible_fish_positions[creature_id].min_x)
                case "BL":
                    possible_fish_positions[creature_id].min_y = max(drones[drone_id].y+1, possible_fish_positions[creature_id].min_y)
                    possible_fish_positions[creature_id].max_x = min(drones[drone_id].x, possible_fish_positions[creature_id].max_x)
                case "BR":
                    possible_fish_positions[creature_id].min_y = max(drones[drone_id].y+1, possible_fish_positions[creature_id].min_y)
                    possible_fish_positions[creature_id].min_x = max(drones[drone_id].x+1, possible_fish_positions[creature_id].min_x)
                case _:
                    print("unknown direction")
    print(f"{possible_fish_positions}", file=sys.stderr, flush=True)

    # Complete positions with estimates
    inferred_positions = copy.deepcopy(positions)
    for creature_id in types.keys():
        if not creature_id in positions:
            if positions.get(creature_id) is not None:
                print("panic")
            inferred_positions[creature_id] = possible_fish_positions[creature_id].estimate()

    # Get all scans
    all_scans = set()
    for drone_id in drones.keys():
        for scan in drones[drone_id].scans:
            all_scans.add(scan)
    for scan in saved_scans:
        all_scans.add(scan)

    turn += 1
    targetted = set()
    for drone_id in drones.keys():
        # If emergency just wait
        if drones[drone_id].emergency:
            print("WAIT 0")
            continue

        # If going up
        if drones[drone_id].going_up:
            print(f"MOVE {drones[drone_id].x} 500 0")
            continue

        # Retain positions from unscanned poissons
        unscanned_positions = copy.deepcopy(inferred_positions)
        for creature_id in all_scans:
            try:
                unscanned_positions.pop(creature_id)
            except:
                pass
        for creature_id in targetted:
            try:
                unscanned_positions.pop(creature_id)
            except:
                pass
        
        # Compute their distances
        distances = {}
        for creature_id in unscanned_positions.keys():
            x, y = unscanned_positions[creature_id]
            dx = x - drones[drone_id].x
            dy = y - drones[drone_id].y
            dist = math.sqrt(dx**2 + dy**2)
            distances[creature_id] = dist
        print(f"{positions}\n{inferred_positions}\n{distances}\n{drones[drone_id].scans}", file=sys.stderr, flush=True)
        
        # Get the closest passive and monster
        closest_dist = 10000
        closest_creature_id = 0
        closest_monster_dist = 10000
        closest_monster_id = 0
        for creature_id in distances.keys():
            distance = distances[creature_id]
            if types[creature_id] == -1:
                if distance < closest_monster_dist:
                    closest_monster_dist = distance
                    closest_monster_id = creature_id
            else:
                if distance < closest_dist:
                    closest_dist = distance
                    closest_creature_id = creature_id

        # When all fish is caught, go to top
        if closest_creature_id == 0:
            print(f"All fishes caught!", file=sys.stderr, flush=True)
            print(f"MOVE {drones[drone_id].x} 0 0")
            continue

        # When danger is nearby, go save the fish
        if closest_monster_dist < 1200 and len(drones[drone_id].scans) > 0:
            print(f"Danger nearby!", file=sys.stderr, flush=True)
            print(f"MOVE {drones[drone_id].x} 500 0")
            drones[drone_id].going_up = True
            continue

        # Get to the target
        print(f"Getting to fish {closest_creature_id}", file=sys.stderr, flush=True)
        tx, ty = inferred_positions[closest_creature_id]
        targetted.add(closest_creature_id)

        # Turn light on when allows catching fish
        #if closest_dist > 800 and closest_dist <= 2000:
        #    light = 1
        #    drones[drone_id].last_light = turn
        #else:
        #    light = 0
        light = 0

        #dx = tx - drone_x
        #dy = ty - drone_y
        #mx_ratio = dx / (abs(dx)+abs(dy))
        #my_ratio = dy / (abs(dx)+abs(dy))
        #mx = math.floor(600*mx_ratio)
        #my = math.floor(600*my_ratio)
        #ex = drone_x+mx
        #ey = drone_y+my

        # Write an action using print
        #print(f"tx ty {tx} {ty}\ndx dy {dx} {dy}\nm ratios {mx_ratio} {my_ratio}\nmx my {mx} {my}\nex ey {ex} {ey}", file=sys.stderr, flush=True)

        # MOVE <x> <y> <light (1|0)> | WAIT <light (1|0)>
        print(f"MOVE {tx} {ty} {light}")
