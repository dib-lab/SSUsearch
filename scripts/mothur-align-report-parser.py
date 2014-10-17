#! /usr/bin/ python
# parse the mothur aligner report
# by gjr; Mar 25, 11;


import sys
import os
import screed

def parser(f):
    '''
    [0]QueryName	[1]QueryLength	[2]TemplateName	[3]TemplateLength	[4]SearchMethod	[5]SearchScore	[6]AlignmentMethod	[7]QueryStart	[8]QueryEnd	[9]TemplateStart	[10]TemplateEnd	[11]PairwiseAlignmentLength	[12]GapsInQuery	[13]GapsInTemplate	[14]LongestInsert	[15]SimBtwnQuery&Template
    '''
    fp = open(f)
    d = {}
    for line in fp:
        line=line.strip()
        if line.startswith('QueryName'):
            firstLine = line.split()
            continue
        lis = line.split()
        d[lis[0]] = lis

    return d

if __name__ == '__main__':

    '''
    plot the ID (the percent of short read matched to ref aligment seqs)
    distribution remove reads with <50% ID with seeds

    Usage: python <thisFile><mothurAlign.report><file.align> <outfile.filter>
    check percentage of short read matched to SEEDs
    '''
    if len(sys.argv) != 4:
        mes = ('Usage: python'
               '{} <mothurAlign.report> <file.align> <outfile.filter>')
        print >> sys.stderr, mes.format(os.path.basename(sys.argv[0]))
        sys.exit(1)

    MINID = 50
    PLOT = True
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        PLOT = False
        pass
    d = parser(sys.argv[1])

    d_match = {}
    st_goodSeqs = set()
    for key in d:
        qu = d[key][0]
        qu_len = int(d[key][1])
        su = d[key][3]
        ID = float(d[key][-1])
        AL = int(d[key][-5])
        if AL < 0:
            continue
        ID2 = ID*AL/qu_len
        if not d_match.has_key(qu):
            d_match[qu] = ID2
        elif ID*AL/qu_len > d_match[qu]:
            d_match[qu] = ID2
        else:
            pass

        ###get a set of good seqs
        #if ID2 >= 50 or AL*ID/100.0 >= 400:  #for GOS data

        ###two standards based on length
        '''
        if (qu_len < 150 and ID2 >= 75):
            st_goodSeqs.add(qu)
        elif (qu_len > 150 and ID2 > 50):
            st_goodSeqs.add(qu)
        '''

        if (ID2 >= MINID or AL*ID/100.0 >= 80): #for illu shotgun
            st_goodSeqs.add(qu)


    if PLOT:
        n, bins, batches = plt.hist(d_match.values(), 50, cumulative = False, histtype = 'step',label = 'SGvsSeeds')
        plt.xlabel ('Identity')
        plt.ylabel ('# of seqs')
        plt.gca().xaxis.grid(False)
        plt.gca().yaxis.grid(True)

        leg = plt.legend(loc = 'upper left', shadow = True, borderpad = 0.1)
        for t in leg.get_texts():
            t.set_fontsize('small')
        for l in leg.get_lines():
            l.set_linewidth(5) 
        plt.savefig('IDdist.png')
        plt.clf()

    print >> sys.stderr, '%d bad seqs removed from alignment' %((len(d)-len(st_goodSeqs)))
    fw = open(sys.argv[3], 'wb')
    totalSeq = 0
    for n, record in enumerate(screed.open(sys.argv[2])):
        name = record['name']
        totalSeq += 1
        if name not in st_goodSeqs:
            continue
        seq = record['sequence']
        fw.write('>%s\n%s\n' %(name, seq))

    print '%d in %d sequences removed due to bad alignment' %((totalSeq-len(st_goodSeqs)), (totalSeq))