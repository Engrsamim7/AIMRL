import os, glob, sys
HERE = os.path.dirname(os.path.abspath(__file__))
def wpath(fname):
    """Locate a .pt weight file: out/ next to the scripts, else search nearby folders."""
    p = os.path.join(HERE, "out", fname)
    if os.path.exists(p): return p
    for root in (HERE, os.path.dirname(HERE), os.path.expanduser("~/Downloads")):
        hits = glob.glob(os.path.join(root, "**", fname), recursive=True)
        if hits: return hits[0]
    sys.exit(f"\nMissing {fname}.\nScripts folder: {HERE}\nExpected it in: {os.path.join(HERE,'out')}\n"
             f"Put the .pt files from trained_weights.zip there.")
