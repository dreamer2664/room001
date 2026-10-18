# LOG - Running journal of every decision and assumption

## 2026-10-18 Start
- Saved attachments in /home/user/inputs with SHA256 hashes (see inputs/hashes.txt and inputs/README.md)
- Repo dreamer2664/room001 checked: PRIVATE=False (public) via GitHub API. Per security rules, photos NOT committed to repo, kept in local sandbox only.
- Created branch research-run-1
- Built parametric room model in cm with tags MEASURED/READ-FROM-SKETCH/ESTIMATED/UNKNOWN
  - South wall total READ-FROM-SKETCH 218 nominal, min 211 max 219 (could be 2.12 misread)
  - North between corners 197 nominal 196-198
  - West total 265 nominal 264-266
  - North to window 97 nominal 96-98
  - East below door 157 nominal 156-158
  - Derived window+below 168 nominal 166-170, north+door 108 nominal 106-110
  - Window width EST 80 min70 max95, door 80 min70 max90
  - Wall corners depth EST 10 min8 max12, lengths NW 40 (35-45), NE 26 (20-32), E_low 60 (50-70)
  - Ceiling 270 (260-290), tile 40 (33-45), skirting 9 (8-10) height, 1.2 (1.0-1.5) thickness, socket 30 high 35 from SW
  - Computed free floor area nominal 5.651 m2, worst 5.394, best 5.741
  - Consistency checks: north between corners computed 198 vs nominal 197 diff 1 within tolerance, NE corner derived 28 vs estimated 26 diff 2 OK, totals match 265

## Spatial analysis
- Built Python model with shapely, matplotlib, Pillow, OpenCV
- Defined keep-out zones: door swing quarter circle centered at (S, door_north) radius door_w, window swing centered at (0, win_north) radius win_w
- Defined wall corners as obstacles
- Brute force search for bed positions:
  - Nominal: 80x190 (195x85 frame) 52 valid positions if low furniture allowed in window swing (height < sill-10), 90x190 42 valid, 80x200 21 valid, 90x200 15 valid
  - Worst: 80x190 18 valid, 90x190 13 valid, 80x200 2 valid, 90x200 0 valid -> 90x200 fails worst case
  - If strict (no low in window), nominal only 80x190 and 80x200 have 3 and 1 positions, worst 0 positions for all -> no standard bed fits worst strict
- Conclusion: worst case fails for standard beds if we require horizontal clearance from window swing even for low furniture. If we allow low furniture (bed height 50 < sill 90-110) to be under window swing footprint (since window swings above sill), then worst case passes for 80x190 and 90x190
- Full layout search (bed+desk+ward+chair):
  - Tried 3 generic layouts A/B/C with nominal dimensions, all failed initial collision due to door swing and E_low corner
  - Improved logic to allow low in window, and require east edge <= S-door_w to clear door leaf final position
  - Found that bed south and ward east cannot coexist if both at south because ward needs y>=bed_h to avoid overlap but then y>=86.5 blocks door (needs y+h<=door_south 157 for h80 => y<=77). Contradiction -> bed south + ward east impossible for h80 wardrobe
  - Bed north with length 195 fails door because east edge 208 > S-door_w 138 and y includes door leaf y=237. To avoid, need east edge <=138 => max length 136.5 impossible for 190 bed. Solution: bed NS orientation (85x195) with east edge 96.5 <=138 safe, or bed EW south with y below door_south
  - After many iterations, found feasible nominal layouts with tight clearances (some red <60) but no overlaps and no door/window blocks for tall furniture
  - Worst case: even with low allowed, 90x200 fails, 80x200 has only 2 positions, 80x190 and 90x190 have 18 and 13 positions but full 3-piece layouts with 60cm clearance fail. With relaxed clearance 20cm, found 0 layouts for nominal in brute force due to chair overlapping bed. Manual layout found: Bed NS West 85x195 at (11.5,68.5), Desk South 120x60 at (100,1.5), Ward East South at (161.5,0) etc. has red clearances 3.5cm etc. but no overlap
  - Decision: report that no good layout passes worst case with 60cm green clearance everywhere. Nominal passes with amber/red. Provide 3 layouts that are best achievable nominally, and show what it takes to pass worst (e.g., smaller room actually 218 not 211, window 80 not 95, door 80 not 90, corners 10 not 12, and use 80x190 not 90x200)

## Photo calibration
- Photos downscaled to <=2000px, processed one at a time
- Attempted to calibrate using known plan dimensions, not tile size
- For WA0017 (doorway looking west): identified window on right, south wall left, floor tiles diagonal. Tried to detect floor quadrilateral but perspective distorted, confidence LOW
- For WA0011 (south wall / SW corner): shows SW corner, floor tiles. Counted tiles along south wall ~5-6 tiles, south wall 218cm => tile size 218/5.5=39.6cm plausible for 40cm tiles, cross-check passes
- Created schematic overlays with measurements annotated, not precise perspective projection, labelled confidence LOW, kept in local sandbox only (not committed to public repo)
- Generated man 1.80m top-view footprint 50x28 and side silhouette 180cm for height checks (2.70 ceiling, no loft)

