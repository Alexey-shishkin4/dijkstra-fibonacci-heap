import random
import unittest

from fibheap_dijkstra import FibHeap
from fibheap_dijkstra.fib_heap import _siblings


def check_invariants(test, heap):
    """Проверяет структуру кучи целиком: ссылки, степени, порядок, размер, минимум."""
    if heap.min is None:
        test.assertEqual(heap.size, 0)
        return

    count = 0
    true_min = None

    def walk(first, parent):
        nonlocal count, true_min
        nodes = _siblings(first)
        for node in nodes:
            count += 1
            test.assertIs(node.left.right, node)
            test.assertIs(node.right.left, node)
            test.assertIs(node.parent, parent)
            if parent is not None:
                test.assertLessEqual(parent.key, node.key)
            if true_min is None or node.key < true_min.key:
                true_min = node
            if node.child is None:
                test.assertEqual(node.degree, 0)
            else:
                test.assertEqual(node.degree, len(_siblings(node.child)))
                walk(node.child, node)
        return nodes

    roots = walk(heap.min, None)
    for root in roots:
        test.assertFalse(root.mark)
    test.assertEqual(count, heap.size)
    test.assertEqual(heap.min.key, true_min.key)


def drain(heap):
    result = []
    while heap:
        result.append(heap.delete_min().key)
    return result


class TestBasics(unittest.TestCase):
    def test_empty(self):
        heap = FibHeap()
        self.assertEqual(len(heap), 0)
        self.assertTrue(heap.is_empty())
        self.assertIsNone(heap.get_min())
        with self.assertRaises(IndexError):
            heap.delete_min()

    def test_insert_returns_node_with_key_and_value(self):
        heap = FibHeap()
        node = heap.insert(5, "five")
        self.assertEqual((node.key, node.value), (5, "five"))
        self.assertIs(heap.get_min(), node)
        self.assertEqual(len(heap), 1)

    def test_single_element(self):
        heap = FibHeap()
        heap.insert(1)
        self.assertEqual(heap.delete_min().key, 1)
        self.assertTrue(heap.is_empty())
        self.assertIsNone(heap.get_min())
        heap.insert(2)
        self.assertEqual(heap.get_min().key, 2)

    def test_get_min_tracks_minimum_on_insert(self):
        heap = FibHeap()
        for key, expected_min in [(5, 5), (7, 5), (3, 3), (4, 3), (-1, -1)]:
            heap.insert(key)
            self.assertEqual(heap.get_min().key, expected_min)

    def test_delete_min_returns_sorted_sequence(self):
        heap = FibHeap()
        keys = [36, 48, 4, 16, 7]
        for key in keys:
            heap.insert(key)
        self.assertEqual(drain(heap), sorted(keys))

    def test_duplicates_and_float_keys(self):
        heap = FibHeap()
        keys = [2.5, 1, 1, float("inf"), -3, 2.5, 0, float("-inf")]
        for key in keys:
            heap.insert(key)
        self.assertEqual(drain(heap), sorted(keys))

    def test_values_follow_their_keys(self):
        heap = FibHeap()
        for key in [3, 1, 2]:
            heap.insert(key, f"v{key}")
        values = []
        while heap:
            values.append(heap.delete_min().value)
        self.assertEqual(values, ["v1", "v2", "v3"])

    def test_tuple_keys(self):
        heap = FibHeap()
        keys = [(2, "b"), (1, "z"), (2, "a")]
        for key in keys:
            heap.insert(key)
        self.assertEqual(drain(heap), sorted(keys))


class TestDecreaseKey(unittest.TestCase):
    def test_decrease_root_becomes_min(self):
        heap = FibHeap()
        heap.insert(1)
        node = heap.insert(10)
        heap.decrease_key(node, 0)
        self.assertIs(heap.get_min(), node)
        check_invariants(self, heap)

    def test_decrease_child_below_parent_is_cut(self):
        heap = FibHeap()
        nodes = [heap.insert(k) for k in range(10)]
        heap.delete_min()  # строит деревья
        heap.decrease_key(nodes[9], -1)
        check_invariants(self, heap)
        self.assertIs(heap.get_min(), nodes[9])
        self.assertIsNone(nodes[9].parent)
        self.assertEqual(drain(heap), [-1] + list(range(1, 9)))

    def test_decrease_without_violating_order_keeps_node_in_place(self):
        heap = FibHeap()
        nodes = [heap.insert(k * 10) for k in range(5)]
        heap.delete_min()
        child = next(n for n in nodes[1:] if n.parent is not None)
        parent = child.parent
        heap.decrease_key(child, parent.key + 1)
        self.assertIs(child.parent, parent)
        check_invariants(self, heap)

    def test_decrease_to_same_key_is_allowed(self):
        heap = FibHeap()
        node = heap.insert(5)
        heap.decrease_key(node, 5)
        self.assertEqual(heap.get_min().key, 5)

    def test_increase_raises(self):
        heap = FibHeap()
        node = heap.insert(5)
        with self.assertRaises(ValueError):
            heap.decrease_key(node, 6)
        self.assertEqual(node.key, 5)

    def test_cascading_cut(self):
        # 16 узлов после delete_min сливаются в одно биномиальное дерево B4:
        # root -> a (степень 3) -> b (степень 2) -> 2 листа.
        heap = FibHeap()
        for k in range(17):
            heap.insert(k)
        heap.delete_min()
        root = heap.get_min()
        self.assertEqual(len(_siblings(root)), 1)
        self.assertEqual(root.degree, 4)
        a = next(c for c in _siblings(root.child) if c.degree == 3)
        b = next(c for c in _siblings(a.child) if c.degree == 2)
        leaf1, leaf2 = _siblings(b.child)

        # Первый вырезанный ребёнок только помечает b.
        heap.decrease_key(leaf1, -1)
        self.assertIsNone(leaf1.parent)
        self.assertTrue(b.mark)
        self.assertIs(b.parent, a)
        check_invariants(self, heap)

        # Второй вырезанный ребёнок вырезает b, а a помечается.
        heap.decrease_key(leaf2, -2)
        self.assertIsNone(b.parent)
        self.assertFalse(b.mark)
        self.assertTrue(a.mark)
        self.assertIs(a.parent, root)
        check_invariants(self, heap)

        # Ещё один вырезанный ребёнок a вырезает и a; корень не помечается.
        heap.decrease_key(next(c for c in _siblings(a.child)), -3)
        self.assertIsNone(a.parent)
        self.assertFalse(root.mark)
        check_invariants(self, heap)

        self.assertEqual(heap.get_min().key, -3)
        self.assertEqual(len(drain(heap)), 16)


