'''
Inter-coder agreement statistic Fleiss' Pi.

.. moduleauthor:: Chris Fournier <chris.m.fournier@gmail.com>
'''
from __future__ import division
from decimal import Decimal
from . import __fnc_metric__, __actual_agreement_linear__


def __fleiss_pi_linear__(items_masses, **kwargs):
    # pylint: disable=C0103,R0914,W0142
    metric_kwargs = dict(kwargs)
    metric_kwargs['return_parts'] = True
    # Arguments
    return_parts = kwargs['return_parts']
    # Check that there are an equal number of items for each coder
    num_items = len(items_masses.values()[0].keys())
    if len([True for coder_segs in items_masses.values() \
            if len(coder_segs.values()) is not num_items]) > 0:
        raise Exception('Unequal number of items contained.')
    # Initialize totals
    all_numerators, all_denominators, _, coders_boundaries = \
        __actual_agreement_linear__(items_masses, **metric_kwargs)
    # Calculate Aa
    A_a = Decimal(sum(all_numerators)) / sum(all_denominators)
    # Calculate Ae
    p_e_segs = list()
    for boundaries_info in coders_boundaries.values():
        for item in boundaries_info:
            boundaries, total_boundaries = item
            p_e_seg = Decimal(boundaries) / total_boundaries
            p_e_segs.append(p_e_seg)
    # Calculate P_e_seg
    P_e_seg = Decimal(sum(p_e_segs)) / len(p_e_segs)
    A_e = (P_e_seg ** 2)
    # Calculate pi
    pi = (A_a - A_e) / (Decimal('1') - A_e)
    # Return
    if return_parts:
        return A_a, A_e
    else:
        return pi


def fleiss_pi_linear(dataset, **kwargs):
    # pylint: disable=W0142
    return __fnc_metric__(__fleiss_pi_linear__, dataset, **kwargs)


