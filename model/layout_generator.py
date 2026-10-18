import json
import itertools
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math

# Load room
room_path = Path("/home/user/model/room.json")
room = json.loads(room_path.read_text())

# Nominal values
S = room["dimensions"]["south_wall_total"]["nominal"]  # x max
W = room["dimensions"]["west_wall_total"]["nominal"]  # y max
depth = room["wall_corners"]["depth"]["nominal"]
nw_len = room["wall_corners"]["NW_length_along_west"]["nominal"]
ne_len = room["wall_corners"]["NE_length_along_east"]["nominal"]
e_low_len = room["wall_corners"]["E_lower_length_along_east"]["nominal"]

# Openings nominal
win_w = room["openings"]["window_width"]["nominal"]
door_w = room["openings"]["door_width"]["nominal"]
win_plus_below = room["dimensions"]["window_plus_below"]["nominal"]
north_plus_door = room["dimensions"]["north_plus_door"]["nominal"]
east_below = room["dimensions"]["east_below_door"]["nominal"]
north_to_win = room["dimensions"]["north_to_window_north_edge"]["nominal"]

# Derived positions
# West wall: window from y = east_below? Actually window_plus_below is from south wall to north edge of window
# So window north edge = win_plus_below, south edge = win_plus_below - win_w
win_north = win_plus_below
win_south = win_plus_below - win_w

# East wall: door from y = east_below to east_below+door_w
door_south = east_below
door_north = east_below + door_w

# Corners
corners = [
    (0, W - nw_len, depth, W, "NW"),
    (S - depth, W - ne_len, S, W, "NE"),
    (S - depth, 0, S, e_low_len, "E_low")
]

# Door swing: center at (S, door_north), radius door_w, quadrant SW (west and south)
# Window swing: center at (0, win_north), radius win_w, quadrant SE (east and south)

def rects_overlap(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):
    return not (ax1 <= bx0 or ax0 >= bx1 or ay1 <= by0 or ay0 >= by1)

def check_collision(x, y, w, h, obstacles):
    x1 = x+w
    y1 = y+h
    for ox0, oy0, ox1, oy1, _ in obstacles:
        if rects_overlap(x,y,x1,y1, ox0,oy0,ox1,oy1):
            return True
    return False

# Define furniture candidates generic sizes (cm)
beds = [
    {"name":"80x190 mattress ~85x195 frame", "w":85, "h":195, "mattress":"80x190"},
    {"name":"90x190 mattress ~95x195 frame", "w":95, "h":195, "mattress":"90x190"},
    {"name":"80x200 mattress ~85x205 frame", "w":85, "h":205, "mattress":"80x200"},
    {"name":"90x200 mattress ~95x205 frame", "w":95, "h":205, "mattress":"90x200"},
]

desks = [
    {"name":"120x60 desk", "w":120, "h":60},
    {"name":"140x60 desk", "w":140, "h":60},
    {"name":"140x65 desk", "w":140, "h":65},
]

wardrobes = [
    {"name":"100x60 sliding", "w":100, "h":60, "type":"sliding"},
    {"name":"80x55 sliding", "w":80, "h":55, "type":"sliding"},
    {"name":"90x60 hinged", "w":90, "h":60, "type":"hinged"},
]

# For simplicity, we will test placements along walls (with 1.5 cm skirting offset)
skirting = 1.5

def place_along_south(furn_w, furn_h, offset_x=0):
    # furn_w along x (width), furn_h along y (depth north)
    # placed at y = skirting, x = offset_x+skirting
    return (skirting+offset_x, skirting, furn_w, furn_h)

def place_along_north(furn_w, furn_h, offset_x=0):
    # placed at north wall: y = W - furn_h - skirting
    return (skirting+offset_x, W - furn_h - skirting, furn_w, furn_h)

def place_along_west_below_window(furn_w, furn_h):
    # furn_w along y (north-south), furn_h along x (east)
    # below window: y from skirting to win_south
    # place at x=skirting, y=skirting
    # Need furn_w <= win_south - skirting (wall below window length)
    # For now return x,y,w,h where w is east-west depth, h is north-south length
    # Actually for west wall, furniture depth east is w, length north-south is h
    return (skirting, skirting, furn_h, furn_w)  # w=depth east, h=length north-south

def place_along_east_below_door(furn_w, furn_h):
    # furn_w along y, furn_h along x (depth west)
    # east wall: x = S - furn_h - skirting, y = skirting + offset
    # y range 0- east_below
    return (S - furn_h - skirting, skirting, furn_h, furn_w)

# Try to find 3 distinct layouts manually designed, not brute force all

layouts = []

