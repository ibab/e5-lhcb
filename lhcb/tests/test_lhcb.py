import os

class Testlhcb:

    def setUp(self):
        from lhcb.util import setup_roofit, silence_roofit
        setup_roofit()
        silence_roofit()
        from ROOT import RooArgSet, RooGaussian, RooRealVar
        self.x = RooRealVar('x', 'x', -10, 10)
        self.mean = RooRealVar('mean', 'mean', 1, -10, 10)
        self.sigma = RooRealVar('sigma', 'sigma', 1, 0, 10)
        self.model = RooGaussian('model', 'model', self.x, self.mean, self.sigma)
        self.data = self.model.generate(RooArgSet(self.x), 1000)

    def test_perform_fit(self):
        from lhcb.fit import perform_fit
        perform_fit(self.model, self.data)

    def test_assemble_model(self):
        from lhcb.model import assemble_model
        w = assemble_model(os.path.dirname(__file__) + '/../testdata/test.model')
        assert w

    def test_save_dataset(self):
        from lhcb.util import save_dataset
        #from lhcb.fit import load_dataset
        save_dataset(self.data, 'mytest.root')
        assert os.path.exists('mytest.root')
        os.remove('mytest.root')

    def test_get_cmdline_parser(self):
        from lhcb.config import get_cmdline_parser
        parser = get_cmdline_parser()
        args = parser.parse_args('show --graph model test.model'.split())

    def test_get_named_section(self):
        from lhcb.config import get_config, get_named_section
        config = get_config(os.path.dirname(__file__) + '/../testdata/test.cfg')
        assert bool(get_named_section(config, 'named', 'first'))

    def test_plot_hist(self):
        from lhcb.plot import plot_hist, set_style
        set_style()
        plot_hist(self.x, self.model, self.data, fname='test.pdf', plotdir='.')
        assert os.path.exists('test.pdf')
        os.remove('test.pdf')

    def test_splot(self):
        from lhcb.fit import splot
        sigData, bkgData = splot(self.model, self.data, ['sigN', 'bkgN'])
        assert sigData
        assert bkgData

