"""
Sandbox Service — Manages E2B sandbox lifecycle for project previews.

Creates isolated cloud sandboxes that run generated projects,
providing a public URL for the preview iframe.

Sandbox creation is done as a background task to avoid HTTP timeouts
(Cloud Run has a 60s request deadline; npm install alone can take 60–120s).
The frontend should call /create, get 202, then poll /status.
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from app.config import get_settings

logger = logging.getLogger(__name__)


class SandboxStatus(str, Enum):
    PENDING = "pending"      # Queued, not started yet
    BUILDING = "building"    # Actively creating / installing
    READY = "ready"          # Dev server running, preview_url available
    ERROR = "error"          # Failed — see error_message


@dataclass
class SandboxInfo:
    """Track an active or in-progress sandbox."""
    sandbox_id: str | None
    preview_url: str | None
    project_id: str
    status: SandboxStatus = SandboxStatus.PENDING
    error_message: str | None = None


class SandboxService:
    """
    Manages E2B sandboxes for live project previews.

    Keeps an in-memory registry of active sandboxes keyed by project_id
    so users can reconnect to an existing sandbox.

    Creation is performed in a background asyncio task so the HTTP endpoint
    can return 202 immediately, avoiding Cloud Run's 60 s request timeout.
    """

    # Class-level registry shared across instances
    _active: dict[str, SandboxInfo] = {}
    # Track background tasks to prevent GC
    _tasks: dict[str, asyncio.Task] = {}

    # ── Public API ───────────────────────────────────────────────

    def start_sandbox_creation(
        self,
        project_id: str,
        files: list[dict[str, str]],
    ) -> SandboxInfo:
        """
        Kick off sandbox creation in the background.

        Returns immediately with a SandboxInfo whose status is PENDING.
        The caller should poll get_sandbox_status() to wait for READY or ERROR.
        """
        # Cancel any in-flight creation task for this project
        existing_task = self._tasks.get(project_id)
        if existing_task and not existing_task.done():
            existing_task.cancel()

        info = SandboxInfo(
            sandbox_id=None,
            preview_url=None,
            project_id=project_id,
            status=SandboxStatus.PENDING,
        )
        self._active[project_id] = info

        task = asyncio.create_task(
            self._build_sandbox(project_id, files),
            name=f"sandbox-create-{project_id}",
        )
        self._tasks[project_id] = task
        logger.info(
            "Background sandbox creation task started for project %s", project_id
        )
        return info

    async def get_sandbox_status(self, project_id: str) -> SandboxInfo | None:
        """
        Return the current SandboxInfo for project_id, or None if unknown.

        For READY sandboxes, verifies the E2B sandbox is still alive.
        """
        info = self._active.get(project_id)
        if not info:
            return None

        # Only ping E2B when the sandbox claims to be ready
        if info.status == SandboxStatus.READY and info.sandbox_id:
            alive = await self._ping_sandbox(info.sandbox_id)
            if not alive:
                self._active.pop(project_id, None)
                return None

        return info

    async def kill_sandbox(self, project_id: str) -> bool:
        """
        Kill the sandbox for a project.

        Returns True if a sandbox was found and killed, False otherwise.
        """
        # Cancel any in-flight build task
        task = self._tasks.pop(project_id, None)
        if task and not task.done():
            task.cancel()

        info = self._active.pop(project_id, None)
        if not info or not info.sandbox_id:
            return False

        try:
            from e2b_code_interpreter import Sandbox

            sandbox = await asyncio.to_thread(Sandbox.connect, info.sandbox_id)
            await asyncio.to_thread(sandbox.kill)
            logger.info(
                "Killed sandbox %s for project %s", info.sandbox_id, project_id
            )
        except Exception as e:
            logger.warning(
                "Failed to kill sandbox %s: %s", info.sandbox_id, e
            )

        return True

    # ── Internal helpers ─────────────────────────────────────────

    async def _build_sandbox(
        self, project_id: str, files: list[dict[str, str]]
    ) -> None:
        """
        Full sandbox bootstrap — runs as a background asyncio task.

        Transitions info.status through BUILDING → READY (or ERROR).
        """
        from e2b_code_interpreter import Sandbox

        settings = get_settings()
        os.environ["E2B_API_KEY"] = settings.e2b_api_key

        info = self._active.get(project_id)
        if not info:
            return

        # Kill any pre-existing sandbox for this project (fire and forget)
        old_info = None
        if info.sandbox_id:
            old_info = info

        info.status = SandboxStatus.BUILDING
        logger.info("Creating E2B sandbox for project %s …", project_id)

        try:
            sandbox = await asyncio.to_thread(
                Sandbox.create, timeout=settings.e2b_sandbox_timeout
            )
            sandbox_id = sandbox.sandbox_id
            info.sandbox_id = sandbox_id
            logger.info("Sandbox %s created for project %s", sandbox_id, project_id)

            app_dir = "/home/user/app"

            # ── 1. Create directories ──
            dirs_to_create: set[str] = set()
            for f in files:
                fpath = f["file_path"].lstrip("/")
                parent = "/".join(fpath.split("/")[:-1])
                if parent:
                    dirs_to_create.add(f"{app_dir}/{parent}")

            if dirs_to_create:
                mkdir_cmd = "mkdir -p " + " ".join(
                    f'"{d}"' for d in sorted(dirs_to_create)
                )
                await asyncio.to_thread(sandbox.commands.run, mkdir_cmd)

            # ── 2. Write files ──
            for f in files:
                fpath = f["file_path"].lstrip("/")
                full_path = f"{app_dir}/{fpath}"
                await asyncio.to_thread(
                    sandbox.files.write, full_path, f["file_content"]
                )

            logger.info("Wrote %d files to sandbox %s", len(files), sandbox_id)

            # ── 3. npm install ──
            logger.info("Running npm install in sandbox %s …", sandbox_id)
            install_result = await asyncio.to_thread(
                sandbox.commands.run,
                "npm install",
                cwd=app_dir,
                timeout=None,
            )
            if install_result.exit_code != 0:
                raise RuntimeError(
                    f"npm install failed (exit {install_result.exit_code}): "
                    f"{install_result.stderr}"
                )

            # ── 4. Ensure Vite React plugin ──
            logger.info("Ensuring @vitejs/plugin-react in sandbox %s …", sandbox_id)
            plugin_result = await asyncio.to_thread(
                sandbox.commands.run,
                "npm install @vitejs/plugin-react --save-dev",
                cwd=app_dir,
                timeout=120,
            )
            if plugin_result.exit_code != 0:
                logger.warning(
                    "Optional @vitejs/plugin-react install failed: %s",
                    plugin_result.stderr,
                )

            # ── 5. Patch Vite config to allow E2B hosts ──
            logger.info("Patching Vite config in sandbox %s …", sandbox_id)
            patch_script = """\
