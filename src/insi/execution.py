"""Kontrollierte Schülerprozesse mit Stoppen und sauberem Aufräumen."""

import subprocess
import threading
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .interpreter import python_command
from .execution_security import (
    DEFAULT_MAX_OUTPUT_CHARS,
    DEFAULT_TIMEOUT_SECONDS,
    course_code_policy,
    execution_environment,
    limited_output,
    popen_isolation_options,
    student_policy,
    terminate_process,
)


@dataclass(frozen=True)
class ExecutionResult:
    returncode: int
    stdout: str
    stderr: str
    stopped: bool = False
    timed_out: bool = False
    output_truncated: bool = False


class ExecutionManager:
    def __init__(self) -> None:
        self._processes: dict[Path, subprocess.Popen[str]] = {}
        self._stopped: set[Path] = set()
        self._lock = threading.Lock()

    @staticmethod
    def _target(path: str | Path, course: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        root = Path(course).expanduser().resolve()
        if not target.is_relative_to(root):
            raise ValueError("Es dürfen nur Dateien aus dem Kursordner gestartet werden.")
        if not target.is_file() or target.suffix.lower() != ".py":
            raise ValueError("Die Aufgabe muss eine vorhandene Python-Datei sein.")
        return target

    def is_running(self, path: str | Path) -> bool:
        target = Path(path).expanduser().resolve()
        with self._lock:
            process = self._processes.get(target)
            return process is not None and process.poll() is None

    def execute(
        self,
        path: str | Path,
        course: str | Path,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
        headless: bool = False,
    ) -> ExecutionResult:
        target = self._target(path, course)
        root = Path(course).expanduser().resolve()
        policy = student_policy(
            root,
            timeout_seconds=timeout_seconds,
            max_output_chars=max_output_chars,
        )
        environment = execution_environment(
            policy,
            pythonpath=(root,),
            overrides={"PYKIM_HEADLESS": "1"} if headless else None,
        )
        with self._lock:
            previous = self._processes.get(target)
            if previous is not None and previous.poll() is None:
                raise RuntimeError("Diese Aufgabe läuft bereits.")
            process = subprocess.Popen(
                [*python_command(), str(target)],
                cwd=target.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
                **popen_isolation_options(),
            )
            self._processes[target] = process
            self._stopped.discard(target)
        try:
            timed_out = False
            try:
                stdout, stderr = process.communicate(timeout=policy.timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                terminate_process(process)
                try:
                    stdout, stderr = process.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    terminate_process(process, force=True)
                    stdout, stderr = process.communicate()
                timeout_message = (
                    f"Das Programm wurde nach {policy.timeout_seconds:g} Sekunden "
                    "automatisch beendet."
                )
                stderr = f"{stderr}\n{timeout_message}".strip()
            stdout, stdout_truncated = limited_output(
                stdout, policy.max_output_chars
            )
            stderr, stderr_truncated = limited_output(
                stderr, policy.max_output_chars
            )
            with self._lock:
                stopped = target in self._stopped
            return ExecutionResult(
                process.returncode,
                stdout,
                stderr,
                stopped,
                timed_out,
                stdout_truncated or stderr_truncated,
            )
        finally:
            with self._lock:
                self._processes.pop(target, None)
                self._stopped.discard(target)

    def launch_preview(self, path: str | Path, course: str | Path) -> None:
        """Starte ein Pyxel-Fenster, ohne die Suite auf dessen Ende warten zu lassen."""
        target = self._target(path, course)
        root = Path(course).expanduser().resolve()
        policy = student_policy(root)
        environment = execution_environment(policy, pythonpath=(root,))
        with self._lock:
            previous = self._processes.get(target)
            if previous is not None and previous.poll() is None:
                raise RuntimeError("Die Vorschau dieser Aufgabe läuft bereits.")
            process = subprocess.Popen(
                [*python_command(), str(target)],
                cwd=target.parent,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=environment,
                **popen_isolation_options(),
            )
            self._processes[target] = process
            self._stopped.discard(target)

        def reap() -> None:
            try:
                process.wait(timeout=policy.timeout_seconds)
            except subprocess.TimeoutExpired:
                terminate_process(process)
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    terminate_process(process, force=True)
                    process.wait()
            finally:
                with self._lock:
                    if self._processes.get(target) is process:
                        self._processes.pop(target, None)
                    self._stopped.discard(target)

        threading.Thread(target=reap, daemon=True).start()

    def stop(self, path: str | Path) -> bool:
        target = Path(path).expanduser().resolve()
        with self._lock:
            process = self._processes.get(target)
            if process is None or process.poll() is not None:
                return False
            self._stopped.add(target)
            terminate_process(process)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            terminate_process(process, force=True)
        return True

    def stop_all(self) -> None:
        with self._lock:
            targets = list(self._processes)
        for target in targets:
            self.stop(target)


execution_manager = ExecutionManager()


@dataclass
class ScriptExampleJob:
    process: subprocess.Popen[str]
    path: Path
    stdout: str = ""
    stderr: str = ""
    finished: bool = False
    timed_out: bool = False
    output_truncated: bool = False
    finished_event: threading.Event = field(default_factory=threading.Event)


class ScriptExampleManager:
    """Starte Skriptbeispiele und sammle ihre Ausgabe bereits während des Laufs."""

    def __init__(self) -> None:
        self._jobs: dict[str, ScriptExampleJob] = {}
        self._lock = threading.Lock()

    def start(
        self,
        source: str,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
    ) -> str:
        descriptor, filename = tempfile.mkstemp(prefix="pykim-script-", suffix=".py")
        path = Path(filename)
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            target.write(source.rstrip() + "\n")
        policy = course_code_policy(
            path.parent,
            timeout_seconds=timeout_seconds,
            max_output_chars=max_output_chars,
        )
        environment = execution_environment(
            policy,
            overrides={"PYKIM_PROGRESS_MODE": "disabled"},
        )
        try:
            process = subprocess.Popen(
                [*python_command(), "-u", str(path)],
                cwd=path.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=environment,
                **popen_isolation_options(),
            )
        except Exception:
            path.unlink(missing_ok=True)
            raise
        job_id = uuid.uuid4().hex
        job = ScriptExampleJob(process, path)
        with self._lock:
            self._jobs[job_id] = job

        def read_stream(stream, attribute: str) -> None:
            if stream is None:
                return
            for chunk in iter(stream.readline, ""):
                with self._lock:
                    current = getattr(job, attribute)
                    remaining = policy.max_output_chars - len(current)
                    if remaining > 0:
                        setattr(job, attribute, current + chunk[:remaining])
                    if len(chunk) > remaining:
                        job.output_truncated = True
            stream.close()

        stdout_reader = threading.Thread(
            target=read_stream, args=(process.stdout, "stdout"), daemon=True
        )
        stderr_reader = threading.Thread(
            target=read_stream, args=(process.stderr, "stderr"), daemon=True
        )

        def finish() -> None:
            try:
                process.wait(timeout=policy.timeout_seconds)
            except subprocess.TimeoutExpired:
                job.timed_out = True
                terminate_process(process)
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    terminate_process(process, force=True)
                    process.wait()
            stdout_reader.join()
            stderr_reader.join()
            path.unlink(missing_ok=True)
            with self._lock:
                if job.output_truncated:
                    marker = "\n… Ausgabe wurde aus Sicherheitsgründen gekürzt.\n"
                    job.stderr = (job.stderr + marker)[-policy.max_output_chars:]
                if job.timed_out:
                    message = (
                        f"\nDas Beispiel wurde nach {policy.timeout_seconds:g} "
                        "Sekunden automatisch beendet.\n"
                    )
                    job.stderr = (job.stderr + message)[-policy.max_output_chars:]
                job.finished = True
                job.finished_event.set()

        stdout_reader.start()
        stderr_reader.start()
        threading.Thread(target=finish, daemon=True).start()
        return job_id

    def status(self, job_id: str) -> dict[str, object] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            returncode = job.process.poll()
            return {
                "running": not job.finished,
                "returncode": returncode if job.finished else None,
                "stdout": job.stdout,
                "stderr": job.stderr,
                "timed_out": job.timed_out,
                "output_truncated": job.output_truncated,
            }

    def stop(self, job_id: str) -> bool:
        """Beende genau einen laufenden Skript- oder Galerieprozess."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.process.poll() is not None:
                return False
            terminate_process(job.process)
        try:
            job.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            terminate_process(job.process, force=True)
        job.finished_event.wait(timeout=3)
        return True

    def stop_all(self) -> None:
        with self._lock:
            jobs = tuple(self._jobs.values())
        for job_id in tuple(self._jobs):
            self.stop(job_id)


script_example_manager = ScriptExampleManager()
