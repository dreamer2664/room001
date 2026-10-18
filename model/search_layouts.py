import math, itertools
from pathlib import Path
import json

room=json.loads(Path("/home/user/model/room.json").read_text())

def get_params(case):
    if case=="nominal":
        S=218;W=265;depth=10;nw_len=40;ne_len=26;e_low_len=60;win_w=80;door_w=80;win_plus_below=168;east_below=157
    elif case=="worst":
        S=211;W=264;depth=12;nw_len=45;ne_len=32;e_low_len=70;win_w=95;door_w=90;win_plus_below=166;east_below=156
    else:
        S=219;W=266;depth=8;nw_len=35;ne_len=20;e_low_len=50;win_w=70;door_w=70;win_plus_below=170;east_below=158
    win_north=win_plus_below
    win_south=win_plus_below-win_w
    door_south=east_below
    door_north=east_below+door_w
    corners=[
        (0, W - nw_len, depth, W, "NW"),
        (S - depth, W - ne_len, S, W, "NE"),
        (S - depth, 0, S, e_low_len, "E_low")
    ]
    return {"S":S,"W":W,"depth":depth,"nw_len":nw_len,"ne_len":ne_len,"e_low_len":e_low_len,
            "win_w":win_w,"door_w":door_w,"win_plus_below":win_plus_below,"east_below":east_below,
            "win_north":win_north,"win_south":win_south,"door_south":door_south,"door_north":door_north,
            "corners":corners}

def rect_overlap(ax,ay,aw,ah,bx0,by0,bx1,by1):
    return not (ax+aw <= bx0 or ax >= bx1 or ay+ah <= by0 or ay >= by1)

def collides(furn, corners):
    for ox0,oy0,ox1,oy1,_ in corners:
        if rect_overlap(furn["x"],furn["y"],furn["w"],furn["h"],ox0,oy0,ox1,oy1):
            return True
    return False

def in_door_swing(furn, p):
    S=p["S"]; door_north=p["door_north"]; door_south=p["door_south"]; door_w=p["door_w"]
    cx,cy=S,door_north
    rx0,ry0=furn["x"],furn["y"]; rx1,ry1=rx0+furn["w"],ry0+furn["h"]
    # check final leaf
    thickness=4
    leaf_y0=door_north-thickness/2
    leaf_y1=door_north+thickness/2
    leaf_x0=S-door_w
    leaf_x1=S
    if not (rx1 <= leaf_x0 or rx0 >= leaf_x1 or ry1 <= leaf_y0 or ry0 >= leaf_y1):
        return True
    # quarter circle
    # bounding box of swing
    if rx1 <= S-door_w or rx0 >= S or ry1 <= door_south or ry0 > door_north:
        return False
    closest_x=max(rx0,min(cx,rx1))
    closest_y=max(ry0,min(cy,ry1))
    if closest_x > cx or closest_y > cy:
        return False
    dist=math.hypot(closest_x-cx, closest_y-cy)
    return dist < door_w - 0.1

def in_window_swing(furn, p, allow_low=False, sill_height=100):
    # if allow_low and furn height < sill, we consider it okay even if in swing (window above)
    # For now, we need to know furniture type: if low (< sill), allow
    win_north=p["win_north"]; win_south=p["win_south"]; win_w=p["win_w"]
    cx,cy=0,win_north
    rx0,ry0=furn["x"],furn["y"]; rx1,ry1=rx0+furn["w"],ry0+furn["h"]
    if rx1 <= 0 or rx0 >= win_w or ry1 <= win_south or ry0 >= win_north:
        return False
    closest_x=max(rx0,min(cx,rx1))
    closest_y=max(ry0,min(cy,ry1))
    if closest_x < cx or closest_y > cy:
        return False
    dist=math.hypot(closest_x-cx, closest_y-cy)
    return dist < win_w -0.1

def clearance(f1,f2):
    x0,y0,w0,h0=f1["x"],f1["y"],f1["w"],f1["h"]
    x1,y1=x0+w0,y0+h0
    x2,y2,w2,h2=f2["x"],f2["y"],f2["w"],f2["h"]
    x3,y3=x2+w2,y2+h2
    if not (x1 <= x2 or x0 >= x3 or y1 <= y2 or y0 >= y3):
        return 0
    dx=max(0, max(x2-x1, x0-x3))
    dy=max(0, max(y2-y1, y0-y3))
    if dx>0 and dy>0:
        return math.hypot(dx,dy)
    return max(dx,dy)

