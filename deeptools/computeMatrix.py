#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
from deeptools.parserCommon import writableFile, numberOfProcessors
from deeptools import parserCommon
from deeptools import heatmapper
import deeptools.computeMatrixOperations as cmo
from importlib.metadata import version


def parse_arguments(args=None):
    parser = \
        argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description="""

This tool calculates scores per genome regions and prepares an intermediate file that can be used with ``plotHeatmap`` and ``plotProfiles``.
Typically, the genome regions are genes, but any other regions defined in a BED file can be used.
computeMatrix accepts multiple score files (bigWig format) and multiple regions files (BED format).
This tool can also be used to filter and sort regions according
to their score.

To learn more about the specific parameters, type:

$ computeMatrix reference-point --help or

$ computeMatrix scale-regions --help

""",
            epilog='An example usage is:\n  computeMatrix reference-point -S '
            '<bigwig file(s)> -R <bed file(s)> -b 1000\n \n')

    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(version('deeptools')))

    subparsers = parser.add_subparsers(
        title='Commands',
        dest='command',
        metavar='')

    # scale-regions mode options
    subparsers.add_parser(
        'scale-regions',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[
            computeMatrixRequiredArgs(),
            computeMatrixOutputArgs(),
            computeMatrixOptArgs(case='scale-regions'),
            parserCommon.gtf_options()
        ],
        help="In the scale-regions mode, all regions in the BED file are "
        "stretched or shrunken to the length (in bases) indicated by the user.",
        usage='An example usage is:\n  computeMatrix scale-regions -S '
        '<biwig file(s)> -R <bed file> -b 1000\n\n')

    # reference point arguments
    subparsers.add_parser(
        'reference-point',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[computeMatrixRequiredArgs(),
                 computeMatrixOutputArgs(),
                 computeMatrixOptArgs(case='reference-point'),
                 parserCommon.gtf_options()
                 ],
        help="Reference-point refers to a position within a BED region "
        "(e.g., the starting point). In this mode, only those genomic"
        "positions before (upstream) and/or after (downstream) of the "
        "reference point will be plotted.",
        usage='An example usage is:\n  computeMatrix reference-point -S '
        '<biwig file(s)> -R <bed file> -a 3000 -b 3000\n\n')

    return parser


def computeMatrixRequiredArgs(args=None):
    parser = argparse.ArgumentParser(add_help=False)
    required = parser.add_argument_group('Required arguments')
    required.add_argument('--regionsFileName', '-R',
                          metavar='File',
                          help='File name or names, in BED or GTF format, containing '
                               'the regions to plot. If multiple bed files are given, each one is considered a '
                               'group that can be plotted separately. Also, adding a "#" symbol in the bed file '
                               'causes all the regions until the previous "#" to be considered one group.',
                          nargs='+',
                          required=True)
    required.add_argument('--scoreFileName', '-S',
                          help='bigWig file(s) containing '
                          'the scores to be plotted. Multiple files should be separated by spaced. BigWig '
                          'files can be obtained by using the bamCoverage '
                          'or bamCompare tools. More information about '
                          'the bigWig file format can be found at '
                          'http://genome.ucsc.edu/goldenPath/help/bigWig.html ',
                          metavar='File',
                          nargs='+',
                          required=True)
    return parser


def computeMatrixOutputArgs(args=None):
    parser = argparse.ArgumentParser(add_help=False)
    output = parser.add_argument_group('Output options')
    output.add_argument('--outFileName', '-out', '-o',
                        help='File name to save the gzipped matrix file '
                        'needed by the "plotHeatmap" and "plotProfile" tools.',
                        type=writableFile,
                        required=True)

    output.add_argument('--outFileNameMatrix',
                        help='If this option is given, then the matrix '
                        'of values underlying the heatmap will be saved '
                        'using the indicated name, e.g. IndividualValues.tab.'
                        'This matrix can easily be loaded into R or '
                        'other programs.',
                        metavar='FILE',
                        type=writableFile)
    output.add_argument('--outFileSortedRegions',
                        help='File name in which the regions are saved '
                        'after skiping zeros or min/max threshold values. The '
                        'order of the regions in the file follows the sorting '
                        'order selected. This is useful, for example, to '
                        'generate other heatmaps keeping the sorting of the '
                        'first heatmap. Example: Heatmap1sortedRegions.bed',
                        metavar='BED file',
                        type=argparse.FileType('w'))
    return parser


