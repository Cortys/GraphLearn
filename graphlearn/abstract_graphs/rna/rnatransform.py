import logging
import eden.converter.rna as converter
import graphlearn.abstract_graphs.rna
import graphlearn.abstract_graphs.rna.fold
import graphlearn.abstract_graphs.rna.rnadecomposer
from graphlearn.abstract_graphs.minortransform import GraphTransformerMinorDecomp as default_preprocessor
from graphlearn.transform import GraphTransformer
from sklearn.cluster import KMeans
logger = logging.getLogger(__name__)


class GraphTransformerRNA(GraphTransformer):
    def __init__(self,
                       shape_cluster=KMeans(n_clusters=2),
                       structure_mod=False,
                       name_cluser=False,
                       save_graphclusters=False):
        """
        Parameters
        ----------
        base_thickness_list: list of int
            thickness of the base graph
        shape_cluster: clasifier
            used to determine the shape of the subgraphs
        structure_mod: bool
            some changes to the RNA graph, that help us do the substitutions.
            this is mainly interesting if you use the forgi abstraction method
        name_cluser:bool
            learn to label clusters
        save_graphclusters:bool
            does nothing
        Returns
        -------
            void
        """
        #super(RnaPreProcessor, self).__init__(base_thickness_list=base_thickness_list,kmeans_clusters=kmeans_clusters)

        self.shape_clusters = shape_cluster
        self.structure_mod = structure_mod

    def fit(self, inputs, vectorizer):
        """

        Parameters
        ----------
        inputs: [rna seq]
        vectorizer:  a vectorizer

        Returns
        -------
        self
        """

        self.vectorizer = vectorizer
        self.NNmodel = graphlearn.abstract_graphs.rna.fold.EdenNNF(n_neighbors=4)
        self.NNmodel.fit(inputs)

        # abstr_input = [ self._sequence_to_base_graph(seq) for seq in inputs ]

        abstr_input = list(self.NNmodel.eden_rna_vectorizer.graphs(inputs))
        self.make_abstract = default_preprocessor(core_shape_cluster= self.shape_clusters,
                                                  name_cluster=False)
        self.make_abstract.set_param(self.vectorizer)
        self.make_abstract.fit(abstr_input)
        logger.debug( "fit pp done" )
        return self

    def fit_transform(self, inputs):
        """

        Parameters
        ----------
        inputs: [rna seq]

        Returns
        -------
        list of graphdecomposer
        """
        inputs = list(inputs)
        self.fit(inputs, self.vectorizer)
        inputs = [b for a, b in inputs]
        return self.transform(inputs)

    def re_transform_single(self, graph):
        """

        Parameters
        ----------
        graph:  digraph

        Returns
        -------
        wrapped graph
        """
        try:
            sequence = graphlearn.abstract_graphs.rna.get_sequence(graph)
        except:
            logger.debug('sequenceproblem: this is not an rna')
            # from graphlearn.utils import draw
            # print 'sequenceproblem:'
            # draw.graphlearn(graph, size=20)
            return None

        sequence = sequence.replace("F", '')
        return self.transform([sequence])[0]

    def _sequence_to_base_graph(self, sequence):
        '''

        Parameters
        ----------
        sequence: rna sequence

        Returns
        -------
        nx.graph
        '''
        structure,sequence = self.NNmodel.transform_single(sequence)
        base_graph = converter.sequence_dotbracket_to_graph(seq_info=sequence, \
                                                                seq_struct=structure)
        return base_graph

    def transform(self, sequences):
        """
        Parameters
        ----------
        sequences : iterable over rna sequences

        Returns
        -------
            list of RnaGraphWrappers
        """

        result = []
        for sequence in sequences:
            if type(sequence) == str:
                structure, energy ,sequence = self.NNmodel.transform_single(('fake', sequence))

                base_graph = converter.sequence_dotbracket_to_graph(seq_info=sequence, \
                                                                        seq_struct=structure)
                base_graph.graph['sequence']=sequence
                base_graph.graph['structure']=structure

                abstract_graph = self.make_abstract.abstract(base_graph.copy())

                base_graph = self.vectorizer._edge_to_vertex_transform(base_graph)

                base_graph = graphlearn.abstract_graphs.rna.expanded_rna_graph_to_digraph(base_graph)

                result.append((sequence,structure,base_graph,abstract_graph))

            # up: normal preprocessing case, down: hack to avoid overwriting the postprocessor
            # needs some changing obviously
            else:
                result.append(self.re_transform_single(sequence))
        return result
