import sys
import math
import copy

# Score points by scanning valuable fish faster than your opponent.

def clamp(n, min, max): 
    if n < min: 
        return min
    elif n > max: 
        return max
    else: 
        return n 

colors = {}
types = {}
positions = {}
speeds = {}
saved_scans = set()
foe_saved_scans = set()
drones = {}
possible_fish_positions = {}

# Positions {4: (3874, 3550), 5: (6402, 4411), 6: (8355, 5131), 16: (2648, 4414), 17: (5807, 4260), 19: (8248, 4481)}
# Possible positions {7: [3217..=6417, 5000..=6226], 8: [2567..=9999, 7500..=9999], 10: [0..=2000, 3057..=5000], 11: [2001..=2400, 3400..=5000], 12: [2567..=8625, 6227..=7100], 13: [3939..=4739, 6227..=6989], 14: [2567..=9999, 7500..=9999], 15: [2567..=5098, 7500..=9999], 16: [2484..=2484, 7426..=7426], 17: [2567..=9999, 2500..=6226]}



class Drone:
    def __init__(self, x, y, emergency, battery):
        self.x = x
        self.y = y
        self.emergency = emergency
        self.battery = battery
        self.last_light = -math.inf
        self.scans = set()
        self.going_up = False
        if x < 5000:
            self.area = "left"
        else:
            self.area = "right"

