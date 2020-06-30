import numpy as np
import pylab as pl
import scipy.stats as st
from numpy.random import uniform, normal
from numpy import array, exp, cumsum, asarray
from numpy.linalg import norm
from scipy.integrate import quad


def is_distribution(p):
    p = asarray(p)
    return (p >= 0).all() and abs(1 - p.sum()) < 1e-10


def anneal(p, *, invT=None, T=None):
    "p ** (1/T)"
    if T is not None:
        assert invT is None
        invT = 1./T
    p = p ** invT
    p /= p.sum()
    return p


class _BruteForce:
    """
    Base class for tabular representation of a distribution

      p(x) ∝ score(x).

    where score(x) > 0 for all x ∈ domain.

    """

    def __init__(self):
        self.Z = np.sum([self.score(x) for x in self.domain()])
        self.P = {x: self.score(x) / self.Z for x in self.domain()}

    def domain(self):
        raise NotImplementedError

    def score(self, x):
        raise NotImplementedError()

    def entropy(self):
        return -np.sum([p * np.log(p) for p in self.P.values() if p != 0])

    def logp(self, x):
        return np.log(self.P[x])


class TruncatedDistribution:
    def __init__(self, d, a, b):
        assert np.all(a <= b), [a, b]
        self.d = d; self.a = a; self.b = b
        self.cdf_b = d.cdf(b)
        self.cdf_a = d.cdf(a)
        self.cdf_w = self.cdf_b - self.cdf_a
    def sf(self, x):
        return 1-self.cdf(x)
    def pdf(self, x):
        return (self.a <= x) * (x <= self.b) * self.d.pdf(x) / self.cdf_w
    def rvs(self, size=None):
        u = uniform(0, 1, size=size)
        return self.ppf(u)
    def ppf(self, u):
        return self.d.ppf(self.cdf_a + u * self.cdf_w)
    def cdf(self, x):
        return np.minimum(1, (self.a <= x) * (self.d.cdf(x) - self.cdf_a) / self.cdf_w)
    def mean(self):
        # The truncated mean is unfortunately not analytical
        return quad(lambda x: x * self.pdf(x), self.a, self.b)[0]

        # XXX: The Darth Vader only applies to positive random variables
        # http://thirdorderscientist.org/homoclinic-orbit/2013/6/25/the-darth-vader-rule-mdash-or-computing-expectations-using-survival-functions
        # https://content.sciendo.com/view/journals/tmmp/52/1/article-p53.xml
#        return quad(self.sf, self.a, self.b)[0] + self.a


def show_distr(D, a, b, resolution=1000):
    xs = np.linspace(a, b, resolution)
    us = np.linspace(0, 1, resolution)
    fig, ax = pl.subplots(figsize=(12,4), ncols=3)

    ax[0].plot(xs, D.pdf(xs))
    ax[0].set_ylabel('f(x)')
    ax[0].set_xlabel('x')
    ax[0].set_title('probability density function')
    ax[0].set_xlim(a, b)


    ax[1].plot(xs, D.cdf(xs))
    ax[1].set_ylabel('F(x)')
    ax[1].set_xlabel('x')
    ax[1].set_title('cumulative distribution function')
    ax[1].set_xlim(a, b)


    ax[2].plot(us, D.ppf(us))
    ax[2].set_ylabel('$F^{-1}(u)$')
    ax[2].set_xlabel('u')
    ax[2].set_xlim(0, 1)
    ax[2].set_title('quantile function')

    fig.tight_layout()

    for a in ax:
        # Move left and bottom spines outward by 10 points
        a.spines['left'].set_position(('outward', 10))
        a.spines['bottom'].set_position(('outward', 10))
        # Hide the right and top spines
        a.spines['right'].set_visible(False)
        a.spines['top'].set_visible(False)
        # Only show ticks on the left and bottom spines
        a.yaxis.set_ticks_position('left')
        a.xaxis.set_ticks_position('bottom')

    return ax


def compare_samples_to_distr(D, samples, a, b, bins):

    fig, ax = pl.subplots(figsize=(12,4), ncols=3)

    ax[0].hist(samples, bins=bins, color='b', alpha=0.5, density=True,
               label='histogram')

    xs = np.linspace(a, b, 1000)
    ax[0].plot(xs, D.pdf(xs), c='k')
    ax[2].set_title('pdf/histogram')

    E = Empirical(samples)

    ax[1].plot(xs, E.cdf(xs), alpha=0.5, linestyle=':')
    ax[1].plot(xs, D.cdf(xs), alpha=0.5)
    ax[1].set_title('cdf')

    us = np.linspace(0, 1, 1000)
    ax[2].plot(us, E.ppf(us), alpha=0.5, linestyle=':')
    ax[2].plot(us, D.ppf(us), alpha=0.5)
    ax[2].set_title('ppf')


    fig.tight_layout()

    for a in ax:
        # Move left and bottom spines outward by 10 points
        a.spines['left'].set_position(('outward', 10))
        a.spines['bottom'].set_position(('outward', 10))
        # Hide the right and top spines
        a.spines['right'].set_visible(False)
        a.spines['top'].set_visible(False)
        # Only show ticks on the left and bottom spines
        a.yaxis.set_ticks_position('left')
        a.xaxis.set_ticks_position('bottom')

    return ax


