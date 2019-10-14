"""Test timing model functions to test out the residuals class."""
from __future__ import absolute_import, division, print_function

import numpy
from astropy.time import Time


def F0(toa, model):

    dt = toa.get_mjds(high_precision=True) - numpy.array(
        Time(model.PEPOCH.value, format="pulsar_mjd", scale="utc"))
    # Can use dt[n].jd1 and jd2 with mpmath here if necessary
    ph = numpy.array([x.sec*model.F0.value for x in dt])

    return ph