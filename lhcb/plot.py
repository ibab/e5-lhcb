"""
Plotting module

Contains several ugly hacks.
Here be dragons.
"""

import os

import logging
logger = logging.getLogger(__name__)

from .model import assemble_model
from .fit import load_dataset

def set_lhcb_style():
    from matplotlib import rc
    import matplotlib.pyplot as pyplot
    rc('xtick.major', size=6)
    rc('ytick.major', size=6)
    rc('xtick.minor', size=3)
    rc('ytick.minor', size=3)
    rc('lines', markeredgewidth=0.5)
    rc('lines', markersize=4)
    rc('font', family='serif')
    rc('font', serif='Times')

def plot_asymmetry(time, data, model, mixing, numcpus=1, xlabel=''):
    from ROOT import RooFit
    ax = plot_dimension(time, data, model, numcpus=numcpus, extra_params=[RooFit.Asymmetry(mixing), RooFit.Binning(23)], norm=1, xlabel=xlabel)
    ax.set_ylim(-1, 1)

def plot_dimension(var, data, model, components=None, numcpus=1, xlabel='', extra_params=None, norm=None, log=False, binning=None):
    if not extra_params:
        extra_params = []
    if not norm:
        norm = 1 #data.numEntries()

    from numpy import linspace, maximum, array

    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    from matplotlib.ticker import MaxNLocator

    cax = plt.gca()
    box = cax.get_position()
    xmin, ymin = box.xmin, box.ymin
    xmax, ymax = box.xmax, box.ymax

    gs = GridSpec(2, 1, height_ratios=[7, 1], left=xmin, right=xmax, bottom=ymin, top=ymax)
    gs.update(hspace=0)

    xpos, width, y, yerr = get_binned_data(var, data, extra_params=extra_params, binning=binning)
    x = linspace(var.getMin(), var.getMax(), 200)

    if not components:
        f = get_function(var, model, data, norm=norm, extra_params=extra_params)
    else:
        f, comps = get_function(var, model, data, components=components, norm=norm, extra_params=extra_params)

    ax = plt.subplot(gs[0])

    if components:
        for c in comps:
            plt.plot(x, c(x), '--', dashes=[8,3])

    plt.plot(x, f(x), 'r-')
    if log:
        ax.set_yscale('log')
        ax.set_ylim(max(0.1, min(y)), 1.2 * max(y))
        yerr[0] = y - maximum(1e-1, y - yerr[0])
    else:
        ax.set_ylim(0, 1.1 * max(y))
        plt.gca().yaxis.set_major_locator(MaxNLocator(prune='lower'))

    plt.errorbar(xpos, y, yerr=yerr, fmt='o', color='k', zorder=100)
    plt.setp(ax.get_xticklabels(), visible=False)

    bx = plt.subplot(gs[1], sharex=ax)
    pull = calc_pull(xpos, f, y, yerr)

    plt.fill_between([var.getMin(), var.getMax()], 2, 1, facecolor='#bbbbbb', linewidth=0, edgecolor='#bbbbbb')
    plt.fill_between([var.getMin(), var.getMax()], -2, -1, facecolor='#bbbbbb', linewidth=0, edgecolor='#bbbbbb')

    color = ['#cc4444' if abs(p) > 3 else '#555555' for p in pull]
    plt.bar(xpos-width/2, pull, width, color=color, linewidth=0.8)

    plt.axhline(0, color='black')

    if xlabel:
        plt.xlabel(xlabel)

    plt.xlim(var.getMin(), var.getMax())
    plt.ylim(-3, 3)
    bx.get_yaxis().set_ticks([-3, 0, 3])

    plt.sca(ax)
    return ax


def calc_pull(x, f, y, yerr):
    from numpy import zeros, NaN

    try:
        yerr_low, yerr_high = yerr
        yerr = zeros(len(yerr_low))
        lower = y > f(x)
        yerr[lower] = yerr_low[lower]
        yerr[~lower] = yerr_high[~lower]
    except ValueError:
        pass
    yerr[yerr == 0] = NaN
    pull = (y - f(x)) / yerr

    return pull

def get_function(x, model, data, components=None, norm=1, numcpus=1, extra_params=None):
    if not extra_params:
        extra_params = []

    from numpy import vectorize
    from ROOT import RooCurve, Double, RooFit

    frame = x.frame()

    data.plotOn(frame)
    model.plotOn(frame, RooFit.NumCPU(numcpus), *extra_params)

    if components:
        for c in components:
            model.plotOn(frame, RooFit.NumCPU(numcpus), RooFit.Components(c), *extra_params)

    funcs = []
    for idx in range(1, int(frame.numItems())):
        curr = frame.getObject(idx)
        funcs.append(vectorize(lambda x, curr=curr: norm * curr.Eval(x)))
    
    if len(funcs) > 1:
        return funcs[0], funcs[1:]
    else:
        return funcs[0]

def get_data(data):
    from .util import wrap_iter
    from numpy import zeros
    curr = data.get(0)
    ret = zeros((curr.getSize(), data.numEntries()))
    vars = []
    for v in wrap_iter(curr.iterator()):
        vars.append(v)
    idx = 0
    while curr:
        for i, v in enumerate(vars):
            var = curr.find(v)
            try:
                ret[i, idx] = var.getVal()
            except AttributeError:
                ret[i, idx] = var.getIndex()
        idx += 1
        curr = data.get(idx)
    return ret

