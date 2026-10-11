# Dijkstra on a Fibonacci heap

Реализация фибоначчиевой кучи и алгоритма Дейкстры на ней на чистом Python, без зависимостей.

Сложность Дейкстры: **O(E + V log V)**.

| Операция кучи  | Амортизированная сложность |
|----------------|----------------------------|
| `insert`       | O(1)                       |
| `get_min`      | O(1)                       |
| `merge`        | O(1)                       |
| `decrease_key` | O(1)                       |
| `delete_min`   | O(log n)                   |
| `delete`       | O(log n)                   |

## Структура

```
fibheap_dijkstra/
    fib_heap.py   # FibHeap, FibNode
    dijkstra.py   # dijkstra, reconstruct_path, build_graph
tests/
    test_fib_heap.py
    test_dijkstra.py
```

## Использование

### Алгоритм Дейкстры

```python
from fibheap_dijkstra import build_graph, dijkstra, reconstruct_path

graph = build_graph([
    (0, 1, 5),
    (0, 2, 10),
    (1, 3, 12),
    (2, 3, 5),
])  # неориентированный; для ориентированного: build_graph(edges, directed=True)

distance, previous = dijkstra(graph, 0)
print(distance)                            # {0: 0, 1: 5, 2: 10, 3: 15}
print(reconstruct_path(previous, 0, 3))    # [0, 2, 3]
```

Граф — словарь смежности `{вершина: {сосед: вес}}`, вершины — любые hashable-объекты,
веса — неотрицательные числа. Для недостижимых вершин расстояние равно `math.inf`.

### Фибоначчиева куча

```python
from fibheap_dijkstra import FibHeap

heap = FibHeap()
a = heap.insert(5, "a")    # insert возвращает узел — он нужен для decrease_key / delete
b = heap.insert(3, "b")
heap.insert(7, "c")

heap.decrease_key(a, 1)
print(heap.get_min().value)     # a
heap.delete(b)
print(heap.delete_min().key)    # 1
print(len(heap))                # 1
```

## Тесты

```bash
python -m unittest -v
```

Тесты кучи после операций проверяют её структурные инварианты: ссылки кольцевых списков, указатели на родителя,
степени, порядок кучи, отметки корней и размер. Кроме того, случайные последовательности операций сверяются
с эталонной моделью и проверяется оценка степени деревьев через числа Фибоначчи.
Дейкстра сверяется с Беллманом–Фордом и с реализацией на `heapq` на случайных графах.
