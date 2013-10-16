import logging
logger = logging.getLogger(__name__)

from sys import exit

from .util import get_workspace


def filter_content(lines):
    lineno = 0
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            yield (line, lineno)
        lineno += 1

def assemble_model(file):
    """
    :param file: a filename for a .model file or an iterable
    :returns: a workspace filled with the model described in `file`
    """
    if type(file) == str:
        with open(file) as f:
            return assemble_model(f)

    w = get_workspace()
    factory = w.factory()

    logger.info('Assembling model file: \'%s\'' % file)

    for line, lineno in filter_content(file):
        if not factory.process(line):
            logger.error('RooFit factory error at line %d', lineno)
            exit(1)

    return w

def split_model(model, dataset, split_on, differing):
    """
    :param model:
    :param dataset:
    :param splitOn:
    :param model_name:
    :param differing:
    :returns: A simultaneous pdf split over the provided category
    """
    from ROOT import RooArgSet, RooSimPdfBuilder, SetOwnership

    model_name = model.GetName()

    # physModels = model1 [model2..]
    # splitCats  = splitVar1 [splitVar2..]
    # model1     = splitVar1 : diff1 [diff2..]

    logger.debug('split_model parameters are %s, %s and %s' % (split_on, model_name, differing))

    builder = RooSimPdfBuilder(RooArgSet(model))
    bconfig = builder.createProtoBuildConfig()
    bconfig['physModels'] =  model_name
    bconfig['splitCats'] = split_on
    bconfig[model_name] = "%s : %s" % (split_on, ','.join(differing))

    pdf = builder.buildPdf(bconfig, dataset)

    SetOwnership(builder, False)

    return pdf

def split_custom(models, dataset, config):
    """
    :config: Dictionary with the following format:
             { 'model1': [('splitCat1', ['var1', 'var2', 'var3']),
                          ('splitCat2', ['var2', 'var3'        ]),
                         ],
               'model2': [('splitCat1', ['var3'])]
             }
    """

    from ROOT import RooArgSet, RooSimPdfBuilder, SetOwnership
    model_name = model.GetName()
    logger.debug('split_custom configuration is %s' % config)

    builder = RooSimPdfBuilder(RooArgSet(*models))
    bconfig = builder.createProtoBuildConfig()

    models = config.keys()
    splitCats = []
    for m in config:
        splitCats.append(config[m][0])

    bconfig['physModels'] = ','.join(config.keys())
    bconfig['splitCats'] = ','.join(config.keys())

    for m in config:
        cats = bconfig[m]
        entries = ""
        for c in cats:
            entries.append('%s : %s\n' % (c[0], ','.join(c[1])))

        bconfig[m] = '\n'.join(entries)

    pdf = builder.buildPdf(bconfig, dataset)
    SetOwnership(builder, False)

    return pdf

def get_values(model, variables):
    from ROOT import RooArgSet
    result = [None] * len(variables)
    result_err = [None] * len(variables)
    it = model.getParameters(RooArgSet()).iterator()
    next = it.Next()
    while next:
        if next.GetName() in variables:
            idx = variables.index(next.GetName())
            result[idx] = next.getVal()
            result_err[idx] = next.getError()
        next = it.Next()
    if None in variables:
        logger.error('Variable not found in model: %s' % (variables[result.index(None)]))
        exit(1)
    return result, result_err

