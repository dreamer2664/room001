import json, math
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

room = json.loads(Path("/home/user/model/room.json").read_text())

def get_params(case="nominal"):
    # case: nominal, worst, best
    if case=="nominal":
        S = room["dimensions"]["south_wall_total"]["nominal"]
        W = room["dimensions"]["west_wall_total"]["nominal"]
        depth = room["wall_corners"]["depth"]["nominal"]
        nw_len = room["wall_corners"]["NW_length_along_west"]["nominal"]
        ne_len = room["wall_corners"]["NE_length_along_east"]["nominal"]
        e_low_len = room["wall_corners"]["E_lower_length_along_east"]["nominal"]
        win_w = room["openings"]["window_width"]["nominal"]
        door_w = room["openings"]["door_width"]["nominal"]
        win_plus_below = room["dimensions"]["window_plus_below"]["nominal"]
        east_below = room["dimensions"]["east_below_door"]["nominal"]
    elif case=="worst":
        S = room["dimensions"]["south_wall_total"]["min"]
        W = room["dimensions"]["west_wall_total"]["min"]
        depth = room["wall_corners"]["depth"]["max"]
        nw_len = room["wall_corners"]["NW_length_along_west"]["max"]
        ne_len = room["wall_corners"]["NE_length_along_east"]["max"]
        e_low_len = room["wall_corners"]["E_lower_length_along_east"]["max"]
        win_w = room["openings"]["window_width"]["max"]
        door_w = room["openings"]["door_width"]["max"]
        win_plus_below = room["dimensions"]["window_plus_below"]["min"]  # worst small
        east_below = room["dimensions"]["east_below_door"]["min"]
    else: # best
        S = room["dimensions"]["south_wall_total"]["max"]
        W = room["dimensions"]["west_wall_total"]["max"]
        depth = room["wall_corners"]["depth"]["min"]
        nw_len = room["wall_corners"]["NW_length_along_west"]["min"]
        ne_len = room["wall_corners"]["NE_length_along_east"]["min"]
        e_low_len = room["wall_corners"]["E_lower_length_along_east"]["min"]
        win_w = room["openings"]["window_width"]["min"]
        door_w = room["openings"]["door_width"]["min"]
        win_plus_below = room["dimensions"]["window_plus_below"]["max"]
        east_below = room["dimensions"]["east_below_door"]["max"]

    win_north = win_plus_below
    win_south = win_plus_below - win_w
    door_south = east_below
    door_north = east_below + door_w

    corners = [
        (0, W - nw_len, depth, W, "NW"),
        (S - depth, W - ne_len, S, W, "NE"),
        (S - depth, 0, S, e_low_len, "E_low")
    ]
    return {
        "S":S,"W":W,"depth":depth,"nw_len":nw_len,"ne_len":ne_len,"e_low_len":e_low_len,
        "win_w":win_w,"door_w":door_w,"win_plus_below":win_plus_below,"east_below":east_below,
        "win_north":win_north,"win_south":win_south,"door_south":door_south,"door_north":door_north,
        "corners":corners
    }

def check_rect_collision(furn, obstacles):
    x,y,w,h = furn["x"], furn["y"], furn["w"], furn["h"]
    x1,y1 = x+w, y+h
    for ox0,oy0,ox1,oy1,_ in obstacles:
        if not (x1 <= ox0 or x <= ox1 or y1 <= oy0 or y <= oy1):
            # Actually need proper: x1 <= ox0 or x >= ox1 or y1 <= oy0 or y >= oy1 => no overlap
            # Correction
            pass
    # redo
    for ox0,oy0,ox1,oy1,_ in obstacles:
        if not (x+w <= ox0 or x >= ox1 or y+h <= oy0 or y >= oy1):
            return True
    return False

