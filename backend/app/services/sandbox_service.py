"""
Sandbox Service — Manages E2B sandbox lifecycle for project previews.

Creates isolated cloud sandboxes that run generated projects,
providing a public URL for the preview iframe.
"""

import asyncio
import logging
import os
from dataclasses import dataclass

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SandboxInfo:
    """Track an active sandbox."""
    sandbox_id: str
    preview_url: str
    project_id: str


class SandboxService:
    """
    Manages E2B sandboxes for live project previews.

    Keeps an in-memory registry of active sandboxes keyed by project_id
    so users can reconnect to an existing sandbox.
    """

    # Class-level registry shared across instances
    _active: dict[str, SandboxInfo] = {}

    async def create_sandbox(
        self,
        project_id: str,
        files: list[dict[str, str]],
    ) -> SandboxInfo:
        """
        Create an E2B sandbox, write project files, install deps, and start dev server.

        Args:
            project_id: Project identifier.
            files: List of dicts with 'file_path' and 'file_content' keys.

        Returns:
            SandboxInfo with sandbox_id and public preview_url.
        """
        from e2b_code_interpreter import Sandbox

        settings = get_settings()

        # E2B SDK reads API key from this env var
        os.environ["E2B_API_KEY"] = settings.e2b_api_key

        # Kill any existing sandbox for this project
        if project_id in self._active:
            await self.kill_sandbox(project_id)

        logger.info("Creating E2B sandbox for project %s", project_id)

        # Create sandbox with timeout (in seconds)
        sandbox = await asyncio.to_thread(
            Sandbox.create, timeout=settings.e2b_sandbox_timeout
        )

        sandbox_id = sandbox.sandbox_id
        logger.info("Sandbox %s created for project %s", sandbox_id, project_id)

        try:
            # Write all project files into the sandbox
            app_dir = "/home/user/app"

            # Collect unique directories to create
            dirs_to_create = set()
            for f in files:
                fpath = f["file_path"].lstrip("/")
                parent = "/".join(fpath.split("/")[:-1])
                if parent:
                    dirs_to_create.add(f"{app_dir}/{parent}")

            # Create all directories at once
            if dirs_to_create:
                mkdir_cmd = "mkdir -p " + " ".join(
                    f'"{d}"' for d in sorted(dirs_to_create)
                )
                await asyncio.to_thread(
                    sandbox.commands.run, mkdir_cmd
                )

            # Write each file
            for f in files:
                fpath = f["file_path"].lstrip("/")
                full_path = f"{app_dir}/{fpath}"
                logger.info("Writing file: %s", full_path)
                await asyncio.to_thread(
                    sandbox.files.write,
                    full_path,
                    f["file_content"],
                )

            logger.info("Wrote %d files to sandbox %s", len(files), sandbox_id)

            # List what we wrote (debug)
            ls_result = await asyncio.to_thread(
                sandbox.commands.run,
                f"find {app_dir} -type f | head -20",
            )
            logger.info("Files in sandbox:\n%s", ls_result.stdout)

            # Install dependencies (timeout=None means no limit)
            logger.info("Running npm install in sandbox %s...", sandbox_id)
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

            # Ensure Vite React plugin is installed (vite.config often uses it without listing it)
            logger.info("Ensuring @vitejs/plugin-react in sandbox %s...", sandbox_id)
            plugin_result = await asyncio.to_thread(
                sandbox.commands.run,
                "npm install @vitejs/plugin-react --save-dev",
                cwd=app_dir,
                timeout=120,
            )
            if plugin_result.exit_code != 0:
                logger.warning(
                    "Optional @vitejs/plugin-react install failed: %s", plugin_result.stderr
                )

            # Patch vite config to allow E2B sandbox hosts
            logger.info("Patching Vite config to allow E2B hosts...")
            patch_script = """\
const fs = require('fs');
const configs = ['vite.config.ts', 'vite.config.js', 'vite.config.mts', 'vite.config.mjs'];
for (const file of configs) {
  try {
    let content = fs.readFileSync(file, 'utf8');
    // Insert allowedHosts into existing server config or add new server config
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

            # Start dev server in background (returns immediately)
            logger.info("Starting dev server in sandbox %s...", sandbox_id)
            await asyncio.to_thread(
                sandbox.commands.run,
                "npm run dev -- --host 0.0.0.0",
                background=True,
                cwd=app_dir,
            )

            # Wait for the dev server to bind (Vite may need a few seconds to compile)
            await asyncio.sleep(5)

            # Get the public URL for port 5173 (Vite default)
            host = await asyncio.to_thread(sandbox.get_host, 5173)
            preview_url = f"https://{host}"

            info = SandboxInfo(
                sandbox_id=sandbox_id,
                preview_url=preview_url,
                project_id=project_id,
            )
            self._active[project_id] = info

            logger.info(
                "Sandbox %s ready for project %s at %s",
                sandbox_id,
                project_id,
                preview_url,
            )
            return info

        except Exception:
            # Clean up on failure
            try:
                await asyncio.to_thread(sandbox.kill)
            except Exception:
                pass
            raise

    async def get_sandbox_status(self, project_id: str) -> SandboxInfo | None:
        """
        Check if a sandbox is alive for the given project.

        Returns:
            SandboxInfo if alive, None otherwise.
        """
        info = self._active.get(project_id)
        if not info:
            return None

        # Verify it's still running by trying to connect
        try:
            from e2b_code_interpreter import Sandbox

            sandbox = await asyncio.to_thread(
                Sandbox.connect,
                info.sandbox_id,
            )
            # Connection succeeded — sandbox is alive
            return info
        except Exception:
            # Sandbox no longer exists
            self._active.pop(project_id, None)
            return None

    async def kill_sandbox(self, project_id: str) -> bool:
        """
        Kill the sandbox for a project.

        Returns:
            True if killed, False if no sandbox was found.
        """
        info = self._active.pop(project_id, None)
        if not info:
            return False

        try:
            from e2b_code_interpreter import Sandbox

            sandbox = await asyncio.to_thread(
                Sandbox.connect,
                info.sandbox_id,
            )
            await asyncio.to_thread(sandbox.kill)
            logger.info("Killed sandbox %s for project %s", info.sandbox_id, project_id)
        except Exception as e:
            logger.warning("Failed to kill sandbox %s: %s", info.sandbox_id, e)

        return True
