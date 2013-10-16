
import os

from .util import get_matching_vars, save_dataset
from .config import get_named_section
from .model import assemble_model, split_model

import logging
logger = logging.getLogger(__name__)

def max_ap(model, data, start_params='None', out_params='result.params', numcpus=1, strategy=1, fit=True, extended=False):
    """
    Finds the maximum of the a posteriori probability of the model given the data.
    Equivalent to finding the best estimate of the model parameters.
    """
    from ROOT import RooFit
    if start_params == 'None':
        logger.warning('Not reading in initial parameters. Using defaults from model.')
    elif not os.path.exists(start_params):
        logger.error('No such parameter file: \'%s\'' % start_params)
        exit(1)
    else:
        logger.info('Reading in parameters from \'%s\'' % start_params)
        model.getParameters(data).readFromFile(start_params)
    logger.info('Starting fit')
    if fit:
        results = model.fitTo(
                data,
                RooFit.NumCPU(numcpus),
                RooFit.Extended(extended),
                RooFit.Minos(False),
                RooFit.Strategy(2),
                RooFit.Minimizer('Minuit2'),
                RooFit.Save(True),
        )
        logger.info('Finished fit')
    else:
        logger.info('Not performing fit')
    logger.info('Writing resulting parameters to \'%s\'' % out_params)
    model.getParameters(data).writeToFile(out_params)
    return results

def add_weights(model, data, yield_names):
    iter = model.getParameters(data).iterator()
    yields = []
    next = iter.Next()
    while next:
        if not next.GetName() in yield_names:
            next.setConstant(True)
        else:
            yields.append(next)
        next = iter.Next()

    from ROOT import RooStats, RooDataSet, RooArgList
    sdata = RooStats.SPlot("SPlot", "SPlot", data, model, RooArgList(*yields))
    components = []
    for name in yield_names:
        components.append(RooDataSet(data.GetName(), data.GetTitle(), data, data.get(), '', name + '_sw'))
    return components

def run_normal(model, data, config, args):
    perform_fit(
            model,
            data,
            config['fit']['startParams'],
            out_params=config['fit']['outParams'],
            numcpus=int(config['fit']['numCPUs']),
            strategy=int(config['fit']['strategy'])
    )

def run_split(model, data, config, args):
    pdf = split_model(model, data, config['split']['splitOn'], config['split']['differing'])
    run_normal(pdf, data, config, args)

def run_montecarlo(model, vars, start_params, numEvents):
    from ROOT import RooArgSet
    logger.info('Generating \'%s\' events with model \'%s\' and initial parameters \'%s\'' % (numEvents, model.GetName(), start_params))
    model.getParameters(RooArgSet(*vars)).readFromFile(start_params)
    return model.generate(RooArgSet(*vars), numEvents)

def run_cmd(config, args):
    w = assemble_model(config['fit']['modelFile'])
    model_name = config['fit']['model']
    model = w.pdf(model_name)

    logger.debug('Model variable is %s' % model)

    type = config['fit']['type']

    dataname = config['fit']['dataset']
    sec = get_named_section(config, 'data', dataname)

    from functools import partial

    datatype = config[sec]['type']
    fname = config[sec]['file']

    if datatype == 'dataset':
        loader = partial(load_dataset, w, fname)
    elif datatype == 'tree':
        cutstring = config[sec]['cutString']
        loader = partial(load_tree, w, fname, config[sec]['treeName'], config[sec]['cutString'])

    if type == 'split':
        data = loader()
        run_split(model, data, config, args)
    elif type == 'normal':
        data = loader()
        run_normal(model, data, config, args)
    elif type == 'montecarlo':
        vs = config['montecarlo']['genVars']
        vars = []
        for v in vs:
            new = w.obj(v)
            if not new:
                logger.error('No such variable in model: %s' % v)
                exit(1)
            vars.append(w.obj(v))
        data = run_montecarlo(model, vars, config['fit']['startParams'], int(config['montecarlo']['numEvents']))
        save_dataset(data, 'test.root')
    else:
        logger.error('No such fit type: %s' % type)
        exit(1)