# Layout A: Bed south wall, Desk north wall, Wardrobe east below door sliding
# Bed south: 80x190 frame 85x195, placed east-west along south wall
# South wall length 218, bed length 195, so offset to avoid E_low corner (which occupies x 208-218, y 0-60)
# If bed depth north 85, its y 0-85 overlaps E_low y 0-60 at x overlap. So need to ensure bed x1 <= S-depth (208) or y1 <= something.
# So place bed with east end at S-depth =208, west end at 208-195=13
# That leaves 13 cm gap west
bedA = {"x": S-depth-195, "y": skirting, "w":195, "h":85, "name":"Bed 80x190 frame 195x85 south", "mattress":"80x190"}
# Check collision with E_low: E_low is x 208-218, y0-60, bed x 13-208, y 0-85, so x overlap? bed x1=208, E_low x0=208 => touching, not overlap if we consider <=, so okay (no overlap)
# Desk north: 140x60, placed along north wall between corners
# North wall between corners 197, desk 140 fits, centered or offset
# Place at x = depth + (197-140)/2 =10 +28.5=38.5
deskA = {"x": depth + (room["dimensions"]["north_wall_between_corners"]["nominal"]-140)/2, "y": W-60-skirting, "w":140, "h":60, "name":"Desk 140x60 north"}
# Wardrobe east below door: 100x60 sliding, placed along east wall below door
# East below door length 157, wardrobe width north-south 100, depth west 60
# Place at y = e_low_len + 5 =65, so y 65-165, x S-60-skirting =218-60-1.5=156.5
wardA = {"x": S-60-skirting, "y": e_low_len+5, "w":60, "h":100, "name":"Wardrobe 100x60 sliding east below door", "type":"sliding"}

layouts.append({"id":"A", "name":"Bed South, Desk North, Wardrobe East", "furniture":[bedA, deskA, wardA]})

# Layout B: Bed North, Desk South-East, Wardrobe West? Let's try
# Bed north: 90x190 frame 95x195, placed along north wall, but rotated: length east-west 195, depth 95 south
bedB = {"x": depth+2, "y": W-95-skirting, "w":195, "h":95, "name":"Bed 90x190 frame 195x95 north", "mattress":"90x190"}
# Desk east below door: 120x60, placed along east wall, but oriented with width north-south 120, depth 60 west
# Place at y = skirting, x = S-60-skirting, y 0-120, but need to avoid E_low corner at y 0-60 x 208-218
# If we place at x 156.5, y 0-120, its x 156.5-216.5, y 0-120 overlaps E_low at x 208-216.5, y 0-60 => collision!
# So shift desk north of E_low: y = e_low_len+5=65 to 185, x same
deskB = {"x": S-60-skirting, "y": e_low_len+5, "w":60, "h":120, "name":"Desk 120x60 east below door (vertical)"}
# Wardrobe west? West below window length is 88 nominal, wardrobe 80x55 sliding could fit below window if low? But wardrobe tall 200 high, under window sill 100 not possible. So wardrobe must be elsewhere, maybe south wall west side
# South wall west side: place wardrobe along south wall? But bed north occupies north, south wall free
# Let's place wardrobe along south wall west of desk? South wall y 0-60 depth, x 0-80 width 80
wardB = {"x": skirting, "y": skirting, "w":80, "h":60, "name":"Wardrobe 80x55 sliding south-west", "type":"sliding"}

# Check collisions: bedB at y 170-265 (W=265, 95 depth => 170-265), deskB at y 65-185, x 156-216, wardrobe at y 0-60, x 0-80 => no overlap between them
layouts.append({"id":"B", "name":"Bed North, Desk East, Wardrobe South-West", "furniture":[bedB, deskB, wardB]})

# Layout C: Bed West? Let's try bed along west wall? But west below window 88 only, not enough for 190 length
# Alternative: Bed along east wall? East below door 157 not enough for 190
# So bed must be north or south. Let's try Bed South 90x200, Desk East, Wardrobe North-West corner L-shaped?
# Bed south 90x200 frame 95x205, placed south
bedC = {"x": S-depth-205, "y": skirting, "w":205, "h":95, "name":"Bed 90x200 frame 205x95 south", "mattress":"90x200"}
# Desk north but smaller 120x60 to leave more clearance
deskC = {"x": depth+10, "y": W-60-skirting, "w":120, "h":60, "name":"Desk 120x60 north-west"}
# Wardrobe east below door 80x55 sliding
wardC = {"x": S-55-skirting, "y": e_low_len+10, "w":55, "h":80, "name":"Wardrobe 80x55 sliding east", "type":"sliding"}

layouts.append({"id":"C", "name":"Bed South 90x200, Desk North-West, Wardrobe East", "furniture":[bedC, deskC, wardC]})