# Furniture sizes to test (w along x, h along y)
beds=[(195,85,"80x190"),(195,95,"90x190"),(205,85,"80x200"),(205,95,"90x200")]
desks=[(120,60),(140,60),(120,50)]
wards=[(60,80,"80x55 sliding"),(60,100,"100x60 sliding"),(55,80,"80x55")]

# Search for layouts that work for worst case
p_worst=get_params("worst")
p_nom=get_params("nominal")

skirting=1.5
step=5

def generate_positions(S,W,w,h,step=5):
    # generate positions along walls with skirting offset
    positions=[]
    # South wall: y=skirting, x from skirting to S-depth-w
    # But need to avoid E_low corner: if y < e_low_len, x must be <= S-depth-w - overlap? Actually we will check collision later
    for x in range(int(skirting), int(S - w - skirting)+1, step):
        y=skirting
        positions.append((x,y))
    # North wall: y=W-h-skirting, x from depth to S-depth-w
    for x in range(int(p_worst["depth"]+skirting), int(S - p_worst["depth"] - w - skirting)+1, step):
        y=W-h-skirting
        positions.append((x,y))
    # West wall below window? West wall: x=skirting, y from skirting to win_south - h
    # Actually west wall furniture oriented with depth east = w, length north-south = h, so x=skirting, y variable
    # We'll also generate for west wall: x=skirting, y from skirting to win_south - h (if h <= win_south)
    # East wall below door: x=S-w-skirting, y from e_low_len to door_south - h
    # We'll generate separately
    return positions

# For simplicity, we will manually try to find 3 good layouts by heuristic, not exhaustive

# Layout attempt 1: Bed South, Desk North (but west enough to clear door), Wardrobe East above E_low
# Bed South: place at x = S-depth - bed_w, y=skirting
# For worst S=211, depth=12, bed_w=195 => x=211-12-195=4, y=1.5
# Check door swing: bed y 1.5-86.5, door_south 156, so below, safe if distance > door_w
# Distance from hinge (211,246) to bed NE corner (199,86.5) = sqrt((12)^2+(159.5)^2)=160 >90 safe
# Desk North: need to place west of door swing: x + w <= S-door_w =121 worst
# So max w=120, x=0? But NW corner occupies x 0-12, so x must be >=12+skirting=13.5
# So x=13.5, w=100 => east edge 113.5 <=121 safe
# Let's try desk 100x60 north
# Wardrobe East: place at x=S-w-skirting, y=e_low_len+5
# For worst, e_low_len=70, so y=75, w=55 depth west, h=80 north-south, x=211-55-1.5=154.5, y=75-155
# Check door swing: distance from hinge (211,246) to wardrobe NE (209.5,155) = sqrt(1.5^2+91^2)=91.0 >90 safe (just barely)
# Good

# Let's evaluate this layout for worst and nominal
def eval_layout(furn_list, p):
    for f in furn_list:
        if collides(f, p["corners"]):
            return False, f"collides {f['name']}"
        if in_door_swing(f, p):
            return False, f"door blocks {f['name']}"
        # window swing only for tall furniture
        if f.get("type") in ["bed","wardrobe"] and in_window_swing(f,p):
            return False, f"window blocks {f['name']}"
    # check pairwise overlap
    for i in range(len(furn_list)):
        for j in range(i+1,len(furn_list)):
            if rect_overlap(furn_list[i]["x"],furn_list[i]["y"],furn_list[i]["w"],furn_list[i]["h"],
                            furn_list[j]["x"],furn_list[j]["y"],furn_list[j]["x"]+furn_list[j]["w"],furn_list[j]["y"]+furn_list[j]["h"]):
                return False, f"overlap {furn_list[i]['name']} vs {furn_list[j]['name']}"
    return True, "ok"

