#!/usr/bin/env python3
"""
command_manager.py — Реализация паттерна Command и стека Undo/Redo для операций разметки.
"""

import sys
from pathlib import Path

# Импорт функций работы с маркерами
sys.path.insert(0, str(Path(__file__).parent.parent))
import beat_marker as bm


class Command:
    """Базовый класс для команд с поддержкой отмены (Undo)."""
    def __init__(self, description="Операция"):
        self.description = description

    def execute(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError


class PlaceMarkersCommand(Command):
    """Команда расстановки маркеров на таймлайн или клип в DaVinci Resolve."""
    def __init__(self, proj, timeline_name, track_index, strong_beats, color="Red", target="clip", log_fn=print, progress_fn=None):
        super().__init__(f"Разметка маркеров ({len(strong_beats)} шт, {color})")
        self.proj = proj
        self.timeline_name = timeline_name
        self.track_index = track_index
        self.strong_beats = strong_beats
        self.color = color
        self.target = target
        self.log_fn = log_fn
        self.progress_fn = progress_fn
        self.placed_count = 0

    def execute(self):
        res = bm.place_markers_for_result(
            proj=self.proj,
            timeline_name=self.timeline_name,
            track_index=self.track_index,
            strong_beats=self.strong_beats,
            color=self.color,
            target=self.target,
            log_fn=self.log_fn,
            progress_fn=self.progress_fn,
        )
        self.placed_count = res.get("markers_placed", 0)
        return res

    def undo(self):
        self.log_fn(f"[Undo] Отмена разметки: удаление маркеров цвета '{self.color}'...")
        tl = bm.set_current_timeline(self.proj, self.timeline_name) if self.timeline_name else self.proj.GetCurrentTimeline()
        if not tl:
            return 0
        items = tl.GetItemListInTrack("audio", self.track_index) or []
        clip_items = items if (items and self.target == "clip") else None
        deleted = bm.delete_markers(tl, color=self.color, timeline_items=clip_items)
        self.log_fn(f"[Undo] Удалено {deleted} маркеров.")
        return deleted


class ClearMarkersCommand(Command):
    """Команда очистки маркеров."""
    def __init__(self, proj, timeline_name, track_index, color="All", target="clip", log_fn=print):
        super().__init__(f"Очистка маркеров ({target})")
        self.proj = proj
        self.timeline_name = timeline_name
        self.track_index = track_index
        self.color = color
        self.target = target
        self.log_fn = log_fn
        self.deleted_count = 0
        self.saved_markers_cache = []

    def execute(self):
        tl = bm.set_current_timeline(self.proj, self.timeline_name) if self.timeline_name else self.proj.GetCurrentTimeline()
        if not tl:
            return 0
        items = tl.GetItemListInTrack("audio", self.track_index) or []
        clip_items = items if (items and self.target == "clip") else None
        
        self.deleted_count = bm.delete_markers(tl, color=self.color, timeline_items=clip_items)
        
        # Информативный лог
        target_desc = f"клипах трека A{self.track_index}" if self.target == "clip" else "шкале таймлайна"
        color_desc = "все цвета" if self.color.lower() == "all" else f"цвет '{self.color}'"
        self.log_fn(f"[Очистка] Удалено {self.deleted_count} маркеров на {target_desc} ({color_desc}).")
        
        # Проверяем, остались ли другие маркеры
        remaining_tl = tl.GetMarkers() or {}
        if remaining_tl and self.target == "clip":
            rem_colors = {}
            for m in remaining_tl.values():
                c = m.get("color", "Unknown")
                rem_colors[c] = rem_colors.get(c, 0) + 1
            rem_str = ", ".join(f"{c}: {cnt}" for c, cnt in rem_colors.items())
            self.log_fn(f"[Инфо] На шкале таймлайна находится маркеров: {len(remaining_tl)} ({rem_str})")
            
        return self.deleted_count

    def undo(self):
        self.log_fn("[Undo] Восстановление очищенных маркеров пока не поддерживается.")
        return 0


class MoveTimelineMarkerCommand(Command):
    """Команда перемещения маркера на таймлайне."""
    def __init__(self, timeline, marker_id, old_time, new_time, log_fn=None):
        super().__init__(f"Перемещение маркера #{marker_id} ({old_time:.2f}с -> {new_time:.2f}с)")
        self.timeline = timeline
        self.marker_id = marker_id
        self.old_time = old_time
        self.new_time = new_time
        self.log_fn = log_fn

    def execute(self):
        self.timeline._apply_marker_move(self.marker_id, self.new_time)
        if self.log_fn:
            self.log_fn(f"[Таймлайн] Перемещен маркер #{self.marker_id}: {self.old_time:.2f}с -> {self.new_time:.2f}с")

    def undo(self):
        self.timeline._apply_marker_move(self.marker_id, self.old_time)
        if self.log_fn:
            self.log_fn(f"[Undo] Возврат маркера #{self.marker_id}: {self.new_time:.2f}с -> {self.old_time:.2f}с")


class AddTimelineMarkerCommand(Command):
    """Команда добавления маркера на таймлайне."""
    def __init__(self, timeline, marker_data, log_fn=None):
        super().__init__(f"Добавление маркера на {marker_data.get('time', 0):.2f}с")
        self.timeline = timeline
        self.marker_data = dict(marker_data)
        self.marker_id = marker_data.get("id")
        self.log_fn = log_fn

    def execute(self):
        self.timeline._apply_marker_add(self.marker_data)
        if self.log_fn:
            self.log_fn(f"[Таймлайн] Добавлен маркер на {self.marker_data.get('time', 0):.2f}с")

    def undo(self):
        self.timeline._apply_marker_delete(self.marker_id)
        if self.log_fn:
            self.log_fn(f"[Undo] Удален добавленный маркер #{self.marker_id}")


class DeleteTimelineMarkerCommand(Command):
    """Команда удаления маркера на таймлайне."""
    def __init__(self, timeline, marker_data, log_fn=None):
        super().__init__(f"Удаление маркера #{marker_data.get('id')} ({marker_data.get('time', 0):.2f}с)")
        self.timeline = timeline
        self.marker_data = dict(marker_data)
        self.marker_id = marker_data.get("id")
        self.log_fn = log_fn

    def execute(self):
        self.timeline._apply_marker_delete(self.marker_id)
        if self.log_fn:
            self.log_fn(f"[Таймлайн] Удален маркер #{self.marker_id}")

    def undo(self):
        self.timeline._apply_marker_add(self.marker_data)
        if self.log_fn:
            self.log_fn(f"[Undo] Восстановлен маркер #{self.marker_id}")


class CommandManager:
    """Менеджер истории команд (Undo/Redo стек)."""
    def __init__(self, max_history=20):
        self.max_history = max_history
        self.undo_stack = []
        self.redo_stack = []
        self.listeners = []

    def add_listener(self, fn):
        """Добавить функцию обратного вызова при изменении доступности Undo/Redo."""
        self.listeners.append(fn)

    def _notify(self):
        for fn in self.listeners:
            try:
                fn(self.can_undo(), self.can_redo())
            except Exception:
                pass

    def can_undo(self):
        return len(self.undo_stack) > 0

    def can_redo(self):
        return len(self.redo_stack) > 0

    def get_undo_description(self):
        return self.undo_stack[-1].description if self.undo_stack else ""

    def execute(self, command):
        """Выполнить команду и сохранить её в стек отмены."""
        result = command.execute()
        self.undo_stack.append(command)
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self._notify()
        return result

    def undo(self):
        """Отменить последнюю команду."""
        if not self.can_undo():
            return None
        cmd = self.undo_stack.pop()
        res = cmd.undo()
        self.redo_stack.append(cmd)
        self._notify()
        return res

    def redo(self):
        """Повторить отмененную команду."""
        if not self.can_redo():
            return None
        cmd = self.redo_stack.pop()
        res = cmd.execute()
        self.undo_stack.append(cmd)
        self._notify()
        return res
