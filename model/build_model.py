import json
from pathlib import Path

# Define room parameters in cm, with tags and ranges
# Tags: MEASURED, READ-FROM-SKETCH, ESTIMATED, UNKNOWN

def param(nominal, min_val, max_val, tag, note=""):
    return {
        "nominal": nominal,
        "min": min_val,
        "max": max_val,
        "tag": tag,
        "note": note,
        "unit": "cm"
    }

room = {
    "meta": {
        "orientation": "N = top of plan",
        "origin": "SW interior corner (0,0), x east, y north, units cm",
        "date": "2026-10-18"
    },
    "dimensions": {
        "south_wall_total": param(218, 211, 219, "READ-FROM-SKETCH", "Could be 2.12 misread; +-1 cm; testing 211-219"),
        "north_wall_between_corners": param(197, 196, 198, "READ-FROM-SKETCH", "+-1 cm"),
        "west_wall_total": param(265, 264, 266, "READ-FROM-SKETCH", "+-1 cm"),
        "north_to_window_north_edge": param(97, 96, 98, "READ-FROM-SKETCH", "From north wall interior to window north jamb"),
        "east_below_door": param(157, 156, 158, "READ-FROM-SKETCH", "Wall below door on east wall"),
        # Derived
        "window_plus_below": {
            "nominal": 168,
            "min": 166,  # 264-98
            "max": 170,  # 266-96
            "tag": "DERIVED",
            "formula": "west_wall_total - north_to_window_north_edge",
            "unit": "cm"
        },
        "north_plus_door": {
            "nominal": 108,
            "min": 106,  # 264-158
            "max": 110,  # 266-156
            "tag": "DERIVED",
            "formula": "west_wall_total - east_below_door",
            "unit": "cm"
        }
    },
    "openings": {
        "window_width": param(80, 70, 95, "ESTIMATED", "Range 0.70-0.95, single-leaf tilt-and-turn, hinged NORTH, inward swing radius = leaf width ~70-75 but use opening width for worst case"),
        "window_swing_radius": param(75, 70, 95, "ESTIMATED", "Approx equal to window width, but test 70-95"),
        "window_sill_height": param(100, 90, 110, "ESTIMATED", "90-110 cm"),
        "window_recess_depth": param(10, 5, 15, "ESTIMATED", "Wall below window recessed, depth unknown 5-15"),
        "door_width": param(80, 70, 90, "ESTIMATED", "Range 0.70-0.90, inward, hinged NORTH jamb"),
        "door_swing_radius": param(80, 70, 90, "ESTIMATED", "Equal to door width"),
        "wall_below_window": {
            "nominal": 88,  # 168-80
            "min": 71,  # 166-95
            "max": 100,  # 170-70
            "tag": "DERIVED",
            "formula": "window_plus_below - window_width",
            "unit": "cm"
        },
        "north_corner_length_east_wall": {
            "nominal": 28,  # 108-80
            "min": 16,  # 106-90
            "max": 40,  # 110-70
            "tag": "DERIVED",
            "formula": "north_plus_door - door_width",
            "unit": "cm",
            "note": "This should match NE corner length estimate ~26 cm; derived range 16-40 overlaps, good consistency check"
        }
    },
    "wall_corners": {
        "depth": param(10, 8, 12, "ESTIMATED", "Protrusion into room"),
        "NW_length_along_west": param(40, 35, 45, "ESTIMATED", "By eye 40 cm"),
        "NE_length_along_east": param(26, 20, 32, "ESTIMATED", "By eye 26 cm, should align with north_corner_length_east_wall"),
        "E_lower_length_along_east": param(60, 50, 70, "ESTIMATED", "By eye 60 cm, east wall lower part"),
        # Width along north wall (east-west) is same as depth (10)
        "NW_width_along_north": param(10, 8, 12, "ESTIMATED", "Same as depth"),
        "NE_width_along_north": param(10, 8, 12, "ESTIMATED", "Same as depth"),
        "E_lower_width_along_south_north": param(10, 8, 12, "ESTIMATED", "Protrusion west from east wall")
    },
    "other": {
        "ceiling_height": param(270, 260, 290, "ESTIMATED", "2.60-2.90, do NOT propose loft >2.60"),
        "floor_tile_size": param(40, 33, 45, "ESTIMATED", "Diagonal tiles 40x40, could be 33 or 45"),
        "skirting_height": param(9, 8, 10, "ESTIMATED", "8-10 cm high"),
        "skirting_thickness": param(1.2, 1.0, 1.5, "ESTIMATED", "1-1.5 cm thick"),
        "socket_height": param(30, 25, 35, "ESTIMATED", "West wall near SW corner ~30 cm above floor"),
        "socket_distance_from_SW": param(35, 30, 40, "ESTIMATED", "30-40 cm from SW corner along west wall"),
        "damp_zone": {
            "location": "base of west wall near SW corner and centre",
            "avoid_wood": True,
            "tag": "ESTIMATED"
        }
    },
    "delivery": {
        "address": "UNKNOWN",
        "assumption": "mainland Italy, standard home delivery",
        "access_path": "UNKNOWN, assume standard 80 cm doors, normal stairwell",
        "tag": "UNKNOWN"
    },
    "worst_case_rules": {
        "must_fit_use": "unfavourable end: smaller room (min S, min W), wider swings (max window, max door), deeper corners (max depth, max lengths), lower ceiling (min)",
        "best_case": "opposite: larger room, smaller swings, shallower corners, higher ceiling"
    }
}

