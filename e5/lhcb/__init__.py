
import sys
back = sys.argv
sys.argv = ['foo', '-b']

import ROOT

ROOT.TApplication
sys.argv = back

ROOT.PyConfig.IgnoreCommandLineOptions = True

ROOT.SetMemoryPolicy(ROOT.kMemoryStrict)

from .main import main
