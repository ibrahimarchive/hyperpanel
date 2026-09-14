"""
Web terminal service.
Manages PTY shell sessions for the browser-based terminal.
Supports Linux standard library pty, ptyprocess, and local dev fallback.
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Optional

logger = logging.getLogger(__name__)


class TerminalSession:
    """Represents an active terminal PTY session."""

    def __init__(self, session_id: str, user_id: int):
        self.session_id = session_id
        self.user_id = user_id
        self.process = None
        self.fd = None
        self.master_fd = None
        self.is_standard_pty = False
        self.is_subprocess = False

    async def start(self, shell: Optional[str] = None, cols: int = 80, rows: int = 24) -> bool:
        """Start a PTY process."""
        if not shell:
            shell = "/bin/bash" if os.path.exists("/bin/bash") else (os.environ.get("SHELL") or "sh")
            if sys.platform == "win32":
                shell = "powershell.exe"

        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["COLUMNS"] = str(cols)
        env["LINES"] = str(rows)

        # 1. Try ptyprocess if installed
        try:
            from ptyprocess import PtyProcess
            self.process = PtyProcess.spawn([shell], dimensions=(rows, cols), env=env)
            logger.info(f"Terminal {self.session_id} started via ptyprocess (PID: {self.process.pid})")
            return True
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"ptyprocess spawn failed: {e}")

        # 2. Try standard library pty (Linux / macOS standard library)
        if sys.platform != "win32":
            try:
                import pty
                import termios
                import struct
                import fcntl

                master_fd, slave_fd = pty.openpty()
                # Set window size
                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)

                # Spawn subprocess connected to slave_fd
                import subprocess
                self.process = subprocess.Popen(
                    [shell],
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    env=env,
                    preexec_fn=os.setsid,
                    close_fds=True,
                )
                os.close(slave_fd)
                self.master_fd = master_fd
                self.is_standard_pty = True
                # Set master_fd non-blocking
                flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
                fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                logger.info(f"Terminal {self.session_id} started via standard pty (PID: {self.process.pid})")
                return True
            except Exception as e:
                logger.error(f"Standard pty launch failed: {e}")

        # 3. Fallback for Windows local dev testing
        try:
            import subprocess
            import threading
            import queue
            self.process = subprocess.Popen(
                [shell],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                bufsize=0,
            )
            self.is_subprocess = True
            self._output_queue = queue.Queue()

            def _subproc_reader():
                try:
                    while self.process and self.process.poll() is None:
                        chunk = self.process.stdout.read(1024)
                        if chunk:
                            self._output_queue.put(chunk.decode("utf-8", errors="replace"))
                        else:
                            break
                except Exception:
                    pass

            self._reader_thread = threading.Thread(target=_subproc_reader, daemon=True)
            self._reader_thread.start()

            logger.info(f"Terminal {self.session_id} started via standard subprocess fallback (PID: {self.process.pid})")
            return True
        except Exception as e:
            logger.error(f"Failed to start fallback terminal: {e}")
            return False

    def write(self, data: str):
        """Write input to the terminal."""
        if not self.process:
            return

        if hasattr(self.process, "write"):  # PtyProcess
            if self.process.isalive():
                self.process.write(data)
        elif self.is_standard_pty and self.master_fd is not None:
            try:
                os.write(self.master_fd, data.encode("utf-8", errors="ignore"))
            except Exception:
                pass
        elif self.is_subprocess and self.process.stdin:
            try:
                self.process.stdin.write(data.encode("utf-8", errors="ignore"))
                self.process.stdin.flush()
            except Exception:
                pass

    def read(self, size: int = 4096) -> Optional[str]:
        """Read output from the terminal (non-blocking)."""
        if not self.process:
            return None

        if hasattr(self.process, "read"):  # PtyProcess
            if not self.process.isalive():
                return None
            try:
                return self.process.read(size)
            except EOFError:
                return None
            except Exception:
                return None
        elif self.is_standard_pty and self.master_fd is not None:
            try:
                chunk = os.read(self.master_fd, size)
                return chunk.decode("utf-8", errors="replace") if chunk else None
            except (BlockingIOError, InterruptedError):
                return ""
            except (OSError, EOFError):
                return None
        elif self.is_subprocess and hasattr(self, "_output_queue"):
            import queue
            items = []
            while not self._output_queue.empty():
                try:
                    items.append(self._output_queue.get_nowait())
                except queue.Empty:
                    break
            return "".join(items) if items else ""

        return None

    def resize(self, cols: int, rows: int):
        """Resize the terminal window."""
        if hasattr(self.process, "setwinsize"):
            try:
                self.process.setwinsize(rows, cols)
            except Exception:
                pass
        elif self.is_standard_pty and self.master_fd is not None:
            try:
                import termios
                import struct
                import fcntl
                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
            except Exception:
                pass

    def is_alive(self) -> bool:
        """Check if the terminal process is still running."""
        if not self.process:
            return False
        if hasattr(self.process, "isalive"):
            return self.process.isalive()
        return self.process.poll() is None

    def terminate(self):
        """Terminate the terminal session."""
        try:
            if hasattr(self.process, "terminate"):
                if hasattr(self.process, "isalive") and self.process.isalive():
                    self.process.terminate(force=True)
                elif hasattr(self.process, "poll") and self.process.poll() is None:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=1)
                    except Exception:
                        pass
            if self.master_fd is not None:
                os.close(self.master_fd)
                self.master_fd = None
            logger.info(f"Terminal session {self.session_id} terminated")
        except Exception as e:
            logger.error(f"Error terminating terminal: {e}")


class TerminalManager:
    """Manages multiple terminal sessions."""

    def __init__(self):
        self.sessions: dict[str, TerminalSession] = {}
        self._counter = 0

    def create_session(self, user_id: int) -> TerminalSession:
        """Create a new terminal session."""
        self._counter += 1
        session_id = f"term_{user_id}_{self._counter}"
        session = TerminalSession(session_id, user_id)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        """Get an existing session."""
        return self.sessions.get(session_id)

    def remove_session(self, session_id: str):
        """Remove and terminate a session."""
        session = self.sessions.pop(session_id, None)
        if session:
            session.terminate()

    def get_user_sessions(self, user_id: int) -> list[TerminalSession]:
        """Get all sessions for a user."""
        return [s for s in self.sessions.values() if s.user_id == user_id]

    def cleanup_dead_sessions(self):
        """Remove sessions whose processes have died."""
        dead = [sid for sid, s in self.sessions.items() if not s.is_alive()]
        for sid in dead:
            self.sessions.pop(sid, None)


# Singleton
terminal_manager = TerminalManager()