# Function to compute clearances
def clearance_between(rect1, rect2):
    # Minimum distance between rectangles (0 if overlapping)
    x0,y0,w0,h0 = rect1["x"], rect1["y"], rect1["w"], rect1["h"]
    x1 = x0+w0
    y1 = y0+h0
    x2,y2,w2,h2 = rect2["x"], rect2["y"], rect2["w"], rect2["h"]
    x3 = x2+w2
    y3 = y2+h2
    # If overlap, 0
    if not (x1 <= x2 or x0 >= x3 or y1 <= y2 or y0 >= y3):
        return 0
    # Compute horizontal and vertical gaps
    dx = max(0, max(x2 - x1, x0 - x3))
    dy = max(0, max(y2 - y1, y0 - y3))
    if dx>0 and dy>0:
        return math.hypot(dx,dy)
    return max(dx,dy)

def evaluate_layout(layout):
    # Check collisions with corners
    obstacles = corners
    results = []
    for furn in layout["furniture"]:
        coll = check_collision(furn["x"], furn["y"], furn["w"], furn["h"], obstacles)
        results.append((furn["name"], "COLLISION" if coll else "OK"))
    # Check door swing collision (keep-out when door open)
    # Door swing quarter circle: center (S, door_north), radius door_w
    # For simplicity, check if furniture intersects door swing bounding box and distance to center < radius
    # We'll approximate by checking if any corner of furniture within radius and in quadrant
    def in_door_swing(f):
        # Check if furniture overlaps door swing area
        # Door swing area: x in [S-door_w, S], y in [door_south, door_north]
        # And distance from center (S, door_north) <= door_w
        # Check closest point of rect to center
        cx, cy = S, door_north
        rx0, ry0 = f["x"], f["y"]
        rx1, ry1 = f["x"]+f["w"], f["y"]+f["h"]
        # Closest point in rect to center
        closest_x = max(rx0, min(cx, rx1))
        closest_y = max(ry0, min(cy, ry1))
        dist = math.hypot(closest_x-cx, closest_y-cy)
        # Also must be in quadrant: closest_x <= cx and closest_y <= cy
        in_quad = closest_x <= cx and closest_y <= cy
        overlap_box = not (rx1 <= S-door_w or rx0 >= S or ry1 <= door_south or ry0 >= door_north)
        return overlap_box and dist < door_w and in_quad

    def in_window_swing(f):
        # Window swing: center (0, win_north), radius win_w, quadrant x>=0, y<=win_north
        cx, cy = 0, win_north
        rx0, ry0 = f["x"], f["y"]
        rx1, ry1 = f["x"]+f["w"], f["y"]+f["h"]
        closest_x = max(rx0, min(cx, rx1))
        closest_y = max(ry0, min(cy, ry1))
        # Actually center at west wall, furniture east of it, so closest_x is rx0 if rx0>cx
        # For window swing, need to check distance
        # Quadrant: x >=0 and y <= win_north
        # Overlap box: x in [0, win_w], y in [win_south, win_north]
        overlap_box = not (rx1 <= 0 or rx0 >= win_w or ry1 <= win_south or ry0 >= win_north)
        if not overlap_box:
            return False
        # Distance from center to closest point
        dist = math.hypot(closest_x-cx, closest_y-cy)
        in_quad = closest_x >= cx and closest_y <= cy
        return dist < win_w and in_quad

    for furn in layout["furniture"]:
        if in_door_swing(furn):
            results.append((furn["name"]+" door swing", "BLOCKS DOOR"))
        if in_window_swing(furn):
            # If furniture height < sill height, it might be okay, but we don't have height info, assume desk low could be okay
            # For now flag but allow if furniture is desk and low?
            results.append((furn["name"]+" window swing", "IN WINDOW SWING (check height < sill)"))

    # Compute pairwise clearances
    clearances = []
    for i in range(len(layout["furniture"])):
        for j in range(i+1, len(layout["furniture"])):
            f1 = layout["furniture"][i]
            f2 = layout["furniture"][j]
            # Compute gap: if separated horizontally or vertically
            # For simplicity, compute minimal edge distance
            # Horizontal gap
            # ...
            # Use clearance_between
            gap = clearance_between(f1,f2)
            clearances.append((f1["name"]+" vs "+f2["name"], gap))

    return results, clearances

for layout in layouts:
    print(f"\n=== Layout {layout['id']}: {layout['name']} ===")
    res, clears = evaluate_layout(layout)
    for r in res:
        print(r)
    for c in clears:
        print(f"Clearance {c[0]}: {c[1]:.1f} cm")

# Save layouts json
out = Path("/home/user/model/layouts.json")
out.write_text(json.dumps(layouts, indent=2))
print(f"\nSaved {out}")

# Also copy to repo model
import shutil
shutil.copy(out, "/home/user/room001_repo/model/layouts.json")
