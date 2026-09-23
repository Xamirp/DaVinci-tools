"""
Аудиоплеер для таймлайна на базе sounddevice.
Потоковое воспроизведение NumPy-массива звука с поддержкой паузы, перемотки
и отслеживания текущего времени воспроизведения.
"""

import threading
import numpy as np

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except Exception:
    HAS_SOUNDDEVICE = False


class AudioPlayer:
    """Потоковый аудиоплеер для работы с аудиоданными в памяти."""

    def __init__(self, on_time_update=None, on_playback_end=None):
        self.on_time_update = on_time_update
        self.on_playback_end = on_playback_end

        self.audio_data = None
        self.sr = 22050
        self.total_frames = 0
        self.duration_sec = 0.0

        self.current_frame = 0
        self.is_playing = False
        self.stream = None
        self._lock = threading.Lock()

    def load(self, y: np.ndarray, sr: int):
        """Загрузить аудиоданные (моно или стерео)."""
        self.stop()
        with self._lock:
            # Преобразуем к float32 моно
            if y.ndim > 1:
                y = np.mean(y, axis=1)
            self.audio_data = np.ascontiguousarray(y, dtype=np.float32)
            self.sr = int(sr)
            self.total_frames = len(self.audio_data)
            self.duration_sec = self.total_frames / float(self.sr) if self.sr > 0 else 0.0
            self.current_frame = 0

    def _audio_callback(self, outdata, frames, time_info, status):
        with self._lock:
            if not self.is_playing or self.audio_data is None:
                outdata.fill(0)
                return

            end_frame = self.current_frame + frames
            if self.current_frame >= self.total_frames:
                outdata.fill(0)
                self.is_playing = False
                if self.on_playback_end:
                    threading.Thread(target=self.on_playback_end, daemon=True).start()
                return

            if end_frame > self.total_frames:
                available = self.total_frames - self.current_frame
                chunk = self.audio_data[self.current_frame:self.total_frames]
                outdata[:available, 0] = chunk
                outdata[available:, 0] = 0
                self.current_frame = self.total_frames
                self.is_playing = False
                if self.on_playback_end:
                    threading.Thread(target=self.on_playback_end, daemon=True).start()
            else:
                outdata[:, 0] = self.audio_data[self.current_frame:end_frame]
                self.current_frame = end_frame

    def _ensure_stream(self):
        if not HAS_SOUNDDEVICE or self.audio_data is None:
            return False
        if self.stream is None or not self.stream.active:
            try:
                self.stream = sd.OutputStream(
                    samplerate=self.sr,
                    channels=1,
                    dtype="float32",
                    blocksize=2048,
                    callback=self._audio_callback
                )
                self.stream.start()
                return True
            except Exception as e:
                print(f"[AudioPlayer] Ошибка создания потока воспроизведения: {e}")
                return False
        return True

    def play(self, start_time: float = None):
        """Начать воспроизведение."""
        if not HAS_SOUNDDEVICE or self.audio_data is None:
            return False

        with self._lock:
            if start_time is not None:
                self.current_frame = int(np.clip(start_time * self.sr, 0, self.total_frames))
            elif self.current_frame >= self.total_frames:
                self.current_frame = 0

            self.is_playing = True

        return self._ensure_stream()

    def pause(self):
        """Приостановить воспроизведение."""
        with self._lock:
            self.is_playing = False

    def toggle_play(self):
        """Переключить воспроизведение/паузу."""
        if self.is_playing:
            self.pause()
            return False
        else:
            self.play()
            return True

    def seek(self, time_sec: float):
        """Перемотать в позицию time_sec."""
        with self._lock:
            if self.audio_data is not None and self.sr > 0:
                self.current_frame = int(np.clip(time_sec * self.sr, 0, self.total_frames))

    def get_time(self) -> float:
        """Получить текущую позицию воспроизведения в секундах."""
        with self._lock:
            if self.sr > 0:
                return float(self.current_frame) / float(self.sr)
            return 0.0

    def stop(self):
        """Остановить воспроизведение и закрыть аудиопоток."""
        with self._lock:
            self.is_playing = False
            self.current_frame = 0
            if self.stream is not None:
                try:
                    self.stream.stop()
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None
