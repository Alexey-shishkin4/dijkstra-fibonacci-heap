import heapq
import math
import random
import unittest

from fibheap_dijkstra import build_graph, dijkstra, reconstruct_path


def bellman_ford(graph, source):
    vertices = set(graph)
    for edges in graph.values():
        vertices.update(edges)
    distance = {v: math.inf for v in vertices}
    distance[source] = 0
    for _ in range(len(vertices) - 1):
        changed = False
        for u, edges in graph.items():
            for v, w in edges.items():
                if distance[u] + w < distance[v]:
                    distance[v] = distance[u] + w
                    changed = True
        if not changed:
            break
    return distance


def heapq_dijkstra(graph, source):
    distance = {source: 0}
    queue = [(0, 0, source)]
    counter = 1
    while queue:
        d, _, u = heapq.heappop(queue)
        if d > distance[u]:
            continue
        for v, w in graph.get(u, {}).items():
            if d + w < distance.get(v, math.inf):
                distance[v] = d + w
                heapq.heappush(queue, (d + w, counter, v))
                counter += 1
    return distance


def random_graph(rng, n, m, directed, max_weight=100):
    edges = [(rng.randrange(n), rng.randrange(n), rng.randint(0, max_weight)) for _ in range(m)]
    graph = build_graph(edges, directed=directed)
    for v in range(n):
        graph.setdefault(v, {})
    return graph


