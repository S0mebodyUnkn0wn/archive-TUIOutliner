from datetime import date

from . import data
from .configs import session_config
from .data import Importance, TaskOrigin


class TaskNode:

    @property
    def icon(self):
        if self.importance == Importance.DONE:
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

    def __init__(self, text: str = None, deadline: date = None, importance: int = data.Importance.TODO_B,
                 origin: TaskOrigin = None):

        self.is_root = True
        self.root_node = self
        self.ident_level = 0

        self.text = text
        self.origin = origin
        self.parent_node = None
        self.child_nodes: list = []
        self.deadline = deadline
        self.importance = importance

    def __str__(self):
        if self.is_root:
            return ""
        return self.text
    
    def is_identical(self, other):
        if isinstance(other, TaskNode):
            return (self == other) and self.child_nodes == other.child_nodes
        
    def __eq__(self, other):
        if isinstance(other, TaskNode):
            return (self.text == other.text) and (self.importance == other.importance)
        elif isinstance(other, str):
            return self.text == other
        elif other is None:
            return False
        else:
            raise TypeError(f"cannot compare {type(other)} with TaskNode")

    def __gt__(self, other):
        if isinstance(other, TaskNode):
            if self.importance > other.importance:
                return True
            elif self.importance < other.importance:
                return False
            elif self.deadline is not None:
                if other.deadline is not None:
                    return self.deadline < other.deadline
                else:
                    return True
            elif other.deadline is not None:
                return False
            elif self.text > other.text:
                return False
            else:
                return True
        if isinstance(other, str):
            if self.text > other:
                return True
            else:
                return False
        else:
            raise TypeError(f"can only compare TaskNode or str with TaskNode not '{type(other)}'")

    def mark_done(self):
        if self.importance != Importance.DONE:
            self.importance = Importance.DONE
        else:
            self.importance = Importance.TODO_B

    def to_cli_format(self):
        return session_config.TaskConfig.tab_string * self.ident_level + self.icon + self.text

    def to_logseq_format(self):
        if self.is_root:
            return
        out = "\n- "
        if self.importance == Importance.DONE:
            out += "DONE "
        elif Importance.TODO_C <= self.importance <= Importance.TODO_A:
            out += "TODO "
        elif Importance.DOING_C <= self.importance <= Importance.DOING_A:
            out += "DOING "
        elif Importance.WAITING_C <= self.importance <= Importance.WAITING_A:
            out += "WAITING "
        match (self.importance % 10):
            case 4:
                out += "[#C] "
            case 5:
                out += "[#B] "
            case 6:
                out += "[#A] "
        out += self.text
        if self.deadline is not None:
            out += "\n DEADLINE: <" + self.deadline.strftime("%Y-%m-%d %a") + ">"
        return out

    def get_tree(self):
        if self.is_root:
            out = ""
        elif self.is_excluded:
            return ""
        else:
            out = session_config.TaskConfig.tab_string * self.ident_level + self.icon + self.text + "\n"
        for child in self.child_nodes:
            out += child.get_tree()
        return out

    def get_all_children(self, with_deadline_only=False):
        if self.is_excluded:
            return []
        include_self = True
        if (with_deadline_only and self.deadline is None) or self.is_root:
            include_self = False
        if len(self.child_nodes) == 0:
            return [self] if include_self else []
        else:
            nodes = [self] if include_self else []
            for child in self.child_nodes:
                nodes.extend(child.get_all_children())
            return nodes

    def get_info(self):
        info = f"Task: {self.text}, duedate: {self.deadline}, has {len(self.child_nodes)} immediate child nodes"
        return info

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

    def to_calcure_csv(self, hide_tasks=()):
        if self.is_root:
            out = ""
        else:
            importance_str = "normal"
            if self.importance == Importance.DONE:
                importance_str = "done"
            elif Importance.DOING_C <= self.importance <= Importance.DOING_A:
                importance_str = "important"
            if self.importance in hide_tasks and (
                    self.parent_node.is_root or self.parent_node.importance in hide_tasks):
                out = ""
            else:
                if self.deadline is None:
                    year = 0
                    month = 0
                    day = 0
                else:
                    year = self.deadline.year
                    month = self.deadline.month
                    day = self.deadline.day
                out = f"{year},{month},{day},\"{self.ident_level * '--' + self.text if len(self.text) < 99 else self.text[:96] + '...'}\",{importance_str}\n"
        for i in range(len(self.child_nodes)):
            out += self.child_nodes[i].to_calcure_csv(hide_tasks=hide_tasks)
        if self.is_root:
            out = out.strip()
        return out