def get_binned_data(x, data, extra_params=None, binning=None):
    if not extra_params:
        extra_params = []
    if binning:
        from ROOT import RooFit
        extra_params.append(RooFit.Binning(binning))

    from numpy import array
    from ROOT import RooHist, Double

    frame = x.frame()

    data.plotOn(frame, *extra_params)

    x = []
    y = []
    x_err_low = []
    x_err_high = []
    y_err_low = []
    y_err_high = []

    data = frame.getObject(0)

    d1 = Double()
    d2 = Double()

    ret = 0
    i = 0
    while ret != -1:
        ret = data.GetPoint(i, d1, d2)
        x.append(float(d1))
        y.append(float(d2))
        x_err_low.append(data.GetErrorXlow(i))
        x_err_high.append(data.GetErrorXhigh(i))
        y_err_low.append(data.GetErrorYlow(i))
        y_err_high.append(data.GetErrorYhigh(i))
        i += 1

    width = array(x_err_low) + array(x_err_high)
    return array(x), width, array(y), array([y_err_low, y_err_high])

def plot_cmd(config, args):
    from functools import partial
    from .config import get_named_section
    from .fit import load_tree, load_dataset

    import re

    try:
        dims = config['plot']['dimensions']
    except:
        logger.error('You must specify the variables you want to plot as \'plot.dimensions\' in your config file')
        exit(1)

    if not dims:
        logger.error('\'plot.dimensions\' is empty. Nothing to plot.')
        exit(1)

    # log(...)
    create_log = []
    vars = []
    log_pattern = 'log\((.*?)\)'
    for d in dims:
        m = re.match(log_pattern, d)
        if m:
            s = m.groups()[0]
            create_log.append(s)
        else:
            vars.append(d)

    w = assemble_model(config['fit']['modelFile'])
    model_name = config['fit']['model']

    model = w.pdf(model_name)

    dataname = config['fit']['dataset']
    sec = get_named_section(config, 'data', dataname)

    datatype = config[sec]['type']
    fname = config[sec]['file']

    if datatype == 'dataset':
        loader = partial(load_dataset, w, fname)
    elif datatype == 'tree':
        cutstring = config[sec]['cutString']
        loader = partial(load_tree, w, fname, config[sec]['treeName'], config[sec]['cutString'])

    data = loader()

    ftype = config['fit']['type']

    if ftype == 'split':
        from .fit import split_model
        model = split_model(model, data, config['split']['splitOn'], config['split']['differing'])
        assert model
    elif ftype == 'normal':
        pass
    else:
        raise ValueError()

    model.getParameters(data).readFromFile(config['plot']['withParams'])

    set_style()

    if type(vars) == str:
        vars = [vars]

    if not 'components' in config['plot']:
        components = None
    else:
        components = config['plot']['components']

    for vname in vars:
        var = w.var(vname)
        if ftype == 'split':
            indexCat = model.indexCat()
            datalist = data.split(indexCat)

            it = indexCat.typeIterator()
            cat = it.Next()

            while cat:
                subdata = datalist.FindObject(cat.GetName())
                subpdf = model.getPdf(cat.GetName())

                plot_hist(var, subpdf, subdata, fname='%s-%s.pdf' % (var.GetName(), cat.GetName()[1:-1]), numcpus=int(config['fit']['numCPUs']), components=components)

                cat = it.Next()

        elif ftype == 'normal':
            plot_hist(var, model, data, numcpus=int(config['fit']['numCPUs']), components=components)

    for vname in create_log:
        var = w.var(vname)
        if ftype == 'split':
            indexCat = model.indexCat()
            datalist = data.split(indexCat)

            it = indexCat.typeIterator()
            cat = it.Next()

            while cat:
                subdata = datalist.FindObject(cat.GetName())
                subpdf = model.getPdf(cat.GetName())

                plot_hist(var, subpdf, subdata, fname='%s-log-%s.pdf' % (var.GetName(), cat.GetName()[1:-1]), numcpus=int(config['fit']['numCPUs']), components=components, log=True)

                cat = it.Next()

        elif ftype == 'normal':
            plot_hist(var, model, data, fname='%s-log.pdf' % (var.GetName()), numcpus=int(config['fit']['numCPUs']), components=components, log=True)

    if 'asymVars' in config['plot']:
        time, mixing = config['plot']['asymVars']
        time = w.var(time)
        mixing = w.cat(mixing)
        if ftype == 'split':
            indexCat = model.indexCat()
            datalist = data.split(indexCat)

            it = indexCat.typeIterator()
            cat = it.Next()

            while cat:
                subdata = datalist.FindObject(cat.GetName())
                subpdf = model.getPdf(cat.GetName())

                plot_asymmetry(time, subpdf, subdata, mixing, fname='Asymmetry-%s.pdf' % cat.GetName()[1:-1], numcpus=int(config['fit']['numCPUs']))

                cat = it.Next()
        else:
            plot_asymmetry(time, model, data, mixing, numcpus=int(config['fit']['numCPUs']))

