"""Command pattern implementation for Undo/Redo functionality."""

from abc import ABC, abstractmethod
from collections import deque
from typing import Optional, List
from copy import deepcopy

from .person import Person
from .family_tree import FamilyTree


class Command(ABC):
    """Abstract base class for commands."""

    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""
        pass

    @abstractmethod
    def undo(self) -> None:
        """Undo the command."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description of the command."""
        pass


class AddPersonCommand(Command):
    """Command for adding a person to the family tree."""

    def __init__(self, family_tree: FamilyTree, person: Person):
        self.family_tree = family_tree
        self.person = person
        self._executed = False

    def execute(self) -> None:
        """Add person to tree."""
        if not self._executed:
            self.family_tree.add_person(self.person)
            self._executed = True

    def undo(self) -> None:
        """Remove person from tree."""
        if self._executed:
            self.family_tree.remove_person(self.person.id)
            self._executed = False

    def get_description(self) -> str:
        return f"Add person: {self.person.name}"


class DeletePersonCommand(Command):
    """Command for deleting a person from the family tree."""

    def __init__(self, family_tree: FamilyTree, person_id: str):
        self.family_tree = family_tree
        self.person_id = person_id
        self.person_backup: Optional[Person] = None
        self.relationships_backup: List = []

    def execute(self) -> None:
        """Delete person and backup their data."""
        person = self.family_tree.get_person(self.person_id)
        if person:
            # Deep copy for backup
            self.person_backup = deepcopy(person)

            # Backup relationships
            for rel in self.family_tree.get_all_relationships():
                if rel.person1_id == self.person_id or rel.person2_id == self.person_id:
                    self.relationships_backup.append(deepcopy(rel))

            # Delete
            self.family_tree.remove_person(self.person_id)

    def undo(self) -> None:
        """Restore the deleted person and relationships."""
        if self.person_backup:
            self.family_tree.add_person(self.person_backup)

            # Restore relationships
            for rel in self.relationships_backup:
                self.family_tree.add_relationship(rel)

    def get_description(self) -> str:
        name = self.person_backup.name if self.person_backup else "Unknown"
        return f"Delete person: {name}"


class UpdatePersonCommand(Command):
    """Command for updating person data."""

    def __init__(self, family_tree: FamilyTree, person_id: str, new_data: Person):
        self.family_tree = family_tree
        self.person_id = person_id
        self.new_data = new_data
        self.old_data: Optional[Person] = None

    def execute(self) -> None:
        """Update person data."""
        person = self.family_tree.get_person(self.person_id)
        if person:
            # Backup old data
            self.old_data = deepcopy(person)

            # Update with new data
            self.family_tree.update_person(self.new_data)

    def undo(self) -> None:
        """Restore old person data."""
        if self.old_data:
            self.family_tree.update_person(self.old_data)

    def get_description(self) -> str:
        name = self.new_data.name if self.new_data else "Unknown"
        return f"Update person: {name}"


class AddRelationshipCommand(Command):
    """Command for adding a relationship."""

    def __init__(self, family_tree: FamilyTree, parent_id: str, child_id: str):
        self.family_tree = family_tree
        self.parent_id = parent_id
        self.child_id = child_id
        self.relationship = None

    def execute(self) -> None:
        """Add parent-child relationship."""
        self.relationship = self.family_tree.set_parent_child(self.parent_id, self.child_id)

    def undo(self) -> None:
        """Remove the relationship."""
        if self.relationship:
            self.family_tree.remove_relationship(self.relationship.id)

            # Restore person references
            child = self.family_tree.get_person(self.child_id)
            parent = self.family_tree.get_person(self.parent_id)

            if child and parent:
                if parent.gender == "M":
                    child.father_id = None
                else:
                    child.mother_id = None

                if self.child_id in parent.children_ids:
                    parent.children_ids.remove(self.child_id)

    def get_description(self) -> str:
        parent = self.family_tree.get_person(self.parent_id)
        child = self.family_tree.get_person(self.child_id)
        parent_name = parent.name if parent else "Unknown"
        child_name = child.name if child else "Unknown"
        return f"Add relationship: {parent_name} -> {child_name}"


class UndoRedoManager:
    """Manages undo/redo operations."""

    def __init__(self, max_history: int = 50):
        self._undo_stack: deque[Command] = deque(maxlen=max_history)
        self._redo_stack: List[Command] = []

    def execute(self, command: Command) -> None:
        """Execute a command and add to undo stack."""
        command.execute()
        self._undo_stack.append(command)

        # Clear redo stack when new command is executed
        self._redo_stack.clear()

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0

    def undo(self) -> Optional[str]:
        """Undo last command. Returns description of undone command."""
        if self.can_undo():
            command = self._undo_stack.pop()
            command.undo()
            self._redo_stack.append(command)
            return command.get_description()
        return None

    def redo(self) -> Optional[str]:
        """Redo last undone command. Returns description of redone command."""
        if self.can_redo():
            command = self._redo_stack.pop()
            command.execute()
            self._undo_stack.append(command)
            return command.get_description()
        return None

    def get_undo_description(self) -> Optional[str]:
        """Get description of next undo command."""
        if self.can_undo():
            return self._undo_stack[-1].get_description()
        return None

    def get_redo_description(self) -> Optional[str]:
        """Get description of next redo command."""
        if self.can_redo():
            return self._redo_stack[-1].get_description()
        return None

    def clear(self) -> None:
        """Clear all undo/redo history."""
        self._undo_stack.clear()
        self._redo_stack.clear()

    def get_history_size(self) -> int:
        """Get current size of undo history."""
        return len(self._undo_stack)