class TestDelete(unittest.TestCase):
    def test_delete_min_node(self):
        heap = FibHeap()
        heap.insert(2)
        node = heap.insert(1)
        heap.delete(node)
        self.assertEqual(drain(heap), [2])

    def test_delete_inner_node(self):
        heap = FibHeap()
        nodes = [heap.insert(k) for k in range(20)]
        heap.delete_min()
        heap.delete(nodes[7])
        heap.delete(nodes[13])
        check_invariants(self, heap)
        self.assertEqual(drain(heap), [k for k in range(1, 20) if k not in (7, 13)])

    def test_delete_does_not_depend_on_minus_infinity(self):
        heap = FibHeap()
        heap.insert(float("-inf"), "a")
        node = heap.insert(float("-inf"), "b")
        heap.insert(0, "c")
        heap.delete(node)
        values = []
        while heap:
            values.append(heap.delete_min().value)
        self.assertEqual(values, ["a", "c"])

    def test_delete_only_element(self):
        heap = FibHeap()
        node = heap.insert(1)
        heap.delete(node)
        self.assertTrue(heap.is_empty())


class TestMerge(unittest.TestCase):
    def test_merge_two_heaps(self):
        a, b = FibHeap(), FibHeap()
        for k in [5, 1, 9]:
            a.insert(k)
        for k in [4, 0, 8]:
            b.insert(k)
        a.merge(b)
        self.assertEqual(len(a), 6)
        self.assertTrue(b.is_empty())
        self.assertIsNone(b.get_min())
        check_invariants(self, a)
        self.assertEqual(drain(a), [0, 1, 4, 5, 8, 9])

    def test_merge_with_empty(self):
        a, b = FibHeap(), FibHeap()
        a.insert(1)
        a.merge(b)
        self.assertEqual(drain(a), [1])
        b.insert(2)
        a.merge(b)
        self.assertEqual(drain(a), [2])

    def test_merge_with_self_is_noop(self):
        heap = FibHeap()
        heap.insert(1)
        heap.merge(heap)
        self.assertEqual(drain(heap), [1])

    def test_nodes_stay_valid_after_merge(self):
        a, b = FibHeap(), FibHeap()
        a.insert(10)
        node = b.insert(20)
        a.merge(b)
        a.decrease_key(node, 1)
        self.assertEqual(drain(a), [1, 10])


class TestRandomized(unittest.TestCase):
    def test_heapsort(self):
        rng = random.Random(1)
        for _ in range(300):
            keys = [rng.randint(-50, 50) for _ in range(rng.randint(0, 60))]
            heap = FibHeap()
            for key in keys:
                heap.insert(key)
            self.assertEqual(drain(heap), sorted(keys))

    def test_random_operations_against_reference(self):
        rng = random.Random(2)
        for _ in range(100):
            heap = FibHeap()
            alive = {}  # node -> key
            for _ in range(300):
                op = rng.random()
                if op < 0.4 or not alive:
                    key = rng.randint(-1000, 1000)
                    alive[heap.insert(key)] = key
                elif op < 0.6:
                    node = heap.delete_min()
                    self.assertEqual(node.key, min(alive.values()))
                    del alive[node]
                elif op < 0.85:
                    node = rng.choice(list(alive))
                    new_key = node.key - rng.randint(0, 500)
                    heap.decrease_key(node, new_key)
                    alive[node] = new_key
                elif op < 0.95:
                    node = rng.choice(list(alive))
                    heap.delete(node)
                    del alive[node]
                else:
                    other = FibHeap()
                    for _ in range(rng.randint(0, 5)):
                        key = rng.randint(-1000, 1000)
                        alive[other.insert(key)] = key
                    heap.merge(other)

                self.assertEqual(len(heap), len(alive))
                if alive:
                    self.assertEqual(heap.get_min().key, min(alive.values()))
            check_invariants(self, heap)
            self.assertEqual(drain(heap), sorted(alive.values()))

    def test_tree_degrees_are_logarithmic(self):
        # В фибоначчиевой куче поддерево степени k содержит не меньше F(k+2) узлов.
        rng = random.Random(3)
        heap = FibHeap()
        nodes = [heap.insert(rng.random()) for _ in range(2000)]
        removed = heap.delete_min()
        nodes.remove(removed)
        for node in rng.sample(nodes, 500):
            heap.decrease_key(node, node.key - rng.random())
        heap.delete_min()

        def subtree_size(node):
            if node.child is None:
                return 1
            return 1 + sum(subtree_size(c) for c in _siblings(node.child))

        fib = [0, 1]
        while len(fib) < 64:
            fib.append(fib[-1] + fib[-2])
        for root in _siblings(heap.get_min()):
            self.assertGreaterEqual(subtree_size(root), fib[root.degree + 2])
        check_invariants(self, heap)


if __name__ == "__main__":
    unittest.main()
