
import re

import logging
logger = logging.getLogger(__name__)

def get_named_section(config, section, name):
    for sec in config.sections:
        if sec.startswith(section):
            if re.match(r'%s\s+("%s"|\'%s\'|%s)' % (section, name, name, name), sec):
                return sec
    raise ValueError('No such section: %s "%s"' % (section, name))

def get_config(filename='fit.cfg'):
    from configobj import ConfigObj

    config = ConfigObj(filename)

    #try:
    #    config = ConfigObj(filename, configspec=spec, file_error=True)
    #except (ConfigObjError, IOError), e:
    #    logger.error('Could not read "%s": %s' % (filename, e))
    #    exit(1)

    #validator = Validator()
    #results = config.validate(validator, preserve_errors=True)

    #if results != True:
    #    for (section_list, key, _) in flatten_errors(config, results):
    #        if key is not None:
    #            logger.error('The "%s" key in the section "%s" failed validation' % (key, ', '.join(section_list)))
    #        else:
    #            logger.error('The following section was missing: %s ' % ', '.join(section_list))
    return config

def get_args():
    parser = get_cmdline_parser()
    args = parser.parse_args()
    logger.debug('Parsed the following arguments: %s' % args)
    return args

def get_cmdline_parser():
    import argparse
    from .fit import run_cmd
    from .visualize import show_cmd
    from .plot import plot_cmd

    parser = argparse.ArgumentParser(description='RooFit helper')

    parser.add_argument('--version', action='version', version='0.0')

    sub = parser.add_subparsers(help='subcommands')

    parser_show = sub.add_parser('show', help='show model')
    parser_show.add_argument('file', help='the .model file')
    parser_show.add_argument('--graph', dest='graph', metavar='PDF')
    parser_show.set_defaults(func=show_cmd)

    parser_run = sub.add_parser('run', help='run fit')
    parser_run.set_defaults(func=run_cmd)

    parser_plot = sub.add_parser('plot', help='plot model')
    parser_plot.set_defaults(func=plot_cmd)

    return parser
