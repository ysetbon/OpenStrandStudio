# Additional sample collection

Keep Woven Heart and Tidal Waves from the original creative collection, and add
four loose Chinese-knot diagram studies: Double Coin, Cloverleaf, Good Luck,
and Pan Chang. The original twelve application samples are unchanged.

The knot diagrams use an attached strand chain for the cord, red and gold for
its two sections, native masks for crossings, and a Complete knot group. These
are editable planar studies rather than step-by-step tying instructions.

The knot curves are simplified with the app's native two-control-point curve
model. The generator tries several fitting tolerances, keeps the smallest
attachment chain whose crossing sequence and over/under order match the
reference, and protects crowded crossing segments when necessary. It uses
start and end handles, with the center control point unlocked. Fitted handles
follow the reference tangents at joins, preventing corners between attachments.
The fitting and reload checks use the live canvas curvature defaults (1, 2, 2).
Masks erase the entire unwanted overlap component when the same two longer
strands cross in opposite orders, preventing clipped edges at shallow crossings.

The four knots use 5, 22, 18, and 9 attached strands respectively. The generator
minimizes the count within its fitting candidates while preserving crossings;
this is not a claim of a global mathematical minimum.

Knot structure and visual references consulted: Carol Wang's
[Double Coin](https://chineseknotting.org/coin/howto2/),
[Cloverleaf](https://chineseknotting.org/flower/howto4.html),
[Good Luck](https://chineseknotting.org/luck/howto4/), and
[Pan Chang](https://chineseknotting.org/mystic/) guides.
Reference photographs are not distributed with these samples.

Regenerate the six additional projects and their previews from the repository
root with:

```sh
python scripts/generate_creative_samples.py --preview artifacts/creative_samples
```

The generator reloads each JSON and checks strand counts, attachment endpoints,
attachment lengths, control points, group references, and nonempty masks.
Every candidate also checks which strand is above at each crossing.
`verify_ui.py` checks
loading, group restoration, snapshot serialization, translations, and access to
all eighteen sample buttons in the real application running offscreen.
`review_in_app.py NAME --tag final` opens one sample in an isolated real
MainWindow, checks that loaded curves match the validated geometry, captures
the actual painted canvas with shadows, and checks control points and mask
erasures survive serialization. The six final canvas captures in `review/`
were individually inspected. These captures use an offscreen test instance,
not the user's running desktop window.