def in_door_swing(furn, params):
    S = params["S"]
    door_north = params["door_north"]
    door_south = params["door_south"]
    door_w = params["door_w"]
    cx, cy = S, door_north
    rx0, ry0 = furn["x"], furn["y"]
    rx1, ry1 = furn["x"]+furn["w"], furn["y"]+furn["h"]
    # Quick bounding box check
    if rx1 <= S-door_w or rx0 >= S or ry1 <= door_south or ry0 > door_north:
        # Might still be in swing if within radius but y below south? Actually swing y range is door_south to door_north
        # If ry1 <= door_south, outside
        # If ry0 > door_north, outside (north of hinge)
        # If rx1 <= S-door_w, outside west
        # If rx0 >= S, outside east
        pass
    else:
        # Check if any part of rect is within quarter circle
        # Closest point in rect to center
        closest_x = max(rx0, min(cx, rx1))
        closest_y = max(ry0, min(cy, ry1))
        # If closest point is outside quadrant (x>cx or y>cy), then not in swing (since quadrant is SW: x<=cx, y<=cy)
        if closest_x > cx or closest_y > cy:
            # But rect could still intersect quarter circle even if closest point outside quadrant? Actually closest point to center inside rect that is in SW quadrant would be...
            # Let's clamp to quadrant: we want point in rect that is closest to center but also in SW quadrant (x<=cx, y<=cy)
            # If rect is north of hinge (ry0 > cy), closest_y = ry0 > cy, so distance will be >0 but y>cy => outside quadrant, so no block
            # If rect is east of hinge (rx0 > cx) impossible since cx=S is east wall max, rect x <=S
            pass
        dist = math.hypot(closest_x-cx, closest_y-cy)
        if closest_x <= cx and closest_y <= cy and dist < door_w - 1e-6:  # - tolerance
            # Check if rect is actually intersecting the swing area, not just touching edge
            # If dist < radius, blocks
            return True
    # Also need to check final open position: door leaf when open 90° occupies line at y=door_north, x from S-door_w to S, with thickness ~4cm
    # If furniture straddles y=door_north and x overlaps, blocks
    thickness = 4
    door_leaf_y0 = door_north - thickness/2
    door_leaf_y1 = door_north + thickness/2
    door_leaf_x0 = S - door_w
    door_leaf_x1 = S
    if not (rx1 <= door_leaf_x0 or rx0 >= door_leaf_x1 or ry1 <= door_leaf_y0 or ry0 >= door_leaf_y1):
        return True
    return False

def in_window_swing(furn, params):
    win_north = params["win_north"]
    win_south = params["win_south"]
    win_w = params["win_w"]
    cx, cy = 0, win_north
    rx0, ry0 = furn["x"], furn["y"]
    rx1, ry1 = furn["x"]+furn["w"], furn["y"]+furn["h"]
    # Bounding box of window swing: x 0..win_w, y win_south..win_north
    if rx1 <= 0 or rx0 >= win_w or ry1 <= win_south or ry0 >= win_north:
        return False
    closest_x = max(rx0, min(cx, rx1))
    closest_y = max(ry0, min(cy, ry1))
    # Quadrant SE: x>=cx, y<=cy
    if closest_x < cx or closest_y > cy:
        return False
    dist = math.hypot(closest_x-cx, closest_y-cy)
    return dist < win_w - 1e-6

def clearance(f1,f2):
    x0,y0,w0,h0 = f1["x"], f1["y"], f1["w"], f1["h"]
    x1,y1 = x0+w0, y0+h0
    x2,y2,w2,h2 = f2["x"], f2["y"], f2["w"], f2["h"]
    x3,y3 = x2+w2, y2+h2
    if not (x1 <= x2 or x0 >= x3 or y1 <= y2 or y0 >= y3):
        return 0
    dx = max(0, max(x2 - x1, x0 - x3))
    dy = max(0, max(y2 - y1, y0 - y3))
    if dx>0 and dy>0:
        return math.hypot(dx,dy)
    return max(dx,dy)

# Define improved layouts that clear door swing

layouts = []

# Layout A improved: Bed South, Desk North-West (west of door swing), Wardrobe East below door but low north edge <= door_south
# Nominal params for design
p_nom = get_params("nominal")
S = p_nom["S"]; W = p_nom["W"]; depth = p_nom["depth"]; e_low_len = p_nom["e_low_len"]
# Bed south: 85x195 (80x190 mattress)
bedA = {"x": S-depth-195, "y": 1.5, "w":195, "h":85, "name":"Bed 80x190 (195x85) South", "type":"bed"}
# Desk north-west: 140x60, placed west of door swing clear zone (east edge <= S-door_w)
# S-door_w nominal = 218-80=138, so east edge <=138, so x + w <=138
# Choose x=10, w=120 => east edge 130 <=138 ok
deskA = {"x": 10, "y": W-60-1.5, "w":120, "h":60, "name":"Desk 120x60 North-West", "type":"desk"}
# Wardrobe east below door: 80x55 sliding, placed below door_south
# door_south nominal 157, so wardrobe north edge <=157 to clear door swing
# Place at y=0-80, x= S-55-1.5=161.5
wardA = {"x": S-55-1.5, "y": 1.5, "w":55, "h":80, "name":"Wardrobe 80x55 sliding East below door", "type":"wardrobe"}