# Layout A
p=p_worst
bedA={"x":p["S"]-p["depth"]-195,"y":skirting,"w":195,"h":85,"name":"Bed 80x190 South","type":"bed"}
deskA={"x":p["depth"]+skirting,"y":p["W"]-60-skirting,"w":100,"h":60,"name":"Desk 100x60 North","type":"desk"}
wardA={"x":p["S"]-55-skirting,"y":p["e_low_len"]+5,"w":55,"h":80,"name":"Ward 80x55 East","type":"wardrobe"}
print("Layout A worst", eval_layout([bedA,deskA,wardA], p))
p2=get_params("nominal")
bedA_nom={"x":p2["S"]-p2["depth"]-195,"y":skirting,"w":195,"h":85,"name":"Bed 80x190 South","type":"bed"}
deskA_nom={"x":p2["depth"]+skirting,"y":p2["W"]-60-skirting,"w":100,"h":60,"name":"Desk 100x60 North","type":"desk"}
wardA_nom={"x":p2["S"]-55-skirting,"y":p2["e_low_len"]+5,"w":55,"h":80,"name":"Ward 80x55 East","type":"wardrobe"}
print("Layout A nominal", eval_layout([bedA_nom,deskA_nom,wardA_nom], p2))
for f1,f2 in [(bedA_nom,deskA_nom),(bedA_nom,wardA_nom),(deskA_nom,wardA_nom)]:
    print(f" clearance {f1['name']} vs {f2['name']} {clearance(f1,f2):.1f}")

# Layout B: Bed North, Desk South-West, Wardrobe East
bedB={"x":p["depth"]+skirting,"y":p["W"]-95-skirting,"w":195,"h":95,"name":"Bed 90x190 North","type":"bed"}
# Desk south-west: x=skirting, y=skirting, w=120,h=60
deskB={"x":skirting,"y":skirting,"w":120,"h":60,"name":"Desk 120x60 South","type":"desk"}
wardB={"x":p["S"]-55-skirting,"y":p["e_low_len"]+5,"w":55,"h":80,"name":"Ward East","type":"wardrobe"}
print("\nLayout B worst", eval_layout([bedB,deskB,wardB], p))
bedB_nom={"x":p2["depth"]+skirting,"y":p2["W"]-95-skirting,"w":195,"h":95,"name":"Bed North","type":"bed"}
deskB_nom={"x":skirting,"y":skirting,"w":120,"h":60,"name":"Desk South","type":"desk"}
wardB_nom={"x":p2["S"]-55-skirting,"y":p2["e_low_len"]+5,"w":55,"h":80,"name":"Ward East","type":"wardrobe"}
print("Layout B nominal", eval_layout([bedB_nom,deskB_nom,wardB_nom], p2))
for f1,f2 in [(bedB_nom,deskB_nom),(bedB_nom,wardB_nom),(deskB_nom,wardB_nom)]:
    print(f" clearance {f1['name']} vs {f2['name']} {clearance(f1,f2):.1f}")

# Layout C: Bed South 90x200, Desk East vertical below door, Wardrobe North-West small
bedC={"x":p["S"]-p["depth"]-205,"y":skirting,"w":205,"h":95,"name":"Bed 90x200 South","type":"bed"}
# Desk east vertical: w=60 depth west, h=120 north-south, x=S-60-skirting, y=e_low_len+5
deskC={"x":p["S"]-60-skirting,"y":p["e_low_len"]+5,"w":60,"h":120,"name":"Desk East vertical","type":"desk"}
# Wardrobe north-west: place north wall but west, w=80,h=60, x=depth+skirting, y=W-60-skirting, but need to avoid bed? Bed south, so north is free
wardC={"x":p["depth"]+skirting,"y":p["W"]-60-skirting,"w":80,"h":60,"name":"Ward North-West","type":"wardrobe"}
print("\nLayout C worst", eval_layout([bedC,deskC,wardC], p))
bedC_nom={"x":p2["S"]-p2["depth"]-205,"y":skirting,"w":205,"h":95,"name":"Bed South","type":"bed"}
deskC_nom={"x":p2["S"]-60-skirting,"y":p2["e_low_len"]+5,"w":60,"h":120,"name":"Desk East","type":"desk"}
wardC_nom={"x":p2["depth"]+skirting,"y":p2["W"]-60-skirting,"w":80,"h":60,"name":"Ward North","type":"wardrobe"}
print("Layout C nominal", eval_layout([bedC_nom,deskC_nom,wardC_nom], p2))
for f1,f2 in [(bedC_nom,deskC_nom),(bedC_nom,wardC_nom),(deskC_nom,wardC_nom)]:
    print(f" clearance {f1['name']} vs {f2['name']} {clearance(f1,f2):.1f}")
