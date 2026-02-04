from typing import List, Optional, Callable
from models.graph import GraphState


class UndoRedoManager:
    """
    Manages undo/redo operations for graph editing.
    """
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self._undo_stack: List[GraphState] = []
        self._redo_stack: List[GraphState] = []
        self._on_change_callbacks: List[Callable[[], None]] = []
        
    def save_state(self, state: GraphState):
        """
        Save current state for potential undo.
        Clears redo stack (new action invalidates redo history).
        """
        # Add copy to undo stack
        self._undo_stack.append(state.copy())
        
        # Limit stack size
        if len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)
            
        # Clear redo stack
        self._redo_stack.clear()
        
        self._notify_change()
        
    def undo(self, current_state: GraphState) -> Optional[GraphState]:
        """
        Undo the last action.
        """
        if not self.can_undo():
            return None
            
        # Save current state to redo
        self._redo_stack.append(current_state.copy())
        
        # Pop and return previous state
        state = self._undo_stack.pop()
        self._notify_change()
        return state
        
    def redo(self, current_state: GraphState) -> Optional[GraphState]:
        """
        Redo a previously undone action.
        """
        if not self.can_redo():
            return None
            
        # Save current state to undo
        self._undo_stack.append(current_state.copy())
        
        # Pop and return redo state
        state = self._redo_stack.pop()
        self._notify_change()
        return state
        
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0
        
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0
        
    def clear(self):
        """Clear all history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._notify_change()
        
    def add_change_callback(self, callback: Callable[[], None]):
        """Add a callback to be called when undo/redo availability changes."""
        self._on_change_callbacks.append(callback)
        
    def remove_change_callback(self, callback: Callable[[], None]):
        """Remove a previously added callback."""
        if callback in self._on_change_callbacks:
            self._on_change_callbacks.remove(callback)
            
    def _notify_change(self):
        """Notify all callbacks of state change."""
        for callback in self._on_change_callbacks:
            try:
                callback()
            except Exception:
                pass  
                
    @property
    def undo_count(self) -> int:
        """Number of available undo steps."""
        return len(self._undo_stack)
        
    @property
    def redo_count(self) -> int:
        """Number of available redo steps."""
        return len(self._redo_stack)