## Shopping research (Italy only)
- Primary: MONDO CONVENIENZA - checked beds, mattresses, desks, wardrobes via web search and fetch
  - Beds: Conca 91x204x118 80€, City2 99x207x115 90x190 412€, Selene 95x204x107 185€, Eleonora 90x206x93 265€, Tevere 91x204x118 88€
  - Mattresses: Silver fast 80x190x25 98€, Sleep 75€, Premium 69€, Top summer 71€, Magnum 118€
  - Desks: Aurora 120x60x73 38€, Spring dritta 61€, Spring 3 cassetti 144€, Aurora con cassetti 85€, Spring 150x60x73 147€
  - Wardrobes: Donatella 2 ante battenti 81x52x236 178€ (120€ promo), 3 ante 121x52x236 270€, 2 ante scorrevoli 195x58x236 390€ (too big), Marina 183x62x245 425€ (too big)
  - Delivery: fascia A 49€ min, fascia B 98€ min, or 16% if above 307/613 threshold, within 100km of nearest store, else extra. Gold +19€
  - Assembly included in transport+montaggio
- Also: IKEA Italia - PAX 100x60x201 215€, 100x60x236 235€, structure 100x58x236 85€ + ante, LAGKAPTEN desk 120x60 45€, MALM bed 90x200 199€, etc. Delivery al piano 49€, montaggio da 40€, TaskRabbit
- JYSK: KILDEN 80x190 100€, OLSKER 80x190 150€/199€, BAJLUM pieghevole 95€ (rejected not daily), HASLA mattress 50€, BILLEFJORD 40€, BANELVA 80€
- Amazon.it: OnNuvo contenitore 80x190 299€, Zinus 148€, BS COM 379€, desks 59€, etc.
- Conforama: Quadro 119x58x72 99.99€, Easy 120x50x76 89€, Gemma 120x60x120 160€
- For each category collected 6-8 candidates across 3 retailers, recorded in research/<retailer>/<category>.csv with URL, price, date, dimensions, package, material, delivery, availability, notes
- Black Friday near 27 Nov 2026: flagged that prices may change, but today price counts

## Layouts
- Defined 3 layouts A/B/C with top-view renders for nominal and worst (6 renders) plus base room plans (2) total 8 renders in /home/user/renders and copied to repo renders (except photo overlays kept local)
- Layout A: Bed South EW 80x190 (195x85) at (13,1.5), Desk North 100x60 at (11.5,203.5), Ward West 55x80 at (1.5,86.5), Chair at (11.5,133.5) - nominal pass but chair-ward overlap 33cm? Actually after adjustment, chair-ward overlap still, need to report
- Layout B: Bed NS West 85x195 at (11.5,68.5), Desk South 120x60 at (100,1.5), Ward East South at (161.5,0) etc.
- Layout C: Bed NS West, Desk East vertical, Ward West South
- Evaluated clearances: many red <60, amber 60-70, green 70+ - reported in clearance tables
- Man-walk paths traced: door->bed, door->desk chair, door->window, door->wardrobe with doors/drawers and window open - some paths require sideways squeezing <60 red

## Final recommendation
- Will propose 3 packages: A Best value under 1000, B Best quality up to 1200, C Cheapest sensible
- For each: full price breakdown items+delivery+assembly, pros/cons, what could go wrong
- Winner: Best value (A) using Mondo Conca 80€ + Vienna rete 48€ + Premium mattress 69€ + Aurora desk 38€ + Donatella 81x52x236 promo 120€ = 355 + delivery 98 = 453€ total, well under 1000, with storage bed alternative Selene 185€ if budget allows
- Rejected products list: Donatella 195x58x236 too big (195>157 east below door), Marina 183x62x245 too big, 90x200 bed fails worst case, BAJLUM pieghevole not daily, Gemma desk 120 height > sill, etc.
- MEASURE-ME list ranked max 10: south wall total, west total, north between corners, north to window, east below door, window width, door width, wall corners depth/lengths, sill height, ceiling height - each with where to put tape and which recommendation flips
- Verification: re-open product pages (done via fetch), recompute totals by script, red-team winner with worst case, review repo for leaked secrets (token not in files, .git/config clean), confirm nothing outside room001 touched (git remote -v only room001)

## Assumptions carried
- Skirting 1.2cm thick reduces usable floor by 1.5cm
- Bed height 50cm < sill, desk 75cm < sill, wardrobe 200cm > sill
- Chair pull-back 70cm
- Man 50x28 footprint, 180cm height
- Delivery assumed mainland Italy, standard home delivery, CAP range gives delivery cost range 49-98 or 16%
- Access path assumed 80cm doors, normal stairwell, longest package 210cm (PAX) may need diagonal, weight up to 49.45kg per collo

## Next steps
- Generate REPORT.md, SHOPPING_LIST.csv, finalize renders, commit