layouts.append({"id":"A", "name":"Bed South 80x190, Desk North-West 120, Wardrobe East 80 sliding - door clear", "furniture":[bedA, deskA, wardA]})

# Layout B: Bed North, Desk East (below door but clear), Wardrobe South-West
# Bed north: 95x195 (90x190)
bedB = {"x": depth+2, "y": W-95-1.5, "w":195, "h":95, "name":"Bed 90x190 (195x95) North", "type":"bed"}
# Desk east below door: 120x60 vertical (w=60 depth west, h=120 north-south)
# Must have north edge <= door_south to clear door swing, so y+h <= door_south
# door_south 157, so y=0, h=120 => north edge 120 <=157 ok, clears
deskB = {"x": S-60-1.5, "y": 1.5, "w":60, "h":120, "name":"Desk 120x60 East vertical below door", "type":"desk"}
# Wardrobe south-west: 100x60 sliding, placed south wall west side, x=0-100, y=0-60
wardB = {"x": 1.5, "y": 1.5, "w":100, "h":60, "name":"Wardrobe 100x60 sliding South-West", "type":"wardrobe"}
# But wardrobe south-west at same y as desk? Desk at x 156-216, y 0-120, wardrobe at x 0-100, y 0-60 => no overlap

layouts.append({"id":"B", "name":"Bed North 90x190, Desk East vertical 120, Wardrobe South-West 100", "furniture":[bedB, deskB, wardB]})

# Layout C: Bed South 90x200, Desk North-West 140, Wardrobe East 80 but with chair clearance
bedC = {"x": S-depth-205, "y": 1.5, "w":205, "h":95, "name":"Bed 90x200 (205x95) South", "type":"bed"}
deskC = {"x": 10, "y": W-60-1.5, "w":140, "h":60, "name":"Desk 140x60 North-West", "type":"desk"}
wardC = {"x": S-55-1.5, "y": 1.5, "w":55, "h":80, "name":"Wardrobe 80x55 East", "type":"wardrobe"}

layouts.append({"id":"C", "name":"Bed South 90x200, Desk North-West 140, Wardrobe East 80", "furniture":[bedC, deskC, wardC]})

# Evaluate each layout for nominal, worst, best
for case in ["nominal","worst","best"]:
    params = get_params(case)
    print(f"\n{'='*20} CASE {case} S={params['S']} W={params['W']} door={params['door_w']} win={params['win_w']} {'='*20}")
    for layout in layouts:
        print(f"\nLayout {layout['id']} {layout['name']}")
        ok = True
        for furn in layout["furniture"]:
            coll = check_rect_collision(furn, params["corners"])
            door_block = in_door_swing(furn, params)
            win_block = in_window_swing(furn, params)
            status = []
            if coll:
                status.append("COLLIDES CORNER")
                ok=False
            if door_block:
                status.append("BLOCKS DOOR")
                ok=False
            if win_block:
                # If furniture is low (< sill), window swing may be above, allow for desk? But for bed and wardrobe tall, block
                # For now flag
                if furn["type"] in ["bed","wardrobe"]:
                    status.append("BLOCKS WINDOW (tall)")
                    ok=False
                else:
                    status.append("IN WINDOW SWING (low furniture may be OK if < sill)")
            if not status:
                status=["OK"]
            print(f"  {furn['name']}: {', '.join(status)}")
        # Clearances
        furns = layout["furniture"]
        for i in range(len(furns)):
            for j in range(i+1, len(furns)):
                gap = clearance(furns[i], furns[j])
                color = "RED <60" if gap<60 else "AMBER 60-70" if gap<70 else "GREEN 70+"
                print(f"    Clearance {furns[i]['name']} vs {furns[j]['name']}: {gap:.1f} cm {color}")
        print(f"  Overall {'PASS' if ok else 'FAIL'} for {case}")

# Save
import json, pathlib
pathlib.Path("/home/user/model/layouts_refined.json").write_text(json.dumps(layouts, indent=2))
