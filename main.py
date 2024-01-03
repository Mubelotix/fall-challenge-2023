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
already_seen_monsters = set()

def should_monster_be_active(turn, y):
    return 500+(turn-1)*600+800 < y

close_threshold = 600+540+500

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
    def __init__(self, ty, creature_id):
        self.min_x = 0
        self.max_x = 9999
        if ty==-1 and creature_id%2==0:
            self.min_x = 0
            self.max_x = 5000
        else:
            self.min_x = 5000
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
    foe_scans = set()
    for i in range(drone_scan_count):
        drone_id, creature_id = [int(j) for j in input().split()]
        try:
            drones[drone_id].scans.add(creature_id)
        except:
            foe_scans.add(creature_id)
    visible_creature_count = int(input())

    positions = {}
    for i in range(visible_creature_count):
        creature_id, creature_x, creature_y, creature_vx, creature_vy = [int(j) for j in input().split()]
        positions[creature_id] = creature_x, creature_y
        speeds[creature_id] = creature_vx, creature_vy

        # Infer some monster positions based on symetry
        if types[creature_id] == -1 and not creature_id in already_seen_monsters and turn <= 18:
            if creature_id % 2 == 0:
                associated_creature_id = creature_id + 1
            else:
                associated_creature_id = creature_id - 1
            previous_x = creature_x - creature_vx
            previous_y = creature_y - creature_vy
            already_seen_monsters.add(creature_id)
            already_seen_monsters.add(associated_creature_id)
            positions[associated_creature_id] = 9999 - previous_x, previous_y
            print(f"Inferring {associated_creature_id} is in {9999 - previous_x} {previous_y}", file=sys.stderr, flush=True)

    # Find out what the possible fish positions are
    for creature_id in types.keys():
        if not creature_id in possible_fish_positions:
            possible_fish_positions[creature_id] = PossibleFishPosition(types[creature_id], creature_id)
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
    
    # Count points of scanned fish if they were saved right now
    potential_score = 0
    scans_by_ty = { 0: 0, 1: 0, 2: 0 }
    scans_by_color = { 0: 0, 1: 0, 2: 0, 3: 0 }
    foe_scans_by_ty = { 0: 0, 1: 0, 2: 0 }
    foe_scans_by_color = { 0: 0, 1: 0, 2: 0, 3: 0 }
    for creature_id in all_scans:
        multiplier = int(not creature_id in foe_saved_scans) + 1
        potential_score += (types[creature_id] + 1) * multiplier
        scans_by_ty[types[creature_id]] += 1
        scans_by_color[colors[creature_id]] += 1
    for creature_id in foe_saved_scans:
        foe_scans_by_ty[types[creature_id]] += 1
        foe_scans_by_color[colors[creature_id]] += 1
    for ty in scans_by_ty.keys():
        multiplier = int(foe_scans_by_ty[ty] < 4) + 1
        if scans_by_ty[ty] == 4:
            potential_score += 4 * multiplier
    for color in scans_by_color.keys():
        multiplier = int(foe_scans_by_color[color] < 3) + 1
        if scans_by_color[color] == 3:
            potential_score += 3 * multiplier
    
    # Get foe potential score
    all_possible_foe_scans = set()
    all_possible_foe_scans = all_possible_foe_scans.union(foe_saved_scans)
    all_possible_foe_scans = all_possible_foe_scans.union(foe_scans)
    all_possible_foe_scans = all_possible_foe_scans.union(still_in_game)
    foe_max_score = 0
    foe_max_scans_by_ty = { 0: 0, 1: 0, 2: 0 }
    foe_max_scans_by_color = { 0: 0, 1: 0, 2: 0, 3: 0 }
    for creature_id in all_possible_foe_scans:
        if types[creature_id] == -1:
            continue
        multiplier = int(not creature_id in all_scans) + 1
        foe_max_score += (types[creature_id] + 1) * multiplier
        foe_max_scans_by_ty[types[creature_id]] += 1
        foe_max_scans_by_color[colors[creature_id]] += 1
    for ty in foe_max_scans_by_ty.keys():
        multiplier = int(scans_by_ty[ty] < 4) + 1
        if foe_max_scans_by_ty[ty] == 4:
            foe_max_score += 4 * multiplier
    for color in foe_max_scans_by_color.keys():
        multiplier = int(scans_by_color[color] < 3) + 1
        if foe_max_scans_by_color[color] == 3:
            foe_max_score += 3 * multiplier

    print(f"Could score {potential_score} now (foe max {foe_max_score})\nPositions {positions}\nPossible positions {possible_fish_positions}", file=sys.stderr, flush=True)

    turn += 1
    targetted = set()
    for i_drone, drone_id in enumerate(drones.keys()):
        drone = drones[drone_id]
        emojis = ""

        # Enable going up if we could win
        if potential_score >= foe_max_score:
            emojis += "🏆"
            drone.going_up = True

        # If emergency just wait
        if drone.emergency:
            print("WAIT 0 🚨")
            continue
        
        # Stop going up if not useful
        if len(drone.scans) == 0 and drone.going_up:
            drone.going_up = False
            drone.area = "all"
            emojis += "🔄"

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
        print(f"{distances}\n{drone.scans}", file=sys.stderr, flush=True)

        # Get the closest passive, deepest passive, and closest monster
        closest_dist = 10000
        closest_creature_id = 0
        deepest_depth = 0
        deepest_creature_id = 0
        closest_monster_dist = 10000
        closest_monster_id = 0
        close_monsters = set()
        for creature_id in distances.keys():
            distance = distances[creature_id]
            if types[creature_id] == -1:
                if distance < closest_monster_dist:
                    closest_monster_dist = distance
                    closest_monster_id = creature_id
                if distance <= close_threshold/1.5:
                    close_monsters.add(creature_id)
            else:
                if distance < closest_dist and distance >= 800:
                    closest_dist = distance
                    closest_creature_id = creature_id
                is_left = inferred_positions[creature_id][0] < 5000
                in_area = (drone.area == "left" and is_left) or (drone.area == "right" and not is_left) or drone.area == "all"
                if in_area and inferred_positions[creature_id][1] > deepest_depth:
                    deepest_depth = inferred_positions[creature_id][1]
                    deepest_creature_id = creature_id

        # Choose where to go when no fish is to be found
        if deepest_creature_id == 0:
            if len(drone.scans) > 0:
                drone.going_up = True
            else:
                drone.area = "all"
                print(f"MOVE {drone.x} {drone.y+600} 0 🔄")
                continue

        # If going up
        if drone.going_up:
            emojis += "⬆️"
            tx = drone.x
            ty = 500
        else:
            emojis += "🏹" + str(deepest_creature_id)
            tx = inferred_positions[deepest_creature_id][0]
            ty = inferred_positions[deepest_creature_id][1]

        # Avoid threats when multiple
        if len(close_monsters) > 1:
            emojis += "😱"
            dx_sum = 0
            dy_sum = 0
            count = 0
            for creature_id in close_monsters:
                dx = drone.x - inferred_positions[creature_id][0]
                dy = drone.y - inferred_positions[creature_id][1]
                current_norm = math.sqrt(dx**2 + dy**2)
                if current_norm == 0:
                    current_norm = 600
                    dy = -600
                extension = 600/current_norm
                dx *= extension
                dy *= extension
                dx_sum += dx
                dy_sum += dy
                count += 1
            dx = dx_sum / count
            dy = dy_sum / count
            current_norm = math.sqrt(dx**2 + dy**2)
            if current_norm == 0:
                current_norm = 600
                dy = -600
            extension = 600/current_norm
            dx *= extension
            dy *= extension
            tx = round(drone.x+dx)
            ty = round(drone.y+dy)
        elif closest_monster_dist <= close_threshold:
            emojis += "⚠️"
            dx = tx - drone.x
            dy = ty - drone.y
            low = 424
            high = 424
            if closest_monster_dist < 1150:
                low = 154
                high = 580
                emojis += "⚠️"
            if closest_monster_dist < 800:
                low = 78
                high = 595
                emojis += "⚠️"
            if closest_monster_dist < 680:
                low = -78
                high = 595
                emojis += "⚠️"
            emojis += str(closest_monster_id)
            l = ""
            if drone.x > 9999-540:
                dx = -low
                if inferred_positions[closest_monster_id][1] < drone.y: # monster is higher
                    dy = high
                    l = "1"
                else:
                    dy = -high
                    l = "2"
            elif drone.x < 540:
                dx = low
                if inferred_positions[closest_monster_id][1] < drone.y: # monster is higher
                    dy = high
                    l = "3"
                else:
                    dy = -high
                    l = "4"
            elif drone.y > 9999-540:
                dy = -low
                if inferred_positions[closest_monster_id][0] < drone.x: # monster is left
                    dx = high
                    l = "5"
                else:
                    dx = -high
                    l = "6"
            elif abs(dx) < abs(dy):
                if dy < 0:
                    if inferred_positions[closest_monster_id][1] < drone.y:
                        dy = -low
                        if drone.x < inferred_positions[closest_monster_id][0]:
                            dx = -high
                            l = "A"
                        else:
                            dx = high
                            l = "B"
                    elif dx != 0:
                        dy = -high
                        if drone.x < inferred_positions[closest_monster_id][0]:
                            dx = -low
                            l = "C"
                        else:
                            dx = low
                            l = "D"
                elif dy > 0:
                    if inferred_positions[closest_monster_id][1] > drone.y:
                        dy = low
                        if drone.x < inferred_positions[closest_monster_id][0]:
                            dx = -high
                            l = "E"
                        else:
                            dx = high
                            l = "F"
                    elif dx != 0:
                        dy = high
                        if drone.x < inferred_positions[closest_monster_id][0]:
                            dx = -low
                            l = "G"
                        else:
                            dx = low
                            l = "H"
            else:
                if dx < 0:
                    if inferred_positions[closest_monster_id][0] < drone.x:
                        dx = -low
                        if drone.y < inferred_positions[closest_monster_id][1]:
                            dy = -high
                            l = "I"
                        else:
                            dy = high
                            l = "J"
                    elif dy != 0:
                        dx = -high
                        if drone.y < inferred_positions[closest_monster_id][1]:
                            dy = -low
                            l = "K"
                        else:
                            dy = low
                            l = "L"
                elif dx > 0:
                    if inferred_positions[closest_monster_id][0] > drone.x:
                        dx = low
                        if drone.y < inferred_positions[closest_monster_id][1]:
                            dy = -high
                            l = "M"
                        else:
                            dy = high
                            l = "N"
                    elif dy != 0:
                        dx = high
                        if drone.y < inferred_positions[closest_monster_id][1]:
                            dy = -low
                            l = "O"
                        else:
                            dy = low
                            l = "P"
            print(f"HERE {low} {high} {dx} {dy} {l}", file=sys.stderr, flush=True)
            tx = round(drone.x+dx)
            ty = round(drone.y+dy)
        
        # Turn on light every 2 turns, in an alternate manner
        if not drone.going_up and drone.y > 2600 and turn%2 == i_drone:
            light = 1
            emojis += "💡"
            drone.last_light = turn
        else:
            light = 0

        print(f"MOVE {tx} {ty} {light} {emojis}")
