from sklearn.neighbors import KNeighborsClassifier
from difflib import SequenceMatcher
from random import shuffle

from engine.index import IndexReader
from engine.search import Search

import utils
import consts


SEARCHER = Search(IndexReader(consts.INDEX_PATH))


def format_document(doc):
    doc_str = ""
    for k, v in doc.iteritems():
        if k == 'runtime' and v != "":
            doc_str += k.title() + ": " + str(utils.MovieTime(int(v))) + '\n'
        else:
            doc_str += k.title() + ": " + v + '\n'

    return doc_str


def get_raw_documents(id_list):
    '''list of ids -> list of documents'''
    documents = utils.read_file(consts.DOCUMENTS_PATH)

    docs_list = []
    for doc_id in id_list:
        docs_list.append(documents[doc_id])

    return docs_list

def get_documents(id_list):
    '''list of ids -> list of documents'''
    documents = utils.read_file(consts.DOCUMENTS_PATH)

    docs_list = []
    for doc_id in id_list:
        docs_list.append("ID: %i\n%s" % (doc_id, format_document(documents[doc_id])))

    return docs_list


def search(query):
    '''query -> list of documents'''
    hits = SEARCHER.search(query)
    ids = [doc_id for doc_id, rank in hits]
    return get_documents(ids)


# Changes: MW project
def split_documents():
    ''' returns two lists: 1: documents that will be evaluated by the user, 2: rest of the documents. '''
    len_documents = len(utils.read_file(consts.DOCUMENTS_PATH))
    docs_ids = [i for i in xrange(len_documents)]
    shuffle(docs_ids)
    return docs_ids[:20], docs_ids[20:]


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def similarity_function(movie1, movie2):
    dist = 0

    for k in movie1:
        dist += similar(movie1[k], movie2[k])

    return dist


def rank(evaluated_docs, evaluation, docs_to_rank):
    ''' Uses k-nn to rank documents. '''
    scores = []
    num_docs_to_rank = len(docs_to_rank)

    for i in xrange(num_docs_to_rank):
        num_positive = 0
        num_negative = 0
        dists = []

        for j in xrange(20):
            d = similarity_function(docs_to_rank[i], evaluated_docs[j])
            dists.append((j, d))

        dists = sorted(dists, key=lambda t: t[1], reverse=True)[:5]

        for doc_id, d in dists:
            if evaluation[doc_id] == True:
                num_positive += 1
            else:
                num_negative += 1

        if num_negative > num_positive:
            scores.append(True)
        else:
            scores.append(False)

    return scores


def rank_documents(evaluated_docs, evaluation, docs_to_rank):
    ''' ranks the docs according to the user evaluation of the relevance 20 docs '''
    raw_evaluated_docs = get_raw_documents(evaluated_docs)
    raw_docs_to_rank = get_raw_documents(docs_to_rank)

    scores = rank(raw_evaluated_docs, evaluation, raw_docs_to_rank)

    recommend = []

    for i in xrange(len(scores)):
        if scores[i] == True:
            recommend.append(docs_to_rank[i])
            if len(recommend) == 10:
                break

    return recommend


def main():
    print "Consulta:"
    title = raw_input("Title: ")
    genre = raw_input("Genre: ")
    director = raw_input("Director: ")
    date = raw_input("Date (Year): ")
    runtime = int(raw_input("Runtime:\n0 - 0-1 hr\n1 - 1-2 hr\n2 - 2-3 hr\n3 - More than 4 hr\n4 - ANY\n"))

    if runtime >= 0 and runtime < 4:
        runtime = utils.MovieTime(runtime * 60 + 1).quartile()
    else:
        runtime = ""

    query = {}
    query['title'] = title
    query['genre'] = genre
    query['director'] = director
    query['date'] = date
    query['runtime'] = runtime

    print
    docs = search(query)
    print len(docs), "results"

    for doc in docs:
        print doc
        print

def test_recommend():
    evaluated_docs, docs_to_rank = split_documents()
    evaluation = [True for i in xrange(10)] + [False for i in xrange(10)]
    recommended = rank_documents(evaluated_docs, evaluation, docs_to_rank)
    print len(recommended)

if __name__ == '__main__':
    main()