def computeMatrixOptArgs(case=['scale-regions', 'reference-point'][0]):

    parser = argparse.ArgumentParser(add_help=False)
    optional = parser.add_argument_group('Optional arguments')
    optional.add_argument('--version', action='version',
                          version='%(prog)s {}'.format(version('deeptools')))

    if case == 'scale-regions':
        optional.add_argument('--regionBodyLength', '-m',
                              default=1000,
                              type=int,
                              help='Distance in bases to which all regions will '
                              'be fit. (Default: %(default)s)')
        optional.add_argument('--startLabel',
                              default='TSS',
                              help='Label shown in the plot for the start of '
                              'the region. Default is TSS (transcription '
                              'start site), but could be changed to anything, '
                              'e.g. "peak start". Note that this is only '
                              'useful if you plan to plot the results yourself '
                              'and not, for example, with plotHeatmap, which '
                              'will override this. (Default: %(default)s)')
        optional.add_argument('--endLabel',
                              default='TES',
                              help='Label shown in the plot for the region '
                              'end. Default is TES (transcription end site). '
                              'See the --startLabel option for more '
                              'information. (Default: %(default)s) ')
        optional.add_argument('--beforeRegionStartLength', '-b', '--upstream',
                              default=0,
                              type=int,
                              help='Distance upstream of the start site of '
                              'the regions defined in the region file. If the '
                              'regions are genes, this would be the distance '
                              'upstream of the transcription start site. (Default: %(default)s)')
        optional.add_argument('--afterRegionStartLength', '-a', '--downstream',
                              default=0,
                              type=int,
                              help='Distance downstream of the end site '
                              'of the given regions. If the '
                              'regions are genes, this would be the distance '
                              'downstream of the transcription end site. (Default: %(default)s)')
        optional.add_argument("--unscaled5prime",
                              default=0,
                              type=int,
                              help='Number of bases at the 5-prime end of the '
                              'region to exclude from scaling. By default, '
                              'each region is scaled to a given length (see the --regionBodyLength option). In some cases it is useful to look at unscaled signals around region boundaries, so this setting specifies the number of unscaled bases on the 5-prime end of each boundary. (Default: %(default)s)')
        optional.add_argument("--unscaled3prime",
                              default=0,
                              type=int,
                              help='Like --unscaled5prime, but for the 3-prime '
                              'end. (Default: %(default)s)')

    elif case == 'reference-point':
        optional.add_argument('--referencePoint',
                              default='TSS',
                              choices=['TSS', 'TES', 'center'],
                              help='The reference point for the plotting '
                              'could be either the region start (TSS), the '
                              'region end (TES) or the center of the region. '
                              'Note that regardless of what you specify, '
                              'plotHeatmap/plotProfile will default to using "TSS" as the '
                              'label. (Default: %(default)s)')

        # set region body length to zero for reference point mode
        optional.add_argument('--regionBodyLength', help=argparse.SUPPRESS,
                              default=0, type=int)
        optional.add_argument('--unscaled5prime', default=0, type=int, help=argparse.SUPPRESS)
        optional.add_argument('--unscaled3prime', default=0, type=int, help=argparse.SUPPRESS)
        optional.add_argument('--beforeRegionStartLength', '-b', '--upstream',
                              default=500,
                              type=int,
                              metavar='INT bp',
                              help='Distance upstream of the reference-point '
                              'selected. (Default: %(default)s)')
        optional.add_argument('--afterRegionStartLength', '-a', '--downstream',
                              default=1500,
                              metavar='INT bp',
                              type=int,
                              help='Distance downstream of the '
                              'reference-point selected. (Default: %(default)s)')
        optional.add_argument('--nanAfterEnd',
                              action='store_true',
                              help='If set, any values after the region end '
                              'are discarded. This is useful to visualize '
                              'the region end when not using the '
                              'scale-regions mode and when the reference-'
                              'point is set to the TSS.')

    optional.add_argument('--binSize', '-bs',
                          help='Length, in bases, of the non-overlapping '
                          'bins for averaging the score over the '
                          'regions length. (Default: %(default)s)',
                          type=int,
                          default=10)

    optional.add_argument('--sortRegions',
                          help='Whether the output file should present the '
                          'regions sorted. The default is to not sort the regions. '
                          'Note that this is only useful if you plan to plot '
                          'the results yourself and not, for example, with '
                          'plotHeatmap, which will override this. Note also that '
                          'unsorted output will be in whatever order the regions '
                          'happen to be processed in and not match the order in '
                          'the input files. If you require the output order to '
                          'match that of the input regions, then either specify '
                          '"keep" or use computeMatrixOperations to resort the '
                          'results file. (Default: %(default)s)',
                          choices=["descend", "ascend", "no", "keep"],
                          default='keep')

    optional.add_argument('--sortUsing',
                          help='Indicate which method should be used for '
                          'sorting. The value is computed for each row.'
                          'Note that the region_length option will lead '
                          'to a dotted line within the heatmap that indicates '
                          'the end of the regions. (Default: %(default)s)',
                          choices=["mean", "median", "max", "min", "sum",
                                   "region_length"],
                          default='mean')

    optional.add_argument('--sortUsingSamples',
                          help='List of sample numbers (order as in matrix), '
                          'that are used for sorting by --sortUsing, '
                          'no value uses all samples, '
                          'example: --sortUsingSamples 1 3',
                          type=int, nargs='+')

    optional.add_argument('--averageTypeBins',
                          default='mean',
                          choices=["mean", "median", "min",
                                   "max", "std", "sum"],
                          help='Define the type of statistic that should be '
                          'used over the bin size range. The '
                          'options are: "mean", "median", "min", "max", "sum" '
                          'and "std". The default is "mean". (Default: %(default)s)')

    optional.add_argument('--missingDataAsZero',
                          help='If set, missing data (NAs) will be treated as zeros. '
                          'The default is to ignore such cases, which will be depicted as black areas in '
                          'a heatmap. (see the --missingDataColor argument '
                          'of the plotHeatmap command for additional options).',
                          action='store_true')

    optional.add_argument('--skipZeros',
                          help='Whether regions with only scores of zero '
                          'should be included or not. Default is to include '
                          'them.',
                          action='store_true')

    optional.add_argument('--minThreshold',
                          default=None,
                          type=float,
                          help='Numeric value. Any region containing a '
                          'value that is less than or equal to this '
                          'will be skipped. This is useful to skip, '
                          'for example, genes where the read count is zero '
                          'for any of the bins. This could be the result of '
                          'unmappable areas and can bias the overall results. (Default: %(default)s)')

    optional.add_argument('--maxThreshold',
                          default=None,
                          type=float,
                          help='Numeric value. Any region containing a value '
                          'greater than or equal to this '
                          'will be skipped. The maxThreshold is useful to '
                          'skip those few regions with very high read counts '
                          '(e.g. micro satellites) that may bias the average '
                          'values. (Default: %(default)s)')

    optional.add_argument('--blackListFileName', '-bl',
                          help="A BED file containing regions that should be excluded from all analyses. Currently this works by rejecting genomic chunks that happen to overlap an entry. Consequently, for BAM files, if a read partially overlaps a blacklisted region or a fragment spans over it, then the read/fragment might still be considered.",
                          metavar="BED file",
                          required=False)

    optional.add_argument('--samplesLabel',
                          help='Labels for the samples. This will then be passed to plotHeatmap and plotProfile. The '
                          'default is to use the file name of the '
                          'sample. The sample labels should be separated '
                          'by spaces and quoted if a label itself'
                          'contains a space E.g. --samplesLabel label-1 "label 2"  ',
                          nargs='+')

    optional.add_argument('--smartLabels',
                          action='store_true',
                          help='Instead of manually specifying labels for the input '
                          'bigWig and BED/GTF files, this causes deepTools to use the file name '
                          'after removing the path and extension.')

    # in contrast to other tools,
    # computeMatrix by default outputs
    # messages and the --quiet flag supresses them
    optional.add_argument('--quiet', '-q',
                          help='Set to remove any warning or processing '
                          'messages.',
                          action='store_true')

    optional.add_argument('--verbose',
                          help='Being VERY verbose in the status messages. --quiet will disable this.',
                          action='store_true')

    optional.add_argument('--scale',
                          help='If set, all values are multiplied by '
                          'this number. (Default: %(default)s)',
                          type=float,
                          default=1)
    optional.add_argument('--numberOfProcessors', '-p',
                          help='Number of processors to use. Type "max/2" to '
                          'use half the maximum number of processors or "max" '
                          'to use all available processors. (Default: %(default)s)',
                          metavar="INT",
                          type=numberOfProcessors,
                          default=1,
                          required=False)
    return parser


