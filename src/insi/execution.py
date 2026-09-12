"""Kontrollierte Schülerprozesse mit Stoppen und sauberem Aufräumen."""

import subprocess
import threading
import os
import tempfile
import uuid
import shutil
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from .interpreter import python_command
from .execution_security import (
    DEFAULT_MAX_OUTPUT_CHARS,
    DEFAULT_TIMEOUT_SECONDS,
    ExecutionPolicy,
    builtin_policy,
    course_code_policy,
    execution_environment,
    limited_output,
    student_policy,
    terminate_process,
)
from .progress import merge_sandbox_progress, prepare_sandbox_progress
from .sandbox import SandboxedProcess, sandbox_popen
from .workspace_files import sandbox_readable_roots


@dataclass(frozen=True)
class ExecutionResult:
    returncode: int
    stdout: str
    stderr: str
    stopped: bool = False
    timed_out: bool = False
    output_truncated: bool = False
    limit_reason: str | None = None


def wait_for_process(process: SandboxedProcess, timeout: float) -> bool:
    """Warte begrenzt und beende bei Zeitüberschreitung den gesamten Prozessbaum."""
    try:
        process.wait(timeout=timeout)
        return False
    except subprocess.TimeoutExpired:
        terminate_process(process)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            terminate_process(process, force=True)
            process.wait()
        return True


def prepare_student_run(
    target: Path, course: Path, *,
    allow_gui: bool = False,
    headless: bool = False,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
    prefix: str = "insi-task-",
) -> tuple[ExecutionPolicy, dict[str, str], int]:
    """Bereite einen privaten Laufbereich samt Sandbox und Lernstand vor."""
    root = course.expanduser().resolve()
    run_root = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        progress_path = run_root / "progress.json"
        progress_baseline = prepare_sandbox_progress(progress_path, root)
        policy = student_policy(
            run_root,
            readable_roots=sandbox_readable_roots(root, target),
            writable_roots=(run_root,),
            timeout_seconds=timeout_seconds,
            max_output_chars=max_output_chars,
            allow_gui=allow_gui,
        )
        overrides = {
            "INSI_PROGRESS_FILE": str(progress_path),
            "INSI_RUN_FILES": str(run_root),
        }
        if headless:
            overrides["PYKIM_HEADLESS"] = "1"
        environment = execution_environment(
            policy,
            pythonpath=(root,),
            overrides=overrides,
        )
        return policy, environment, progress_baseline
    except BaseException:
        shutil.rmtree(run_root, ignore_errors=True)
        raise


def finish_student_run(policy: ExecutionPolicy, course: Path, baseline: int) -> None:
    """Übernimm neue Versuche und räume auch bei Speicherfehlern auf."""
    try:
        merge_sandbox_progress(
            policy.workspace / "progress.json", course, baseline_attempts=baseline,
        )
    finally:
        shutil.rmtree(policy.workspace, ignore_errors=True)