# Compute free floor area nominal and worst/best
def compute_area(south, west, corners):
    # corners: list of (x0,y0,x1,y1) rectangles
    total = south * west
    corner_area = sum((x1-x0)*(y1-y0) for x0,y0,x1,y1 in corners)
    return total - corner_area

# Nominal corners
south_nom = room["dimensions"]["south_wall_total"]["nominal"]
west_nom = room["dimensions"]["west_wall_total"]["nominal"]
depth_nom = room["wall_corners"]["depth"]["nominal"]
nw_len_nom = room["wall_corners"]["NW_length_along_west"]["nominal"]
ne_len_nom = room["wall_corners"]["NE_length_along_east"]["nominal"]
e_low_len_nom = room["wall_corners"]["E_lower_length_along_east"]["nominal"]

corners_nom = [
    (0, west_nom - nw_len_nom, depth_nom, west_nom),  # NW
    (south_nom - depth_nom, west_nom - ne_len_nom, south_nom, west_nom),  # NE
    (south_nom - depth_nom, 0, south_nom, e_low_len_nom)  # E lower
]

free_nom = compute_area(south_nom, west_nom, corners_nom)

# Worst case: min room, max corners
south_min = room["dimensions"]["south_wall_total"]["min"]
west_min = room["dimensions"]["west_wall_total"]["min"]
depth_max = room["wall_corners"]["depth"]["max"]
nw_len_max = room["wall_corners"]["NW_length_along_west"]["max"]
ne_len_max = room["wall_corners"]["NE_length_along_east"]["max"]
e_low_len_max = room["wall_corners"]["E_lower_length_along_east"]["max"]

corners_worst = [
    (0, west_min - nw_len_max, depth_max, west_min),
    (south_min - depth_max, west_min - ne_len_max, south_min, west_min),
    (south_min - depth_max, 0, south_min, e_low_len_max)
]
free_worst = compute_area(south_min, west_min, corners_worst)

# Best case
south_max = room["dimensions"]["south_wall_total"]["max"]
west_max = room["dimensions"]["west_wall_total"]["max"]
depth_min = room["wall_corners"]["depth"]["min"]
nw_len_min = room["wall_corners"]["NW_length_along_west"]["min"]
ne_len_min = room["wall_corners"]["NE_length_along_east"]["min"]
e_low_len_min = room["wall_corners"]["E_lower_length_along_east"]["min"]

corners_best = [
    (0, west_max - nw_len_min, depth_min, west_max),
    (south_max - depth_min, west_max - ne_len_min, south_max, west_max),
    (south_max - depth_min, 0, south_max, e_low_len_min)
]
free_best = compute_area(south_max, west_max, corners_best)

room["computed"] = {
    "free_floor_area_cm2": {
        "nominal": free_nom,
        "worst": free_worst,
        "best": free_best
    },
    "free_floor_area_m2": {
        "nominal": round(free_nom/10000, 3),
        "worst": round(free_worst/10000, 3),
        "best": round(free_best/10000, 3)
    },
    "usable_wall_lengths": {
        "south_wall": {
            "nominal": south_nom,
            "note": "Full length, but skirting and socket/damp near SW"
        },
        "west_wall_below_window": {
            "nominal": room["openings"]["wall_below_window"]["nominal"],
            "min": room["openings"]["wall_below_window"]["min"],
            "max": room["openings"]["wall_below_window"]["max"],
            "note": "From south wall to window south edge"
        },
        "west_wall_gap_NW_to_window": {
            "nominal": room["dimensions"]["north_to_window_north_edge"]["nominal"] - room["wall_corners"]["NW_length_along_west"]["nominal"],
            "min": room["dimensions"]["north_to_window_north_edge"]["min"] - room["wall_corners"]["NW_length_along_west"]["max"],
            "max": room["dimensions"]["north_to_window_north_edge"]["max"] - room["wall_corners"]["NW_length_along_west"]["min"],
            "note": "Gap between NW corner south face and window north edge"
        },
        "east_wall_below_door": {
            "nominal": room["dimensions"]["east_below_door"]["nominal"],
            "min": room["dimensions"]["east_below_door"]["min"],
            "max": room["dimensions"]["east_below_door"]["max"]
        }
    },
    "consistency_checks": [
        f"North wall between corners 197 vs computed 10+208=218? Computed total north width = south total = {south_nom}, between = {south_nom - depth_nom - depth_nom} = {south_nom - 2*depth_nom}, nominal 197 => diff {south_nom - 2*depth_nom - 197}",
        f"NE corner length derived {room['openings']['north_corner_length_east_wall']['nominal']} vs estimated {ne_len_nom} => diff {room['openings']['north_corner_length_east_wall']['nominal'] - ne_len_nom}",
        f"West wall total {west_nom} = north_to_window {room['dimensions']['north_to_window_north_edge']['nominal']} + window_plus_below {room['dimensions']['window_plus_below']['nominal']} => {room['dimensions']['north_to_window_north_edge']['nominal'] + room['dimensions']['window_plus_below']['nominal']}",
        f"East wall total {west_nom} = east_below_door {room['dimensions']['east_below_door']['nominal']} + north_plus_door {room['dimensions']['north_plus_door']['nominal']} => {room['dimensions']['east_below_door']['nominal'] + room['dimensions']['north_plus_door']['nominal']}"
    ]
}

out_path = Path("/home/user/model/room.json")
out_path.write_text(json.dumps(room, indent=2))
print(f"Wrote {out_path}")
print(json.dumps(room["computed"], indent=2))

# Also copy to repo
import shutil
shutil.copy(out_path, "/home/user/room001_repo/model/room.json")