def process_args(args=None):
    args = parse_arguments().parse_args(args)

    if len(sys.argv) == 1:
        parse_arguments().print_help()
        sys.exit()

    if args.quiet is True:
        args.verbose = False

    # Ensure before and after region length is positive
    if args.beforeRegionStartLength < 0:
        print(f"beforeRegionStartLength changed from {args.beforeRegionStartLength} into {abs(args.beforeRegionStartLength)}")
        args.beforeRegionStartLength = abs(args.beforeRegionStartLength)
    if args.afterRegionStartLength < 0:
        print(f"afterRegionStartLength changed from {args.afterRegionStartLength} into {abs(args.afterRegionStartLength)}")
        args.afterRegionStartLength = abs(args.afterRegionStartLength)

    if args.command == 'scale-regions':
        args.nanAfterEnd = False
        args.referencePoint = None
    elif args.command == 'reference-point':
        if args.beforeRegionStartLength == 0 and \
                args.afterRegionStartLength == 0:
            sys.exit("\nUpstrean and downstream regions are both "
                     "set to 0. Nothing to output. Maybe you want to "
                     "use the scale-regions mode?\n")

    return args


def main(args=None):

    args = process_args(args)

    parameters = {'upstream': args.beforeRegionStartLength,
                  'downstream': args.afterRegionStartLength,
                  'body': args.regionBodyLength,
                  'bin size': args.binSize,
                  'ref point': args.referencePoint,
                  'verbose': args.verbose,
                  'bin avg type': args.averageTypeBins,
                  'missing data as zero': args.missingDataAsZero,
                  'min threshold': args.minThreshold,
                  'max threshold': args.maxThreshold,
                  'scale': args.scale,
                  'skip zeros': args.skipZeros,
                  'nan after end': args.nanAfterEnd,
                  'proc number': args.numberOfProcessors,
                  'sort regions': args.sortRegions,
                  'sort using': args.sortUsing,
                  'unscaled 5 prime': args.unscaled5prime,
                  'unscaled 3 prime': args.unscaled3prime
                  }

    hm = heatmapper.heatmapper()

    scores_file_list = args.scoreFileName
    hm.computeMatrix(scores_file_list, args.regionsFileName, parameters, blackListFileName=args.blackListFileName, verbose=args.verbose, allArgs=args)
    if args.sortRegions not in ['no', 'keep']:
        sortUsingSamples = []
        if args.sortUsingSamples is not None:
            for i in args.sortUsingSamples:
                if (i > 0 and i <= hm.matrix.get_num_samples()):
                    sortUsingSamples.append(i - 1)
                else:
                    exit("The value {0} for --sortUsingSamples is not valid. Only values from 1 to {1} are allowed.".format(args.sortUsingSamples, hm.matrix.get_num_samples()))
            print('Samples used for ordering within each group: ', sortUsingSamples)

        hm.matrix.sort_groups(sort_using=args.sortUsing, sort_method=args.sortRegions, sample_list=sortUsingSamples)
    elif args.sortRegions == 'keep':
        hm.parameters['group_labels'] = hm.matrix.group_labels
        hm.parameters["group_boundaries"] = hm.matrix.group_boundaries
        cmo.sortMatrix(hm, args.regionsFileName, args.transcriptID, args.transcript_id_designator, verbose=not args.quiet)

    hm.save_matrix(args.outFileName)

    if args.outFileNameMatrix:
        hm.save_matrix_values(args.outFileNameMatrix)

    if args.outFileSortedRegions:
        hm.save_BED(args.outFileSortedRegions)
