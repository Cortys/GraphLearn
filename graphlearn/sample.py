from graphlearn.util import util
import logging
from graphlearn.choice import SelectMax

logger = logging.getLogger(__name__)

def sample_step(object, transformer, grammar, scorer, selector):
    """
    Parameters
    ----------
    object:
    transformer: test.test(object) -> graph
    grammar: trained on graphs, lsgg.propose(graph) -> objects
    scorer: score.decision_function(object) -> number

    Returns
    -------
        object
    """
    graph = transformer.encode_single(object)
    util.valid_gl_graph(graph)
    proposal_graphs = list(grammar.neighbors_sample(graph,1))+[graph]

    proposal_objects = list(transformer.decode(proposal_graphs))
    scores = scorer.decision_function(proposal_objects)
    logger.info(str(scores) + str(scores[0]/scores[1]))  
    object, score = selector.select(proposal_objects, scores)

    return object, score


def sample(graph, transformer=None, grammar=None, scorer=None, selector=None, n_steps=75, return_score=False):
    for i in range(n_steps):
        graph, score = sample_step(graph, transformer, grammar, scorer,selector)
    if return_score:
        return graph, score
    return graph


def sample_sizeconstraint(graph,penalty=0.01, **kwargs):
    kwargs['scorer'].sizefactor = len(graph)
    kwargs['scorer'].sizepenalty = penalty
    return sample(graph,**kwargs)




def fit():
    pass

def optimize():
    pass




def test_sample_step():
    from graphlearn.score import SimpleDistanceEstimator as SDE
    import networkx as nx
    from graphlearn import choice
    import graphlearn.test.transformutil as transformutil

    lsgg = util.test_get_grammar()
    graph = util._edenize_for_testing(nx.path_graph(4))
    graph.nodes[3]['label'] = '5'
    score_estimator = SDE().fit(util._edenize_for_testing(nx.path_graph(4)))
    graph,score= sample(graph, transformutil.no_transform(), lsgg, score_estimator, choice.SelectMax(), n_steps=2, return_score=True)

    assert (0.000001 > abs(0.319274373045 - score)), score
    print("sambledestdone")

def multi_sample_step(objects, transformer, grammar, scorer, selector, n_neighbors):
    graphs = list(transformer.encode(objects))
    [util.valid_gl_graph(graph) for graph in graphs]
    proposal_graphs = [ prop for graph in graphs for prop in grammar.neighbors_sample_faster(graph,n_neighbors) ]+graphs
    proposal_objects = list(transformer.decode(proposal_graphs))
    scores = scorer.decision_function(proposal_objects)
    objects, scores = selector.select(proposal_objects, scores)
    return objects,scores


def multi_sample(graph, transformer=None, grammar=None, scorer=None, selector=None, n_steps=10, n_neighbors=20):

    # tests are basically in  long_range_graphlearn/code/chem
    graphs=[graph]
    for i in range(n_steps):
        graphs, scores= multi_sample_step(graphs, transformer, grammar, scorer,selector,n_neighbors)
    s=SelectMax()
    return s.select(graphs,scores)[0]
