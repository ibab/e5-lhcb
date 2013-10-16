import logging
logger = logging.getLogger(__name__)

def setup_roofit():
    from .silence import silence
    from ROOT import gSystem
    logger.info('Did you know that RooFit was written by Wouter Verkerke and David Kirkby?')
    with silence():
        gSystem.Load('libRooFit')

def silence_roofit():
    import ROOT
    ROOT.RooMsgService.instance().setGlobalKillBelow(ROOT.RooFit.WARNING)

def get_workspace():
    from ROOT import RooWorkspace
    return RooWorkspace('workspace')

def get_matching_vars(wspace, tree):
    varSet = wspace.allVars()
    vars = dict()
    it = varSet.createIterator()
    el = it.Next()
    result = []
    while el:
        vars[el.GetName()] = el
        el = it.Next()
    catSet = wspace.allCats()
    it = catSet.createIterator()
    el = it.Next()
    while el:
        vars[el.GetName()] = el
        el = it.Next()

    for b in tree.GetListOfBranches():
        if b.GetName() in vars:
            result.append(vars[b.GetName()])

    logger.info('Matched the following variables between model and data: %s' % [v.GetName() for v in result])
    return result

def load_dataset(w, fname):
    from ROOT import RooDataSet, TFile, RooArgSet

    if not os.path.exists(fname):
        raise IOError('File not found: %s' % fname)

    logger.info('Loading data from dataset: %s' % fname)

    file = TFile(fname)
    data = file.Get('modelData')

    return data

def save_dataset(dataset, fname):
    from rootpy.io import root_open

    f = root_open(fname, 'recreate')
    dataset.Write()
    f.close()

def wrap_iter(it):
    elem = it.Next()
    while elem:
        yield elem
        elem = it.Next()

def load_tree(w, fname, treename, cutstring=''):
    from ROOT import RooDataSet, TFile, RooArgSet

    if not os.path.exists(fname):
        raise IOError('File not found: %s' % fname)

    logger.debug('Loading data from tree: %s/%s' % (fname, treename))

    file = TFile(fname)
    tree = file.Get(treename)

    tmp = TFile('tmp.root', 'RECREATE')
    if cutstring:
        logger.info('Applying cut string: \'%s\'' % cutstring)
        tree = tree.CopyTree(cutstring)
    else:
        tree = tree.CopyTree()

    vars = get_matching_vars(w, tree)
    tree.SetBranchStatus("*", False)
    for v in vars:
        tree.SetBranchStatus(v.GetName(), True)
    args = RooArgSet(*vars)
    data = RooDataSet('data', 'data', tree, args)

    return data

