import sys
import math
import copy

# Score points by scanning valuable fish faster than your opponent.

colors = {}
types = {}
positions = {}
speeds = {}
directions = {}
scans = set()
saved_scans = set()
foe_saved_scans = set()
last_light = -math.inf

creature_count = int(input())
for i in range(creature_count):
    creature_id, color, ty = [int(j) for j in input().split()]
    colors[creature_id] = color
    types[creature_id] = ty

# game loop
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
    foe_drone_count = int(input())
    for i in range(foe_drone_count):
        foe_drone_id, foe_drone_x, foe_drone_y, foe_emergency, foe_battery = [int(j) for j in input().split()]
    drone_scan_count = int(input())
    for i in range(drone_scan_count):
        drone_id, creature_id = [int(j) for j in input().split()]
    visible_creature_count = int(input())
    for i in range(visible_creature_count):
        creature_id, creature_x, creature_y, creature_vx, creature_vy = [int(j) for j in input().split()]
        positions[creature_id] = creature_x, creature_y
        speeds[creature_id] = creature_vx, creature_vy
    radar_blip_count = int(input())
    for i in range(radar_blip_count):
        inputs = input().split()
        drone_id = int(inputs[0])
        creature_id = int(inputs[1])
        radar = inputs[2]
        directions[creature_id] = radar

    turn = 0
    for i in range(my_drone_count):
        turn += 1

        # Retain positions from unscanned poissons
        unscanned_positions = copy.deepcopy(positions)
        for creature_id in scans:
            try:
                unscanned_positions.pop(creature_id)
            except:
                pass
        
        # Compute their distances
        distances = {}
        for creature_id in unscanned_positions.keys():
            x, y = unscanned_positions[creature_id]
            dx = x - drone_x
            dy = y - drone_y
            dist = math.sqrt(dx**2 + dy**2)
            if dist < 800:
                scans.add(creature_id)
            else:
                distances[creature_id] = dist
        print(f"{distances}\n{scans}", file=sys.stderr, flush=True)
        
        # Get the closest
        closest_dist = 10000
        closest_creature_id = 0
        for creature_id in distances.keys():
            distance = distances[creature_id]
            if distance < closest_dist:
                print(f"{distance} < {closest_dist} ({creature_id})", file=sys.stderr, flush=True)
                closest_dist = distance
                closest_creature_id = creature_id

        # If there is no closest, get to new fishes
        if closest_creature_id == 0:
            if turn - last_light > 4:
                light = 1
                last_light = turn
            else:
                light = 0
            sum_x = 0
            sum_y = 0
            count = 0
            for creature_id in directions:
                if creature_id in scans:
                    continue
                direction = directions[creature_id]
                count += 1
                match direction:
                    case "TL":
                        sum_x -= 1
                        sum_y -= 1
                    case "TR":
                        sum_y += 1
                        sum_y -= 1
                    case "BL":
                        sum_x -= 1
                        sum_y += 1
                    case "BR":
                        sum_x += 1
                        sum_y += 1
                    case _:
                        print("panic")
            mx = sum_x / count
            my = sum_y / count
            if mx == 0 and my == 0:
                print("No fish! Fish all around! Waiting", file=sys.stderr, flush=True)
                print("WAIT 1")
                continue
            mx_ratio = mx / (abs(mx)+abs(my))
            my_ratio = my / (abs(mx)+abs(my))
            mx = math.floor(600*mx_ratio)
            my = math.floor(600*my_ratio)
            ex = drone_x+mx
            ey = drone_y+my
            print(f"No fish! Driven by {sum_x},{sum_y} over {count} -> {ex} {ey}", file=sys.stderr, flush=True)
            print(f"MOVE {ex} {ey} 1")
            continue

        # Get to the target
        tx, ty = positions[closest_creature_id]

        if closest_dist > 600 and closest_dist <= 2000 and battery > 5:
            light = 1
            last_light = turn
        else:
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