def test_truncated_distribution():

    import pylab as pl
    import scipy.stats as st
    d = st.lognorm(1.25)

    t = TruncatedDistribution(d, 2, 4)

    print(t.mean(), t.rvs(100_000).mean())

    if 1:
        us = np.linspace(0.01, 0.99, 1000)
        xs = np.linspace(d.ppf(0.01), d.ppf(0.99), 1000)
        pl.plot(xs, t.cdf(xs), label='cdf')
        pl.plot(t.ppf(us), us, label='ppf')
        pl.legend(loc='best')
        pl.xlim(0, 6)
        pl.show()

    if 1:
        pl.hist(t.rvs(100000), density=True, bins=200)
        pl.plot(xs, t.pdf(xs), c='r', lw=3, alpha=0.75)
        pl.xlim(0, 6)
        pl.show()

    if 1:
        us = np.linspace(0.01, 0.99, 100)
        for u in us:
            v = t.cdf(t.ppf(u))
            assert abs(u - v)/abs(u) < 1e-3

    if 1:
        xs = np.linspace(1, 5, 1000)
        for x in xs:
            y = t.ppf(t.cdf(x))
            if t.pdf(x) > 0:
                err = abs(x - y)/abs(x)
                assert err < 1e-3, [err, x, y]


def random_dist(*size):
    """
    Generate a random conditional distribution which sums to one over the last
    dimension of the input dimensions.
    """
    return np.random.dirichlet(np.ones(size[-1]), size=size[:-1])


def random_psd(n):
    return st.wishart.rvs(df=n, scale=np.eye(n)) / n


class Mixture(object):
    """
    Mixture of several densities
    """
    def __init__(self, w, pdfs):
        w = array(w)
        assert is_distribution(w), \
            'w is not a prob. distribution.'
        self.pdfs = pdfs
        self.w = w

    def rvs(self, size=1):
        # sample component
        i = sample(self.w, size=size)
        # sample from component
        return array([self.pdfs[j].rvs() for j in i])

    def pdf(self, x):
        return sum([p.pdf(x) * w for w, p in zip(self.w, self.pdfs)])


def spherical(size):
    "Generate random vector from spherical Gaussian."
    x = normal(0, 1, size=size)
    x /= norm(x, 2)
    return x



# TODO: Should we create a class to represent this data with this the fit
# method?  This should really be the MLE of some sort of distrbution.  What
# distribution is it?  I suppose it is nonparametric in the same sense that
# Kaplan-Meier is nonparametric (In fact, KM generalizes this estimator to
# support censored response).
# TODO: That same class would probably have the defacto mean/std estimators.
class Empirical:
    """
    Empirical CDF of data `a`, returns function which makes values to their
    cumulative probabilities.

     >>> g = cdf([5, 10, 15])

    Evaluate the CDF at a few points

     >>> g([5,9,13,15,100])
     array([0.33333333, 0.33333333, 0.66666667, 1.        , 1.        ])


    Check that ties are handled correctly

     >>> g = cdf([5, 5, 15])

     The value p(x <= 5) = 2/3

     >>> g([0, 5, 15])
     array([0.        , 0.66666667, 1.        ])

    The auantile function should be the inverse of the cdf.

      >>> g = cdf([-1, 5, 5, 15])
      >>> g.quantile(np.linspace(0, 1, 10))
      array([-1, -1, -1,  5,  5,  5,  5,  5,  5, 15])

    """

    def __init__(self, x):
        self.x = x = np.array(x, copy=True)
        [self.n] = x.shape
        self.x.sort()

    def __call__(self, z):
        return self.x.searchsorted(z, 'right') / self.n

    cdf = __call__

    def sf(self, z):
        return 1-self.cdf(z)

    def conditional_mean(self, a, b):
        "E[T | a <= T < b]"
        m = 0.0; n = 0.0
        for i in range(self.x.searchsorted(a, 'right'),
                       self.x.searchsorted(b, 'left')):
            m += self.x[i]
            n += 1
        return m / n if n > 0 else np.inf

    def quantile(self, q):
        # TODO: this could be made fastet given that x is already sorted.
        assert np.all((0 <= q) & (q <= 1))
        return np.quantile(self.x, q, interpolation='lower')

    ppf = quantile

cdf = Empirical


def sample(w, size=None, u=None):
    """
    Uses the inverse CDF method to return samples drawn from an (unnormalized)
    discrete distribution.
    """
    c = cumsum(w)
    if u is None:
        assert size is None
        u = uniform(0,1,size=size)
    return c.searchsorted(u * c[-1])


def log_sample(w):
    "Sample from unnormalized log-distribution."
    a = w - w.max()
    exp(a, out=a)
    return sample(a)


if __name__ == '__main__':
    test_truncated_distribution()
