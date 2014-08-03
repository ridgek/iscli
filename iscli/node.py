# -*- coding: utf-8 -*-
"""
iscli.node
~~~~~~~~~~

Command tree implementation.


When a command is installed it is stored in a prefix-tree.

    show ip connection
    show ip interfaces
    show ip routes
    show system
    show system detail
    show system inventory

    show─┬─ip─┬─connections*
         │    ├─interfaces*
         │    └─routes*
         └─system*─┬─detail*
                   └─inventory*

    (* indicates a command endpoint)


XOR groupings are handled by creating a branch for each alternative.

    foo (bar | baz)

    foo─┬─bar*
        └─baz*


OR groupings are handled by creating a branch for each permuation.

    foo {bar | baz}

    foo─┬─bar*──baz*
        └─baz*──bar*


It can get complicated quickly:

    sshfs HOSTNAME ({username USERNAME | path PATH | port <1-65535>}|)

    sshfs──HOSTNAME*─┬─username──USERNAME*─┬─path──PATH*──port──<1-65535>*
                     │                     └─port──<1-65535>*──path──PATH*
                     ├─path──PATH*─┬─username──USERNAME*──port──<1-65535>*
                     │             └─port──<1-65535>*──username──USERNAME*
                     └─port──<1-65535>*─┬─username──USERNAME*──path──PATH*
                                        └─path──PATH*──username──USERNAME*


Argspec, keyword, fragment, huh?

These are all similar, but have slightly different meanings.

* Argspec: argument specification from command installation.
* Keyword: what is displayed to the user in describe help.
* Fragment: what the user has entered at the command line.

======== ======== ======== ========
type     argspec  keyword  fragment
======== ======== ======== ========
variable 'FOO'    'FOO'    'blah'
vararg   '.FOO'   'FOO'    'blah'
range    '<1-20>' '<1-20>' '5'
"""
import collections
from itertools import chain, permutations, repeat

from .converter import create_converter


class CliElement(object):
    """The element object stores data about an individual argspec in a
    command, a :class:`CliElement` can belong to multiple :class:`CliNode`
    objects.

    :param argspec: argument specification
    :param desc: description for help
    :param is_argument: consider this element an argument
    """
    def __init__(self, argspec, desc='', is_argument=False):

        self.argspec = argspec
        self.keyword = argspec.lstrip('.')
        self.desc = desc

        #: Converter function to match and convert fragments
        self.converter = create_converter(self.keyword)

        #: Include in arguments passed to command handler function
        self.is_argument = is_argument or bool(self.converter)

        #: Recurse on this element (varargs)
        self.is_recursive = argspec.startswith('.')

    def __repr__(self):
        return self.keyword


class CliNode(dict):
    """The node object forms the structure of the command tree.

    :param element: element for this node
    :type element: :class:`CliElement`
    :param fn: command function
    """
    def __init__(self, element, fn=None):
        super(CliNode, self).__init__()
        self.element = element
        self.fn = fn

    @property
    def keyword(self):
        return self.element.keyword

    def lookup(self, *fragments):
        try:
            return reduce(CliNode.get, fragments, self)
        except AttributeError:
            return None

    def parse(self, fragment):
        """Expand or convert fragment

        :param fragment:
        :returns: expanded keyword or value if match else None
        """
        if self.keyword.startswith(fragment):
            return self.keyword
        if self.element.converter:
            match, value = self.element.converter(fragment)
            if match:
                return value
        return None

    def match(self, fragment):
        """Find all matches for a fragment

        :param fragment: fragment to match
        :returns: dictionary of matches. The keys are
        """
        # First try an exact match
        node = self.get(fragment)
        if node is not None:
            return {fragment: node}

        # Maybe we are recursive?
        if self.element.is_recursive and self.parse(fragment) is not None:
            return {self.parse(fragment): self}

        # Do it the long way
        nodes = {n.parse(fragment): n for n in self.itervalues()}
        nodes.pop(None, None)  # Pop non-matches
        return nodes

    def merge(self, node):
        """Recursively merge a node and its children into this node"""
        assert self.keyword == node.keyword

        self.fn = node.fn or self.fn

        ours = set(self.keys())
        theirs = set(node.keys())
        for k in ours.intersection(theirs):
            self[k].merge(node[k])
        for k in (theirs.difference(ours)):
            self[k] = node[k]

    def build(self, elements, fn):
        """Build a command into the tree

        :param elements: output of function:`cmdsplit`
        :param fn: function to install
        """
        node = self
        elements = collections.deque(elements)
        while elements:
            element = elements.popleft()
            if isinstance(element, ElementGroup):
                group = element
                if isinstance(element, ParenGroup):
                    branches = group
                elif isinstance(element, BraceGroup):
                    branches = []
                    for i in xrange(1, len(group) + 1):
                        for p in permutations(group, i):
                            branches.append(chain(*p))
                for branch in branches:
                    node.build(chain(branch, elements), fn)
                return
            else:
                node = node.setdefault(
                    element.keyword,
                    self.__class__(element)
                )
        node.fn = fn

    def __repr__(self):
        return dict.__repr__(self)


class ElementGroup(list):
    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            list.__repr__(self),
        )


class ParenGroup(ElementGroup):
    pass


class BraceGroup(ElementGroup):
    pass


def cmdsplit(cmdspec, desc_seq=None):
    desc = iter(desc_seq) if desc_seq else repeat('')
    cmdspec = cmdspec.strip()
    last = 0
    elements = []
    stack = collections.deque([elements])

    def consume(i):
        argspec = cmdspec[last:i].strip()
        if argspec:
            elem = CliElement(
                argspec,
                desc=next(desc),
                is_argument=(len(stack) > 1)
            )
            stack[-1].append(elem)
        if i is not None:
            return i + 1

    def push_group(cls):
        group = cls([[]])
        stack[-1].append(group)
        stack.append(group)
        stack.append(group[0])

    def pop_group(cls):
        stack.pop()
        group = stack.pop()
        assert isinstance(group, cls)

    for i, c in enumerate(cmdspec):
        if c == '(':
            push_group(ParenGroup)
            last = i + 1
        elif c == ')':
            last = consume(i)
            pop_group(ParenGroup)
        elif c == '{':
            push_group(BraceGroup)
            last = i + 1
        elif c == '}':
            last = consume(i)
            pop_group(BraceGroup)
        elif c == ' ' and cmdspec[i - 1] != ' ':
            last = consume(i)
        elif c == '|':
            last = consume(i)
            stack.pop()
            new = []
            stack[-1].append(new)
            stack.append(new)
    consume(None)

    if stack.pop() is not elements:
        raise ValueError('%r is unbalanced' % cmdspec)

    return elements


def make_root():
    return CliNode(CliElement('_root'))
