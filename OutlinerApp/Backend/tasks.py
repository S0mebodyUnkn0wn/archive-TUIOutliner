from datetime import date

from . import data
from .configs import session_config
from .data import Importance


class TaskNode:

    @property
    def icon(self):
        if self.is_done:
            icon = session_config.Icons.done_icon
        elif self.importance == Importance.DOING_C:
            icon = session_config.Icons.doing_C_icon
        elif self.importance == Importance.DOING_B:
            icon = session_config.Icons.doing_icon
        elif self.importance == Importance.DOING_A:
            icon = session_config.Icons.doing_A_icon
        elif self.importance == Importance.TODO_C:
            icon = session_config.Icons.generic_task_C_icon
        elif self.importance == Importance.TODO_A:
            icon = session_config.Icons.generic_task_A_icon
        else:
            icon = session_config.Icons.generic_task_icon

        return icon

    @property
    def total_children(self):
        if self.is_excluded:
            return 0
        if len(self.child_nodes) == 0:
            print(self)
            return 1
        else:
            child_count = 0
            for child in self.child_nodes:
                child_count += child.total_children
            return child_count + (0 if self.is_root else 1)

    @property
    def is_excluded(self):
        return self.importance in session_config.TaskConfig.exclude_tasks and (
                self.deadline is None or self.deadline < date.today())

    @property
    def priority(self):
        priority = self.importance
        if self.is_done:
            priority=1
        if self.deadline is not None:
            if self.deadline>date.today():
                if priority<0:
                    priority = Importance.DEFAULT
            if priority>0:
                priority *= 1000
                priority -= (self.deadline - date.today()).days

        return priority

    @property
    def importance(self):
        if self.is_done:
            return Importance.DONE
        return self._importance

    @property
    def is_done(self):
        return self._is_done

    def __init__(self, text: str = None, deadline: date = None, importance: int = data.Importance.TODO_B):

        self.is_root = True
        self.root_node = self
        self.ident_level = 0

        self.text: str = text
        self.parent_node: TaskNode | None = None
        self.child_nodes: list = []
        self.deadline: date = deadline
        self._importance: int = importance
        self._is_done: bool = False

    def __str__(self):
        if self.is_root:
            return ""
        return session_config.TaskConfig.tab_string * self.ident_level + self.icon + self.text

    def sort_children(self):
        self.child_nodes.sort(reverse=True)

    def is_identical(self, other):
        if isinstance(other, TaskNode):
            return (self == other) and self.child_nodes == other.child_nodes

    def __eq__(self, other):
        if isinstance(other, TaskNode):
            return (self.text == other.text) and (self.priority == other.priority)
        elif isinstance(other, str):
            return self.text == other
        elif other is None:
            return False
        else:
            raise TypeError(f"cannot compare {type(other)} with TaskNode")

    def compare_deadlines(self, other: "TaskNode"):
        if self.deadline is not None:
            if other.deadline is not None:
                if self.deadline < other.deadline:
                    return 1
                if self.deadline == other.deadline:
                    return 0
                if self.deadline > other.deadline:
                    return -1
            else:
                return 1
        if self.deadline is None and other.deadline is not None:
            return -1
        return 0

    def __gt__(self, other):
        if isinstance(other, TaskNode):
            if self.priority == other.priority:
                return self.text <= other.text
            return self.priority > other.priority

        if isinstance(other, str):
            if self.text > other:
                return True
            else:
                return False
        else:
            raise TypeError(f"can only compare TaskNode or str with TaskNode not '{type(other)}'")

    def set_done(self, is_done: bool = True, affect_children: bool = True):
        if affect_children:
            for child in self.child_nodes:
                child.set_done(is_done)
        self._is_done = is_done
        self.parent_node.sort_children()

    def toggle_done(self, affect_children: bool= True):
        is_done = not self.is_done
        self.set_done(is_done,affect_children)


    def get_tree(self):
        if self.is_root:
            out = ""
        elif self.is_excluded:
            return ""
        else:
            out = f"{session_config.TaskConfig.tab_string * self.ident_level} {self.icon} {self.text}\n"
        for child in self.child_nodes:
            out += child.get_tree()
        return out

    def get_all_children(self, with_deadline_only=False):
        include_self = True
        if (with_deadline_only and self.deadline is None) or self.is_root or self.is_excluded:
            include_self = False

        nodes = [self] if include_self else []

        if len(self.child_nodes) > 0:
            for child in self.child_nodes:
                nodes.extend(child.get_all_children())

        return nodes

    def add_subtask(self, subtask):
        already_in = self.find_subtask(subtask)
        if not already_in:

            subtask.is_root = False
            subtask.parent_node = self
            subtask.root_node = self.root_node
            subtask.ident_level = subtask.get_level() - 1

            for i in range(len(self.child_nodes)):
                if subtask > self.child_nodes[i]:
                    self.child_nodes.insert(i, subtask)
                    break
            else:
                self.child_nodes.append(subtask)
            return True
        return False

    def get_level(self):
        level = 0
        p = self.parent_node
        while p is not None:
            p = p.parent_node
            level += 1
        return level

    def remove(self):
        self.parent_node.child_nodes.remove(self)

    def find_subtask(self, task):
        if self.is_root:
            pass
        elif isinstance(task, str):
            if self.text.strip("-") == task.strip("-"):
                return self
        elif isinstance(task, TaskNode):
            if self == task:
                return self
        if len(self.child_nodes) == 0:
            return False
        for child in self.child_nodes:
            result = child.find_subtask(task)
            if result:
                return result
        else:
            return False
