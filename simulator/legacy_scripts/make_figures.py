"""Regenerate ALL manuscript figures from the saved experiment outputs in out/*.csv (+ a live simulator run for Fig. 6 and 12).
Usage:  python make_figures.py        -> writes figs/*.pdf and figs/*.png
Data source per figure:
  Fig 1  schematic of the model (hand-drawn diagram by design; contains no results)
  Fig 2  out/curve_*.csv (python curves.py <algo> <comm> <seed> 300)      Fig 3  out/table3_full.csv (python table3.py)
  Fig 4  out/ablate.csv   Fig 5 out/harsh2.csv   Fig 6 out/casestudy.json (python casestudy.py)  Fig 7 out/sweep_gate.csv
  Fig 8  out/scaling.csv  Fig 9 out/reactive_heur.csv + out/diversify.csv  Fig 10 out/fir.csv  Fig 11 out/rob_*.csv
  Fig 14 out/dynamics.csv (python dynamics.py)
  Fig 12 live simulator trace (fig_trace.py)   Fig 13 live simulator snapshots (fig_snapshots.py)"""
import os, glob, runpy, sys
os.makedirs("figs", exist_ok=True)
need = {"fig3": "out/table3_full.csv", "fig4": "out/ablate.csv", "fig5": "out/harsh2.csv", "fig6": "out/casestudy.json", "fig7": "out/sweep_gate.csv",
        "fig8": "out/scaling.csv", "fig9": "out/reactive_heur.csv", "fig10": "out/fir.csv", "fig14": "out/dynamics.csv"}
for k, f in need.items():
    if not os.path.exists(f): print(f"[skip] {k}: {f} missing - run the matching experiment script first")
import figs_a, figs_b
ncur = len(glob.glob("out/curve_*.csv"))
for mod in (figs_a, figs_b):
    for n in sorted(x for x in dir(mod) if x.startswith("fig") and x[3:].isdigit()):
        if n == "fig2" and ncur < 18: print(f"[skip] fig2: only {ncur}/18 training-curve files - run  python run_curves.py"); continue
        try: getattr(mod, n)(); print("ok  ", n)
        except Exception as e: print("FAIL", n, "->", type(e).__name__, e)
for fn, nm in (("fig_trace.py", "fig12"), ("fig_snapshots.py", "fig13")):
    try: runpy.run_path(fn); print("ok  ", nm)
    except Exception as e: print("FAIL", nm, "->", e)