class PossibleFishPosition:
    def __init__(self, ty):
        self.min_x = 0
        self.max_x = 9999
        self.min_y = 0
        self.max_y = 9999
        self.restrict_ty(ty)
        
    def restrict_ty(self, ty):
        match ty:
            case -1:
                self.min_y = max(self.min_y, 2500)
                self.max_y = min(self.max_y, 9999)
            case 0:
                self.min_y = max(self.min_y, 2500)
                self.max_y = min(self.max_y, 5000)
            case 1:
                self.min_y = max(self.min_y, 5000)
                self.max_y = min(self.max_y, 7500)
            case 2:
                self.min_y = max(self.min_y, 7500)
                self.max_y = min(self.max_y, 9999)
            case _:
                print("Unknown fish type")
        self.min_x = max(self.min_x, 0)
        self.max_x = min(self.max_x, 9999)

    def extend(self, ty):
        match ty:
            case -1:
                self.min_y -= 540
                self.max_y += 540
                self.min_x -= 540
                self.max_x += 540
            case _:
                self.min_y -= 400
                self.max_y += 400
                self.min_x -= 400
                self.max_x += 400
        self.restrict_ty(ty)

    def set_position(self, position):
        self.min_x = position[0]
        self.max_x = position[0]
        self.min_y = position[1]
        self.max_y = position[1]

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
    for creature_id in types.keys():
        if not creature_id in possible_fish_positions:
            possible_fish_positions[creature_id] = PossibleFishPosition(types[creature_id])
        else:
            possible_fish_positions[creature_id].extend(types[creature_id])
    for creature_id in positions:
        position = positions[creature_id]
        possible_fish_positions[creature_id].set_position(position)
    radar_blip_count = int(input())
    still_in_game = set()
    for i in range(radar_blip_count):
        inputs = input().split()
        drone_id = int(inputs[0])
        creature_id = int(inputs[1])
        still_in_game.add(creature_id)
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
    removed_from_game = set()
    for creature_id in possible_fish_positions.keys():
        if not creature_id in still_in_game:
            removed_from_game.add(creature_id)
    for creature_id in removed_from_game:
        possible_fish_positions.pop(creature_id)

    # Complete positions with estimates
    inferred_positions = copy.deepcopy(positions)
    for creature_id in possible_fish_positions.keys():
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

    # Get remaining fish
    remaining_fish = set()
    for creature_id in inferred_positions.keys():
        if not creature_id in all_scans:
            remaining_fish.add(creature_id)

    print(f"Positions {positions}\nPossible positions {possible_fish_positions}", file=sys.stderr, flush=True)

    turn += 1
    targetted = set()
    for drone_id in drones.keys():
        drone = drones[drone_id]

        # If emergency just wait
        if drone.emergency:
            print("WAIT 0 🚨")
            continue
        
        # Go up if useful and not costly
        if drone.y < 4500 and len(drone.scans) > 2:
            drone.going_up = True

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
            dx = x - drone.x
            dy = y - drone.y
            dist = math.sqrt(dx**2 + dy**2)
            distances[creature_id] = dist
        print(f"{positions}\n{inferred_positions}\n{distances}\n{drone.scans}", file=sys.stderr, flush=True)

        # Get the closest passive, deepest passive, and closest monster
        closest_dist = 10000
        closest_creature_id = 0
        deepest_depth = 0
        deepest_creature_id = 0
        closest_monster_dist = 10000
        closest_monster_id = 0
        for creature_id in distances.keys():
            distance = distances[creature_id]
            if types[creature_id] == -1:
                if distance < closest_monster_dist:
                    closest_monster_dist = distance
                    closest_monster_id = creature_id
            else:
                if distance < closest_dist and distance >= 800:
                    closest_dist = distance
                    closest_creature_id = creature_id
                is_left = inferred_positions[creature_id][0] < 5000
                in_area = (drone.area == "left" and is_left) or (drone.area == "right" and not is_left)
                if in_area and inferred_positions[creature_id][1] > deepest_depth:
                    deepest_depth = inferred_positions[creature_id][1]
                    deepest_creature_id = creature_id

        if deepest_creature_id == 0:
            drone.going_up = True

        # If going up
        if drone.going_up:
            emojis: str = "⬆️"
            if closest_monster_dist < 2000:
                emojis += "⚠️"
                dy = -424
                if inferred_positions[closest_monster_id][1] < drone.y and drone.x < inferred_positions[closest_monster_id][0]:
                    dx = -424
                else:
                    dx = 424
                ex = round(drone.x+dx)
                ey = round(drone.y+dy)
                print(f"MOVE {ex} {ey} 0 {emojis}")
            else:
                print(f"MOVE {drone.x} 500 0 {emojis}")
            continue
        else:
            emojis: str = "🏹"
            tx = inferred_positions[deepest_creature_id][0]
            ty = inferred_positions[deepest_creature_id][1]
            emojis += str(deepest_creature_id)
            if closest_monster_dist < 2000:
                # Vector to target
                emojis += "⚠️"
                dx = tx - drone.x
                dy = ty - drone.y
                if abs(dx) < abs(dy):
                    if dy < 0 and inferred_positions[closest_monster_id][1] < drone.y:
                        dy = -424
                        if drone.x < inferred_positions[closest_monster_id][0]:
                            dx = -424
                            emojis += "1"
                        else:
                            dx = 424
                            emojis += "2"
                    elif dy > 0 and inferred_positions[closest_monster_id][1] > drone.y:
                        dy = 424
                        if drone.x < inferred_positions[closest_monster_id][0]:
                            dx = -424
                            emojis += "3"
                        else:
                            dx = 424
                            emojis += "4"
                else:
                    if dx < 0 and inferred_positions[closest_monster_id][0] < drone.x:
                        dx = -424
                        if drone.y < inferred_positions[closest_monster_id][1]:
                            dy = -424
                            emojis += "5"
                        else:
                            dy = 424
                            emojis += "6"
                    elif dx > 0 and inferred_positions[closest_monster_id][0] > drone.x:
                        dx = 424
                        if drone.y < inferred_positions[closest_monster_id][1]:
                            dy = -424
                            emojis += "7"
                        else:
                            dy = 424
                            emojis += "8"
                tx = round(drone.x+dx)
                ty = round(drone.y+dy)
        
        # Turn on light every 3 turns
        if drone.y > 2500 and turn - drone.last_light >= 3:
            light = 1
            emojis += "💡"
            drone.last_light = turn
        else:
            light = 0

        print(f"MOVE {tx} {ty} {light} {emojis}")
        continue


        # When all fish is caught, go to top
        if closest_creature_id == 0:
            print(f"All fishes caught!", file=sys.stderr, flush=True)
            print(f"MOVE {drone.x} 0 0")
            continue

        # When danger is nearby, go save the fish
        if closest_monster_dist < 1200 and len(drone.scans) > 0:
            print(f"Danger nearby!", file=sys.stderr, flush=True)
            print(f"MOVE {drone.x} 500 0")
            drone.going_up = True
            continue

        # Get to the target
        print(f"Getting to fish {closest_creature_id}", file=sys.stderr, flush=True)
        tx, ty = inferred_positions[closest_creature_id]
        targetted.add(closest_creature_id)

        # Turn light on when allows catching fish
        #if closest_dist > 800 and closest_dist <= 2000:
        #    light = 1
        #    drone.last_light = turn
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
