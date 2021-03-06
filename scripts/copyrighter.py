#! /usr/bin/env python
# corrent ssu rRNA gene copy number based on the taxon copy number table from
#   copyrigter.
# by gjr; 080614

"""
Corrent ssu rRNA gene copy number based on the taxon copy number table from 
copyrigter.

% python copyrighter.py <copy.table> <sample.gg.taxonomy> <outfile.table>
"""

import sys
import os
import collections

#EXCLUDE = ['Archaea', 'Eukaryota', 'unknown']
EXCLUDE = []
LEVELS = 7


def read_refcopy(f):
    """
    Parse a taxon string to copy number table
    Return a dictionary with taxon as key and copy number as value

    Parameters
    ----------
    f : str
    	filename of taxon string to copy number table

    Returns
    -------
    dictionary:
        with taxon as key and copy number as value

    """

    d_refcopy = {}
    for n, line in enumerate(open(f)):
        if line.startswith('#'):
            continue

        line = line.rstrip()
        if line == '':
            continue

        _lis = line.split('\t')
        taxa, num, = _lis[:2]
        skip = False
        for word in EXCLUDE:
            if word in taxa:
                skip = True
                break

        if skip:
            continue 

        # the parsing of taxa works for both mothur output and this
        taxa = taxa.rstrip(';')    # for mothur classfy.seqs output
        lis = taxa.split(';')
        lis2 = []
        for item in lis:
            item = item.strip()    # for copyrigher copy table ' ;' separater
            if item.endswith(')'):
                item = item.rsplit('(', 1)[0].strip()

            # remove taxon level prefix, e.g. 'p__Firmicutes'
            if '__' in item:
                item = item.split('__', 1)[1]

            #item = item.strip('"')

            # green gene taxonomy has sapce
            item = item.replace(' ', '_')

            item = item.lower()
            if item == '':
                item = 'Unclassifed'
            elif item == 'unknown':
                item = 'Unclassifed'
            elif item == 'other':
                item = 'Unclassifed'
            elif item == 'unassigned':
                item = 'Unclassifed'

            item = item.capitalize()
            lis2.append(item)

        length = len(lis2)
        assert length <= LEVELS, '> {} levels found ({})'.format(
            LEVELS, length)
        if length != LEVELS:
            lis2 = lis2 + ['Unclassified']*(LEVELS - length)

        tu = tuple(lis2)
        d_refcopy[tu] = float(num)

    return d_refcopy


def read_mothur_taxonomy(f):
    """
    Parse mothur classify.seqs output

    Parameters:
    -----------
    f : str
        file name of .taxonomy file from classify.seqs

    Returns:
    --------
    generator
        an iterable (generator) of tuples (each level of taxonomy)

    """
    for n, line in enumerate(open(f)):
        if line.startswith('#'):
            continue

        line = line.rstrip()
        name, taxa = line.rstrip().split('\t')
        skip = False
        for word in EXCLUDE:
            if word in taxa:
                skip = True
                break

        if skip:
            continue 

        # the parsing of taxa works for both mothur output and this
        taxa = taxa.rstrip(';')    # for mothur classfy.seqs output
        lis = taxa.split(';')
        lis2 = []
        for item in lis:
            item = item.strip()    # for copyrigher copy table ' ;' separater
            if item.endswith(')'):
                item = item.rsplit('(', 1)[0].strip()

            # remove taxon level prefix, e.g. 'p__Firmicutes'
            if '__' in item:
                item = item.split('__', 1)[1]

            #item = item.strip('"')

            # green gene taxonomy has sapce
            item = item.replace(' ', '_')

            item = item.lower()
            if item == '':
                item = 'Unclassifed'
            elif item == 'unknown':
                item = 'Unclassifed'
            elif item == 'unclassified':
                item = 'Unclassifed'
            elif item == 'other':
                item = 'Unclassifed'
            elif item == 'unassigned':
                item = 'Unclassifed'

            item = item.capitalize()
            lis2.append(item)

        length = len(lis2)
        assert length == LEVELS, 'levels ({}) is not ({})'.format(
            length, LEVELS)
        yield tuple(lis2)


def main():
    if len(sys.argv) != 4:
        mes = ('Usage: python {} <copy.table> '
               '<sample.gg.taxonomy> <outfile.table>')
        print >> sys.stderr, mes.format(os.path.basename(sys.argv[0]))
        sys.exit(1)

    copytable = sys.argv[1]
    taxonfile = sys.argv[2]
    outfile = sys.argv[3]

    d_refcopy = read_refcopy(copytable)
    g_taxonomy = read_mothur_taxonomy(taxonfile)
    d_count = collections.Counter(g_taxonomy)
    missing_taxon_cnt = 0
    temp_summ = 0
    temp_cnt = 0
    for key in d_count:
        if key in d_refcopy:
            temp_cnt += 1
            temp_summ += d_refcopy[key]

    average_copy = temp_summ*1.0/temp_cnt
    for key in d_count:
        if key in d_refcopy:
            copy = d_refcopy[key]
        else:
            copy = average_copy
            missing_taxon_cnt += 1
            print >> sys.stderr, '{} is missing in copyrighter'.format(
                ';'.join(key))

        d_count[key] = d_count[key]/copy

    _mes = '{0:d} taxons are not found in copyrighter, {1:.1f} copy per genome is used'
    print >> sys.stderr, _mes.format(missing_taxon_cnt, average_copy)

    with open(outfile, 'wb') as fw:
        for key, cnt in sorted(d_count.items()):
            taxon_string = ';'.join(key)
            print >> fw, '{}\t{}'.format(taxon_string, cnt)

if __name__ == '__main__':
    main()
