# Plot 83 / Portrait orientation correction

Rebuild: `python3 build_cad_2800443.py` followed by `python3 build_claude_boards.py` and delivery rendering.

The employer survey governs: north road P4–P1 =17m, east spine P1–P2 =25m, west Plot84 P4–P3 =25m, south Plot10 P3–P2 =17m. North is up. P4–P2 =30.2324329157m, displayed30.23m.

All plan exports share the same geometric primitives. Screen drawing coordinates run south from the north edge; DXF local coordinates are X east and Y north, P3=(0,0). Drawing x offsets are recorded in engineering_validation.json; subtract each offset to recover the surveyed coordinates. DXF units are millimetres.

Ground: world X=3.50..16.50, Y=6.00..23.00; 13.00×17.00=221.00 minus2.50×3.40=8.50 open court gives212.50m² (50%).
Typical: world X=3.00..16.75, Y=6.00..23.618181818; 13.75×17.618181818=242.25 minus8.50 gives233.75m² (55%). The depth rounds to17.62m; treating17.62 as exact would add0.025m².
Roof:12.50×8.50=106.25m² (25%), level+13.65m. The court stays open outside the roof enclosure.

Pool:6.00×3.00m is the outside structural-shell footprint. A200mm shell lies INSIDE that footprint, leaving5.60×2.60m clear water. The south garden is exactly1.50m insulated structural buffer +3.00m pool shell +1.50m fence clearance=6.00m. A6×3m CLEAR-WATER pool plus shell cannot satisfy those exact dimensions inside a6m garden. The lowered, retained buffer permits a conceptual basement overlook; foundation and water details are pending.

Basement has six2.40×4.60m compact bays, a6.00m aisle with no drawn columns, family sitting facing the sunken pool court, kitchenette,2WCs, gym, storage, electrical and water rooms. Ri3.2/Ro5.8 are geometric turning envelopes only. The3m west ramp strip has a nominal20%/16m run to−3.20m; its landing, grade transitions, wall deductions and connection to the parking aisle remain unresolved. Do not present six-car access as verified.

Room dimensions and areas are schematic rectangular reservations. Door access, wall offsets, fire and structure need design development. Coverage is a geometric calculation, not local-authority approval. The package is not for construction.

## Remaining design work

### H01 / RAMP CONNECTION / SWEPT PATH
3.00 m west strip; 20% x 16.00 m nominal run. Transitions and garage link unresolved.
The west strip satisfies the requested plan width. Walls reduce usable clear width; local ramp slope limits, transitions, headroom and six-car entry/exit routes are not verified. Ri3.20/Ro5.80 arcs are geometric templates, not vehicle simulation.

### H02 / SUNKEN POOL / RETAINING
6 x 3 m outside shell; 1.50 m building buffer + 1.50 m south-fence clearance.
The 200 mm shell lies inside the pool footprint, leaving 5.60 x 2.60 m clear water. The buffer is lowered and retained to allow the basement overlook. Retaining, foundations, waterproofing, drainage, flood protection and guarding need engineering design.

### H03 / AREA MEASUREMENT
Ground221.00-8.50=212.50; typical242.25-8.50=233.75; roof106.25 m2.
Typical depth is exactly17.618181818m, rounded17.62m on dimensions. Open-sky court is2.50x3.40m. Coverage assumes the court is excluded; statutory counting and projections must be confirmed locally.

### H04 / CORE / STRUCTURE / SERVICES
Core B selected. Fire, egress, structure, lift and services remain schematic.
The clear 6m parking aisle contains no columns in this scheme. Structural spans, stacked core, ventilation, external openings and roof installations are not certified. No14% efficiency or energy-performance claim is made.

## Outputs
DXF,9-page vector PDF,10 individual SVG/PNG drawings,parameters,validation and manifest; board HTML and final JPG copies rebuilt by the delivery renderer. No submission or deployment performed.