class ExecutionManager:
    def __init__(self) -> None:
        self._processes: dict[Path, SandboxedProcess] = {}
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

    def _start(
        self, target: Path, root: Path, *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
        headless: bool = False,
        preview: bool = False,
    ) -> tuple[SandboxedProcess, ExecutionPolicy, int]:
        message = (
            "Die Vorschau dieser Aufgabe läuft bereits."
            if preview else "Diese Aufgabe läuft bereits."
        )
        if self.is_running(target):
            raise RuntimeError(message)
        policy, environment, baseline = prepare_student_run(
            target, root, allow_gui=not headless, headless=headless,
            timeout_seconds=timeout_seconds, max_output_chars=max_output_chars,
            prefix="insi-preview-" if preview else "insi-task-",
        )
        try:
            with self._lock:
                previous = self._processes.get(target)
                if previous is not None and previous.poll() is None:
                    raise RuntimeError(message)
                process = sandbox_popen(
                    [*python_command(), str(target)],
                    policy=policy,
                    cwd=policy.workspace,
                    stdout=subprocess.DEVNULL if preview else subprocess.PIPE,
                    stderr=subprocess.DEVNULL if preview else subprocess.PIPE,
                    text=True,
                    env=environment,
                )
                self._processes[target] = process
                self._stopped.discard(target)
        except Exception:
            shutil.rmtree(policy.workspace, ignore_errors=True)
            raise
        return process, policy, baseline

    def _finish(
        self, target: Path, root: Path, process: SandboxedProcess,
        policy: ExecutionPolicy, baseline: int,
    ) -> None:
        try:
            finish_student_run(policy, root, baseline)
        finally:
            with self._lock:
                if self._processes.get(target) is process:
                    self._processes.pop(target)
                    self._stopped.discard(target)

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
        process, policy, baseline = self._start(
            target, root, timeout_seconds=timeout_seconds,
            max_output_chars=max_output_chars, headless=headless,
        )
        try:
            stdout, stderr, timed_out, capture_truncated = (
                process.communicate_bounded(timeout=policy.timeout_seconds)
            )
            if timed_out:
                timeout_message = (
                    f"Das Programm wurde nach {policy.timeout_seconds:g} Sekunden "
                    "automatisch beendet."
                )
                stderr = f"{stderr}\n{timeout_message}".strip()
            if capture_truncated and len(stdout) >= policy.max_output_chars:
                stdout += "\n"
            if capture_truncated and len(stderr) >= policy.max_output_chars:
                stderr += "\n"
            stdout, stdout_truncated = limited_output(
                stdout, policy.max_output_chars
            )
            stderr, stderr_truncated = limited_output(
                stderr, policy.max_output_chars
            )
            if process.violation_reason:
                stderr = (
                    f"{stderr}\nDas Programm wurde beendet: "
                    f"{process.violation_reason}"
                ).strip()
            with self._lock:
                stopped = target in self._stopped
            return ExecutionResult(
                process.returncode,
                stdout,
                stderr,
                stopped,
                timed_out,
                capture_truncated or stdout_truncated or stderr_truncated,
                process.violation_reason,
            )
        finally:
            self._finish(target, root, process, policy, baseline)

    def launch_preview(self, path: str | Path, course: str | Path) -> None:
        """Starte ein Pyxel-Fenster, ohne die Suite auf dessen Ende warten zu lassen."""
        target = self._target(path, course)
        root = Path(course).expanduser().resolve()
        process, policy, baseline = self._start(target, root, preview=True)

        def reap() -> None:
            try:
                wait_for_process(process, policy.timeout_seconds)
            finally:
                self._finish(target, root, process, policy, baseline)

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
    process: SandboxedProcess
    path: Path
    stdout: str = ""
    stderr: str = ""
    finished: bool = False
    timed_out: bool = False
    output_truncated: bool = False
    finished_event: threading.Event = field(default_factory=threading.Event)


class ScriptExampleManager:
    """Starte Skriptbeispiele und sammle ihre Ausgabe bereits während des Laufs."""

    def __init__(self, *, max_finished_jobs: int = 20) -> None:
        if max_finished_jobs < 1:
            raise ValueError("Mindestens ein abgeschlossenes Skriptergebnis muss erhalten bleiben.")
        self._max_finished_jobs = max_finished_jobs
        self._finished_jobs: deque[str] = deque()
        self._jobs: dict[str, ScriptExampleJob] = {}
        self._lock = threading.Lock()

    def start(
        self,
        source: str,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
        trusted: bool = False,
    ) -> str:
        descriptor, filename = tempfile.mkstemp(prefix="pykim-script-", suffix=".py")
        path = Path(filename)
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            target.write(source.rstrip() + "\n")
        policy_factory = builtin_policy if trusted else course_code_policy
        policy = policy_factory(
            path.parent,
            timeout_seconds=timeout_seconds,
            max_output_chars=max_output_chars,
            allow_gui=True,
        )
        environment = execution_environment(
            policy,
            overrides={"PYKIM_PROGRESS_MODE": "disabled"},
        )
        try:
            process = sandbox_popen(
                [*python_command(), "-u", str(path)],
                policy=policy,
                cwd=path.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=environment,
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
            for chunk in iter(lambda: stream.readline(4096), ""):
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
            job.timed_out = wait_for_process(process, policy.timeout_seconds)
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
                if job.process.violation_reason:
                    message = (
                        "\nDas Beispiel wurde beendet: "
                        f"{job.process.violation_reason}\n"
                    )
                    job.stderr = (job.stderr + message)[-policy.max_output_chars:]
                job.finished = True
                self._finished_jobs.append(job_id)
                while len(self._finished_jobs) > self._max_finished_jobs:
                    del self._jobs[self._finished_jobs.popleft()]
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
            job_ids = tuple(self._jobs)
        for job_id in job_ids:
            self.stop(job_id)


script_example_manager = ScriptExampleManager()
