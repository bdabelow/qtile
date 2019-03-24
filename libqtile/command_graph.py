# Copyright (c) 2008, Aldo Cortesi. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import abc
from typing import Dict, List, Optional, Tuple, Type  # noqa: F401

SelectorType = Tuple[str, Optional[str]]


def _format_selectors(selectors: List[SelectorType]) -> str:
    """Build the path to the selected command graph node"""
    path_elements = []
    for name, selector in selectors:
        if selector is not None:
            path_elements.append("{}[{}]".format(name, selector))
        else:
            path_elements.append(name)
    return ".".join(path_elements)


class _CommandGraphNode(metaclass=abc.ABCMeta):
    """An abstract node in the command graph"""

    @property
    @abc.abstractmethod
    def path(self) -> str:
        """The path to the current command graph node"""
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def selectors(self) -> List[SelectorType]:
        """The selectors resolving the location of the node in the command graph"""
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def parent(self) -> Optional["CommandGraphContainer"]:
        """The parent of the current node"""
        pass  # pragma: no cover


class CommandGraphContainer(_CommandGraphNode, metaclass=abc.ABCMeta):
    """A container node in the command graph structure

    A command graph node which can contain other elements that it can link to.
    May also have commands that can be executed on itself.
    """

    @property
    def path(self) -> str:
        """The path to the current command graph node"""
        return _format_selectors(self.selectors)

    @property
    @abc.abstractmethod
    def selector(self) -> Optional[str]:
        """The selector for the current node"""
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def children(self) -> List[str]:
        """The child objects that are contained within this object"""
        pass  # pragma: no cover

    def navigate(self, name: str, selector: Optional[str]) -> "_CommandGraphNode":
        """Navigate from the current node to the specified child"""
        if name in self.children:
            return _CommandGraphMap[name](selector, self)
        elif selector is not None:
            raise KeyError("Given node is not an object: {}".format(name))
        else:
            return CommandGraphCall(name, self)


class CommandGraphRoot(CommandGraphContainer):
    """The root node of the command graph

    Contains all of the elements connected to the root of the command graph.
    """

    @property
    def selector(self) -> None:
        """The selector for the current node"""
        return None

    @property
    def selectors(self) -> List[SelectorType]:
        """The selectors resolving the location of the node in the command graph"""
        return []

    @property
    def parent(self) -> None:
        """The parent of the current node"""
        return None

    @property
    def children(self) -> List[str]:
        """All of the child elements in the root of the command graph"""
        return ["bar", "group", "layout", "screen", "widget", "window"]


class CommandGraphCall(_CommandGraphNode):
    def __init__(self, name: str, parent: CommandGraphContainer):
        """A command to be executed on the selected object

        A terminal node in the command graph, specifying an actual command to
        execute on the selected graph element.

        Parameters
        ----------
        name:
            The name of the command to execute
        parent:
            The command graph node on which to execute the given command.
        """
        self._name = name
        self._parent = parent

    @property
    def name(self) -> str:
        """The name of the call to make"""
        return self._name

    @property
    def selectors(self) -> List[SelectorType]:
        """The selectors resolving the location of the node in the command graph"""
        return self.parent.selectors

    @property
    def parent(self) -> CommandGraphContainer:
        """The parent of the current node"""
        return self._parent

    @property
    def path(self) -> str:
        """The path to the current command graph node"""
        parent_path = self.parent.path
        if parent_path:
            return "{}.{}".format(parent_path, self._name)
        else:
            return self._name


class CommandGraphObject(CommandGraphContainer, metaclass=abc.ABCMeta):
    def __init__(self, selector: Optional[str], parent: CommandGraphContainer):
        """A container object in the command graph

        Parameters
        ----------
        selector: Optional[str]
            The name of the selected element within the command graph.  If not
            given, corresponds to the default selection of this type of object.
        parent: CommandGraphContainer
            The container object that this object is the child of.
        """
        self._selector = selector
        self._parent = parent

    @property
    def selector(self) -> Optional[str]:
        """The selector for the current node"""
        return self._selector

    @property
    def selectors(self) -> List[SelectorType]:
        """The selectors resolving the location of the node in the command graph"""
        selectors = self.parent.selectors + [(self.object_type, self.selector)]
        return selectors

    @property
    def parent(self) -> CommandGraphContainer:
        """The parent of the current node"""
        return self._parent

    @property
    @abc.abstractmethod
    def object_type(self) -> str:
        """The type of the current container object"""
        pass  # pragma: no cover


class _BarGraphNode(CommandGraphObject):
    object_type = "bar"
    children = ["screen"]


class _GroupGraphNode(CommandGraphObject):
    object_type = "group"
    children = ["layout", "window", "screen"]


class _LayoutGraphNode(CommandGraphObject):
    object_type = "layout"
    children = ["group", "window", "screen"]


class _ScreenGraphNode(CommandGraphObject):
    object_type = "screen"
    children = ["layout", "window", "bar"]


class _WidgetGraphNode(CommandGraphObject):
    object_type = "widget"
    children = ["bar", "screen", "group"]


class _WindowGraphNode(CommandGraphObject):
    object_type = "window"
    children = ["group", "screen", "layout"]


_CommandGraphMap = {
    "bar": _BarGraphNode,
    "group": _GroupGraphNode,
    "layout": _LayoutGraphNode,
    "widget": _WidgetGraphNode,
    "window": _WindowGraphNode,
    "screen": _ScreenGraphNode,
}  # type: Dict[str, Type[CommandGraphObject]]