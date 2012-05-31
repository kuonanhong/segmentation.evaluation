'''
Implementation of the WindowDiff segmentation evaluation metric described in:



@author: Chris Fournier
@contact: chris.m.fournier@gmail.com
'''
#===============================================================================
# Copyright (c) 2011-2012, Chris Fournier
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the author nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#       
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#===============================================================================
from decimal import Decimal
from . import compute_window_size, parser_one_minus_support
from .. import SegmentationMetricError, compute_pairwise, \
    convert_masses_to_positions


def window_diff(hypothesis_positions, reference_positions, window_size=None,
                one_minus=False, lamprier_et_al_2007_fix=False,
                convert_from_masses=False):
    '''
    Calculates the WindowDiff segmentation evaluation metric score for a
    hypothetical segmentation against a reference segmentation for a given
    window size.  The standard method of calculating the window size
    is performed a window size is not specified.
    
    :param hypothesis_positions:     Hypothesis segmentation section labels
                                        sequence.
    :param reference_positions:      Reference segmentation section labels
                                        sequence.
    :param window_size:              The size of the window that is slid over \
                                        the two segmentations used to count \
                                        mismatches (default is None and will \
                                        use the average window size)
    :param one_minus:                Return 1-WindowDiff to make it no longer \
                                         a penalty-metric.
    :param lamprier_et_al_2007_fix:  Apply a fix for improperly counted errors \
                                        at the beginning and end of \
                                        segmentations, provided by \
                                        _[LamprierEtAl2007].
    :param convert_from_masses:      Convert the segmentations provided from \
                                        masses into positions.
    :type hypothesis_positions: list
    :type reference_positions: list
    :type window_size: int
    :type one_minus: bool
    :type lamprier_et_al_2007_fix: bool
    :type convert_from_masses: bool
    
    .. note:: See :func:`segeval.convert_masses_to_positions` for an example of
              the input format.
    '''
    # pylint: disable=C0103,R0913
    # Convert from masses into positions 
    if convert_from_masses:
        reference_positions  = convert_masses_to_positions(reference_positions)
        hypothesis_positions = convert_masses_to_positions(hypothesis_positions)
    # Check for input errors
    if len(reference_positions) != len(hypothesis_positions):
        raise SegmentationMetricError(
                    'Reference and hypothesis segmentations differ in length.')
    # Compute window size to use if unspecified
    if window_size is None:
        window_size = compute_window_size(reference_positions)
    # Create a set of pairs of units from each segmentation to go over using a
    # window
    sum_differences = 0
    units_ref_hyp = None
    phantom_size = window_size - 1
    if lamprier_et_al_2007_fix == False:
        units_ref_hyp = zip(reference_positions, hypothesis_positions)
    else:
        phantom = [0] * phantom_size
        units_ref_hyp = zip(phantom + reference_positions + phantom,
                            phantom + hypothesis_positions + phantom)
    # Slide window over and sum the number of varying windows
    for i in xrange(0, len(units_ref_hyp) - window_size + 1):
        window = units_ref_hyp[i:i+window_size]
        ref_boundaries = 0
        hyp_boundaries = 0
        # For pair in window
        for j in xrange(0, len(window)-1):
            ref_part, hyp_part = zip(*window[j:j+2])
            # Boundary exists in the reference segmentation
            if ref_part[0] != ref_part[1]:
                ref_boundaries += 1
            # Boundary exists in the hypothesis segmentation
            if hyp_part[0] != hyp_part[1]:
                hyp_boundaries += 1
        # If the number of boundaries per segmentation in the window differs
        if ref_boundaries != hyp_boundaries:
            sum_differences += 1
    # Perform final division
    n = len(reference_positions) + 1
    if lamprier_et_al_2007_fix:
        n += phantom_size
    win_diff = Decimal(sum_differences) / (n - window_size)
    if not one_minus:
        return win_diff
    else:
        return Decimal('1.0') - win_diff


def pairwise_window_diff(dataset_masses, one_minus=False,
                         lamprier_et_al_2007_fix=True,
                         convert_from_masses=True):
    '''
    Calculate mean pairwise segmentation F-Measure.
    
    .. seealso:: :func:`window_diff`
    .. seealso:: :func:`segeval.compute_pairwise`
    
    :param dataset_masses: Segmentation mass dataset (including multiple \
                           codings).
    :type dataset_masses: dict
        
    :returns: Mean, standard deviation, variance, and standard error of a \
        segmentation metric.
    :rtype: :class:`decimal.Decimal`, :class:`decimal.Decimal`, \
        :class:`decimal.Decimal`, :class:`decimal.Decimal`
    '''
    def wrapper(hypothesis_masses, reference_masses):
        '''
        Wrapper to provide parameters.
        '''
        return window_diff(hypothesis_masses, reference_masses,
                           one_minus=one_minus,
                           lamprier_et_al_2007_fix=lamprier_et_al_2007_fix,
                           convert_from_masses=convert_from_masses)
    
    return compute_pairwise(dataset_masses, wrapper, permuted=True)


OUTPUT_NAME = 'Mean WindowDiff'
SHORT_NAME  = 'WindowDiff'


def parse(args):
    '''
    Parse this module's metric arguments and perform requested actions.
    '''
    from ..data import load_file
    from ..data.Display import render_mean_values
    
    values = load_file(args)[0]
    one_minus = args['oneminus']
    
    mean, std, var, stderr = pairwise_window_diff(values, one_minus)
    name = SHORT_NAME
    
    if one_minus:
        name = '1 - %s' % name
    
    return render_mean_values(name, mean, std, var, stderr)


def create_parser(subparsers):
    '''
    Setup a command line parser for this module's metric.
    '''
    from ..data import parser_add_file_support
    parser = subparsers.add_parser('wd',
                                   help=OUTPUT_NAME)
    parser_add_file_support(parser)
    parser_one_minus_support(parser)
    parser.set_defaults(func=parse)

