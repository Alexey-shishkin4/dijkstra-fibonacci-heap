"""Алгоритм Дейкстры на фибоначчиевой куче: O(E + V log V)."""

import math

from .fib_heap import FibHeap


def dijkstra(graph, source):
    """Кратчайшие расстояния от source до всех вершин графа.

    graph — словарь смежности {вершина: {сосед: вес}}, веса неотрицательны.
    Вершина может встречаться только как сосед и не быть ключом graph.

    Возвращает (distance, previous):
      distance[v] — длина кратчайшего пути из source в v (math.inf, если v недостижима);
      previous[v] — предыдущая вершина на этом пути (None для source и недостижимых).
    """
    if source not in graph:
        raise KeyError(source)

    distance = {v: math.inf for v in graph}
    previous = {v: None for v in graph}
    distance[source] = 0

    heap = FibHeap()
    nodes = {source: heap.insert(0, source)}  # узлы кучи ещё не обработанных вершин
    done = set()

    while heap:
        u = heap.delete_min().value
        del nodes[u]
        done.add(u)
        for v, weight in graph.get(u, {}).items():
            if weight < 0:
                raise ValueError(f"negative edge weight {u!r} -> {v!r}: {weight}")
            if v in done:
                continue
            new_distance = distance[u] + weight
            if new_distance < distance.get(v, math.inf):
                distance[v] = new_distance
                previous[v] = u
                if v in nodes:
                    heap.decrease_key(nodes[v], new_distance)
                else:
                    nodes[v] = heap.insert(new_distance, v)

    return distance, previous


def reconstruct_path(previous, source, target):
    """Путь из source в target по словарю previous из dijkstra; [] если пути нет."""
    path = [target]
    while path[-1] != source:
        prev = previous.get(path[-1])
        if prev is None:
            return []
        path.append(prev)
    path.reverse()
    return path


def build_graph(edges, directed=False):
    """Строит словарь смежности из рёбер (from, to, weight).

    Из параллельных рёбер сохраняется самое лёгкое.
    """
    graph = {}
    for src, dst, weight in edges:
        graph.setdefault(src, {})
        graph.setdefault(dst, {})
        _add_edge(graph, src, dst, weight)
        if not directed:
            _add_edge(graph, dst, src, weight)
    return graph


def _add_edge(graph, src, dst, weight):
    if dst not in graph[src] or weight < graph[src][dst]:
        graph[src][dst] = weight
