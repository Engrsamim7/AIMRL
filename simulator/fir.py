"""Use the exact single-message replay runner; the old policy-level FIR is historical."""
import sys
from run_experiments import main
if __name__ == '__main__':
    sys.argv.insert(1,'fir')
    main()
