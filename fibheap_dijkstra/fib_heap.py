"""Фибоначчиева куча (min-heap).

Амортизированная сложность операций:

    insert        O(1)
    get_min       O(1)
    merge         O(1)
    decrease_key  O(1)
    delete_min    O(log n)
    delete        O(log n)
"""


class FibNode:
    __slots__ = ("key", "value", "parent", "child", "left", "right", "degree", "mark")

    def __init__(self, key, value=None):
        self.key = key
        self.value = value
        self.parent = None
        self.child = None  # любой из детей; дети образуют кольцевой двусвязный список
        self.left = self
        self.right = self
        self.degree = 0  # количество детей
        self.mark = False  # терял ли узел ребёнка с момента, как сам стал чьим-то ребёнком

    def __repr__(self):
        return f"FibNode(key={self.key!r}, value={self.value!r})"


def _splice(a, b):
    """Склеивает два кольцевых списка, содержащих узлы a и b, в один."""
    a_right = a.right
    b_left = b.left
    a.right = b
    b.left = a
    b_left.right = a_right
    a_right.left = b_left


def _unlink(node):
    """Вынимает узел из его кольцевого списка, оставляя его одиночным кольцом."""
    node.left.right = node.right
    node.right.left = node.left
    node.left = node
    node.right = node


def _siblings(node):
    """Все узлы кольцевого списка, начиная с node."""
    result = [node]
    current = node.right
    while current is not node:
        result.append(current)
        current = current.right
    return result


class FibHeap:
    def __init__(self):
        self.size = 0
        self.min = None  # узел с минимальным ключом; через него доступен весь список корней

    def __len__(self):
        return self.size

    def is_empty(self):
        return self.size == 0

    def insert(self, key, value=None):
        """Добавляет элемент и возвращает его узел (он нужен для decrease_key и delete)."""
        node = FibNode(key, value)
        self._add_root(node)
        self.size += 1
        return node

    def get_min(self):
        """Узел с минимальным ключом или None, если куча пуста."""
        return self.min

    def merge(self, other):
        """Переносит все элементы other в эту кучу; other становится пустой."""
        if other is self or other.min is None:
            return
        if self.min is None:
            self.min = other.min
        else:
            _splice(self.min, other.min)
            if other.min.key < self.min.key:
                self.min = other.min
        self.size += other.size
        other.min = None
        other.size = 0

    def delete_min(self):
        """Извлекает и возвращает узел с минимальным ключом."""
        z = self.min
        if z is None:
            raise IndexError("delete_min from empty heap")

        if z.child is not None:
            for child in _siblings(z.child):
                child.parent = None
                child.mark = False
            _splice(z, z.child)
            z.child = None

        if z.right is z:
            self.min = None
        else:
            self.min = z.right
            _unlink(z)
            self._consolidate()

        z.degree = 0
        self.size -= 1
        return z

    def decrease_key(self, node, new_key):
        """Уменьшает ключ узла node до new_key."""
        if new_key > node.key:
            raise ValueError("new key is greater than current key")
        node.key = new_key
        parent = node.parent
        if parent is not None and node.key < parent.key:
            self._cut(node, parent)
            self._cascading_cut(parent)
        if node.key < self.min.key:
            self.min = node

    def delete(self, node):
        """Удаляет узел node из кучи."""
        parent = node.parent
        if parent is not None:
            self._cut(node, parent)
            self._cascading_cut(parent)
        # Узел теперь в списке корней; делаем его минимумом без изменения ключа,
        # чтобы не зависеть от типа ключей (вместо уменьшения до -inf).
        self.min = node
        self.delete_min()

    def _add_root(self, node):
        node.parent = None
        node.mark = False
        if self.min is None:
            node.left = node
            node.right = node
            self.min = node
        else:
            _splice(self.min, node)
            if node.key < self.min.key:
                self.min = node

    def _consolidate(self):
        """Сливает корни одинаковой степени, пока все степени корней не станут различны."""
        degree_table = []
        for root in _siblings(self.min):
            x = root
            d = x.degree
            while True:
                while d >= len(degree_table):
                    degree_table.append(None)
                y = degree_table[d]
                if y is None:
                    break
                if y.key < x.key:
                    x, y = y, x
                self._link(y, x)
                degree_table[d] = None
                d += 1
            degree_table[d] = x

        self.min = None
        for node in degree_table:
            if node is not None and (self.min is None or node.key < self.min.key):
                self.min = node

    def _link(self, child, parent):
        """Делает корень child ребёнком корня parent."""
        _unlink(child)
        child.parent = parent
        child.mark = False
        if parent.child is None:
            parent.child = child
        else:
            _splice(parent.child, child)
        parent.degree += 1

    def _cut(self, node, parent):
        """Отрезает node от parent и переносит в список корней."""
        if node.right is node:
            parent.child = None
        else:
            if parent.child is node:
                parent.child = node.right
            _unlink(node)
        parent.degree -= 1
        self._add_root(node)

    def _cascading_cut(self, node):
        parent = node.parent
        while parent is not None:
            if not node.mark:
                node.mark = True
                return
            self._cut(node, parent)
            node = parent
            parent = node.parent
