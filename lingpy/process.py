from lingpy import *
from lingpy.evaluate.acd import bcubes, diff
from lingpy.compare.sanity import mutual_coverage_check, mutual_coverage
from segments.tokenizer import Tokenizer


# load data and add ids

def pre_prepare():
    csv = csv2list('DravLex-2017-04-23.csv', strip_lines=False)
    D = {0: ['language', 'concept', 'cogid', 'cognacy', 'value', 'borrowing']}
    for cognacy, cogid, language, lexeme, lexeme_id, status in csv[1:]:
        if lexeme.strip():
            idx = int(lexeme_id)
            concept = cognacy[:cognacy.index('-')]
            D[idx] = [language, concept, cogid, cognacy, lexeme, status]
        else:
            print('[!] Warning lexeme {0} does not contain an entry.'.format(
                lexeme_id))
    return Wordlist(D)

def parse_first():
    """
    Add ids, make regular wordlist, make list of languages, make concept list.
    """
    wl = pre_prepare()

    # define explicit replacements
    repl = {
            "la:ʋu(adjective)": "la:ʋu",
            "ir(ḍu)": "ir",
            "koʋʋu (noun)": "koʋʋu",
            }
    
    # write language list (with coverage)
    with open('languages.csv', 'w') as f:
        f.write('NAME,CONCEPTS,WORDS,GLOTTOLOG\n')
        for lang in wl.cols:
            cnc = len([x for x, y in wl.get_dict(col=lang).items() if y])
            wrd = len(wl.get_dict(col=lang, flat=True))
            f.write('{0},{1},{2},\n'.format(lang, cnc, wrd))

    # write concept list (with coverage)
    with open('concepts.tsv', 'w') as f:
        f.write('NUMBER\tENGLISH\tLANGUAGES\n')
        for i, c in enumerate(wl.rows):
            cnc = len([k for k, v in wl.get_dict(row=c).items() if v])
            f.write(str(i+1)+'\t'+c+'\t'+str(cnc)+'\n')
    
    # add form, splitting bad values
    wl.add_entries('form', 'value', lambda x: repl.get(x, x).split(' ~ ')[0])

    # get the tokenizer
    t = Tokenizer('profile.tsv')
    wl.add_entries('tokens', 'form', lambda x: t(x, 'IPA').split(' '))

    
    # write data to file
    wl.output('tsv', filename='DravLex', ignore='all', prettify=False)
            
    return wl

def thresholds():

    wl = parse_first()
    lex = LexStat(wl, check=True)
    lex.get_scorer(runs=10000)
    lex.add_entries('nobor', 'cogid,borrowing', lambda x,y:
            str(x[y[0]])+'-'+x[y[1]])
    lex.renumber('nobor')
    for i in range(1, 20):
        tr = i * 0.05
        trn = 't_'+str(i)
        lex.cluster(method='lexstat', threshold=tr, ref=trn,
            cluster_method='infomap')
        a, b, c = bcubes(lex, 'noborid', trn, pprint=False)
        print('Accuracy: T: {3:.2f}, P: {0:.2f}, R: {1:.2f}, FS: {2:.2f}'.format(a,
            b, c, tr))

def cognates():
    wl = parse_first()
    lex = LexStat(wl, check=True)
    lex.get_scorer(runs=10000)
    lex.add_entries('nobor', 'cogid,borrowing', lambda x,y:
            str(x[y[0]])+'-'+x[y[1]])
    lex.renumber('nobor')

    best_t = 0.55
    lex.cluster(method='lexstat', threshold=best_t, ref='lexstatid')
    lex.output('paps.nex', filename='DravLex', missing='?')


    alm = Alignments(lex, ref='cogid')
    alm.align(scoredict=lex.cscorer)
    alm.output('tsv', filename='DravLex-aligned', ignore='all',
            prettify=False)

    diff(lex, 'cogid', 'lexstatid', filename='DravLex.tsv')

def coverage():

    wl = pre_prepare()
    for i in range(wl.height, 0, -1):
        if mutual_coverage_check(wl, i):
            print("Mutual coverage is {0}.".format(i))
            break

    # TODO: average mutual coverage computation
    mucu = mutual_coverage(wl)
    sums = []
    for t in wl.cols:
        sums += [sum(mucu[t].values()) / len(mucu[t])]
    print("Average mutual coverage is {0:.2f}".format(
        sum(sums) / len(sums)))


if __name__ == '__main__':
    from sys import argv
    import os
    if 'prepare' in argv:
        parse_first()
    if 'coverage' in argv:
        coverage()
    if 'profile' in argv:
        os.system('lingpy profile -i DravLex.tsv --column=form -o oprofile.tsv')
    if 'cognates' in argv:
        cognates()
    if 'thresholds' in argv:
        thresholds()
    
    if len(argv) == 1:
        print('Usage: python process.py [prepare, coverage, profile, cognates]')