const fs = require('fs');
const configs = ['vite.config.ts', 'vite.config.js', 'vite.config.mts', 'vite.config.mjs'];
for (const file of configs) {
  try {
    let content = fs.readFileSync(file, 'utf8');
    if (content.includes('server:') || content.includes('server :')) {
      content = content.replace(/server\\s*:\\s*{/, 'server: { allowedHosts: true,');
    } else if (content.includes('defineConfig(')) {
      content = content.replace('defineConfig({', 'defineConfig({\\n  server: { host: true, allowedHosts: true },');
    }
    fs.writeFileSync(file, content);
    console.log('Patched ' + file);
    break;
  } catch (e) { /* file not found, try next */ }
}
"""
            await asyncio.to_thread(
                sandbox.files.write, f"{app_dir}/patch-vite.cjs", patch_script
            )
            await asyncio.to_thread(
                sandbox.commands.run, "node patch-vite.cjs", cwd=app_dir
            )

            # ── 6. Start dev server ──
            logger.info("Starting dev server in sandbox %s …", sandbox_id)
            await asyncio.to_thread(
                sandbox.commands.run,
                "npm run dev -- --host 0.0.0.0",
                background=True,
                cwd=app_dir,
            )

            # Give Vite a moment to compile
            await asyncio.sleep(5)

            host = await asyncio.to_thread(sandbox.get_host, 5173)
            preview_url = f"https://{host}"

            info.preview_url = preview_url
            info.status = SandboxStatus.READY

            logger.info(
                "Sandbox %s ready for project %s at %s",
                sandbox_id,
                project_id,
                preview_url,
            )

        except asyncio.CancelledError:
            logger.info("Sandbox creation cancelled for project %s", project_id)
            raise
        except Exception as exc:
            logger.exception(
                "Sandbox creation failed for project %s: %s", project_id, exc
            )
            info.status = SandboxStatus.ERROR
            info.error_message = str(exc)
            # Best-effort cleanup
            if info.sandbox_id:
                try:
                    from e2b_code_interpreter import Sandbox as _S

                    s = await asyncio.to_thread(_S.connect, info.sandbox_id)
                    await asyncio.to_thread(s.kill)
                except Exception:
                    pass

    async def _ping_sandbox(self, sandbox_id: str) -> bool:
        """Return True if the sandbox is still alive."""
        try:
            from e2b_code_interpreter import Sandbox

            await asyncio.to_thread(Sandbox.connect, sandbox_id)
            return True
        except Exception:
            return False
