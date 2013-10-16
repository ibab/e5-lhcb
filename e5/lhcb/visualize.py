import logging
logger = logging.getLogger(__name__)

from .model import assemble_model

def show_cmd(config, args):
    w = assemble_model(args.file)

    if args.graph:
        import subprocess
        pdf = w.pdf(args.graph)
        if not pdf:
            logger.error('No model named "%s" in %s' % (args.graph, args.file))
            exit(1)
        pdf.graphVizTree('/tmp/graph.dot')
        subprocess.Popen('dot -Tpdf /tmp/graph.dot -o graph.pdf'.split())
    else:
        w.Print("t")