class TestDijkstra(unittest.TestCase):
    def assert_distances_equal(self, actual, expected):
        for v, d in expected.items():
            self.assertEqual(actual.get(v, math.inf), d, f"vertex {v!r}")
        for v, d in actual.items():
            self.assertEqual(expected.get(v, math.inf), d, f"vertex {v!r}")

    def assert_valid_tree(self, graph, source, distance, previous):
        """previous задаёт дерево кратчайших путей, согласованное с distance."""
        for v, d in distance.items():
            if v == source or d == math.inf:
                self.assertIsNone(previous[v])
                continue
            u = previous[v]
            self.assertEqual(distance[u] + graph[u][v], d)
            path = reconstruct_path(previous, source, v)
            self.assertEqual(path[0], source)
            self.assertEqual(path[-1], v)
            self.assertEqual(sum(graph[a][b] for a, b in zip(path, path[1:])), d)

    def test_single_vertex(self):
        distance, previous = dijkstra({"a": {}}, "a")
        self.assertEqual(distance, {"a": 0})
        self.assertEqual(previous, {"a": None})

    def test_undirected_example(self):
        graph = build_graph([(0, 1, 5), (0, 2, 10), (1, 3, 12), (2, 3, 5)])
        distance, previous = dijkstra(graph, 0)
        self.assertEqual(distance, {0: 0, 1: 5, 2: 10, 3: 15})
        self.assertEqual(reconstruct_path(previous, 0, 3), [0, 2, 3])

    def test_longer_path_with_fewer_weight_wins(self):
        edges = [(0, 6, 12), (0, 2, 15), (2, 6, 5), (2, 5, 1), (6, 5, 3), (5, 3, 1),
                 (6, 7, 15), (7, 3, 2), (3, 4, 88), (5, 4, 5), (5, 1, 11), (1, 4, 2)]
        graph = build_graph(edges)
        distance, previous = dijkstra(graph, 0)
        self.assertEqual(distance, {0: 0, 1: 22, 2: 15, 3: 16, 4: 20, 5: 15, 6: 12, 7: 18})
        self.assertEqual(reconstruct_path(previous, 0, 4), [0, 6, 5, 4])
        self.assert_valid_tree(graph, 0, distance, previous)

    def test_needs_decrease_key(self):
        # Сначала до "c" находится путь длины 10, потом он улучшается до 3.
        graph = {"s": {"a": 1, "c": 10}, "a": {"b": 1}, "b": {"c": 1}, "c": {"d": 1}, "d": {}}
        distance, previous = dijkstra(graph, "s")
        self.assertEqual(distance, {"s": 0, "a": 1, "b": 2, "c": 3, "d": 4})
        self.assertEqual(reconstruct_path(previous, "s", "d"), ["s", "a", "b", "c", "d"])

    def test_directed_edges_are_one_way(self):
        graph = build_graph([("a", "b", 1), ("b", "c", 1), ("c", "a", 1)], directed=True)
        distance, _ = dijkstra(graph, "b")
        self.assertEqual(distance, {"a": 2, "b": 0, "c": 1})

    def test_unreachable_vertices(self):
        graph = build_graph([(0, 1, 1), (2, 3, 1)])
        distance, previous = dijkstra(graph, 0)
        self.assertEqual(distance, {0: 0, 1: 1, 2: math.inf, 3: math.inf})
        self.assertIsNone(previous[2])
        self.assertEqual(reconstruct_path(previous, 0, 3), [])

    def test_vertex_only_as_neighbor(self):
        distance, previous = dijkstra({"a": {"b": 2}}, "a")
        self.assertEqual(distance, {"a": 0, "b": 2})
        self.assertEqual(reconstruct_path(previous, "a", "b"), ["a", "b"])

    def test_zero_weights(self):
        graph = build_graph([(0, 1, 0), (1, 2, 0), (0, 2, 1)])
        distance, _ = dijkstra(graph, 0)
        self.assertEqual(distance, {0: 0, 1: 0, 2: 0})

    def test_float_weights(self):
        graph = build_graph([(0, 1, 0.5), (1, 2, 0.25), (0, 2, 1.0)])
        distance, _ = dijkstra(graph, 0)
        self.assertEqual(distance[2], 0.75)

    def test_self_loop_ignored(self):
        graph = build_graph([(0, 0, 5), (0, 1, 3)])
        distance, _ = dijkstra(graph, 0)
        self.assertEqual(distance, {0: 0, 1: 3})

    def test_negative_weight_raises(self):
        with self.assertRaises(ValueError):
            dijkstra({0: {1: -1}, 1: {}}, 0)

    def test_unknown_source_raises(self):
        with self.assertRaises(KeyError):
            dijkstra({0: {}}, 1)

    def test_source_path(self):
        _, previous = dijkstra({0: {1: 1}, 1: {}}, 0)
        self.assertEqual(reconstruct_path(previous, 0, 0), [0])

    def test_random_graphs_against_references(self):
        rng = random.Random(42)
        for _ in range(300):
            n = rng.randint(1, 40)
            m = rng.randint(0, n * 4)
            directed = rng.random() < 0.5
            graph = random_graph(rng, n, m, directed, max_weight=rng.choice([1, 5, 100]))
            source = rng.randrange(n)
            distance, previous = dijkstra(graph, source)
            self.assert_distances_equal(distance, bellman_ford(graph, source))
            self.assert_valid_tree(graph, source, distance, previous)

    def test_large_random_graph(self):
        rng = random.Random(7)
        n = 3000
        graph = random_graph(rng, n, 20000, directed=True, max_weight=10**6)
        distance, previous = dijkstra(graph, 0)
        expected = heapq_dijkstra(graph, 0)
        self.assert_distances_equal(distance, expected)
        self.assert_valid_tree(graph, 0, distance, previous)


class TestBuildGraph(unittest.TestCase):
    def test_undirected(self):
        self.assertEqual(build_graph([(1, 2, 3)]), {1: {2: 3}, 2: {1: 3}})

    def test_directed(self):
        self.assertEqual(build_graph([(1, 2, 3)], directed=True), {1: {2: 3}, 2: {}})

    def test_parallel_edges_keep_lightest(self):
        graph = build_graph([(1, 2, 5), (2, 1, 3), (1, 2, 7)])
        self.assertEqual(graph, {1: {2: 3}, 2: {1: 3}})

    def test_empty(self):
        self.assertEqual(build_graph([]), {})


if __name__ == "__main__":
    unittest.main()
