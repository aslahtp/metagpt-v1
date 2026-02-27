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
from textwrap import dedent

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
    logs: list[str] = field(default_factory=list)


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

            # Detect frontend / backend roots from the incoming files.
            # We keep writing all files under app_dir but run npm commands
            # from the detected frontend directory.
            def _detect_roots() -> tuple[str, str | None]:
                package_json_paths: list[str] = []
                for f in files:
                    fpath = f["file_path"].lstrip("/")
                    if fpath.endswith("package.json"):
                        package_json_paths.append(fpath)

                def _parent_dir(path: str) -> str:
                    if "/" not in path:
                        return "."
                    return path.rsplit("/", 1)[0]

                def _pick_by_prefix(prefixes: list[str]) -> str | None:
                    # Prefer the deepest match under the prefix (e.g. frontend/client/package.json).
                    matches = [
                        p for p in package_json_paths if any(p.startswith(f"{pre}/") for pre in prefixes)
                    ]
                    if not matches:
                        return None
                    matches.sort(key=lambda p: (p.count("/"), len(p)), reverse=True)
                    return matches[0]

                frontend_rel_dir = "."
                backend_rel_dir: str | None = None

                # If we see a conventional frontend folder, treat that as the frontend root
                # even if a root package.json exists (workspace / monorepo-like setups).
                chosen_frontend_pkg = _pick_by_prefix(["frontend", "client", "web"])

                if chosen_frontend_pkg:
                    frontend_rel_dir = _parent_dir(chosen_frontend_pkg)
                elif len(package_json_paths) == 1:
                    # Single package.json anywhere → treat as the app root
                    frontend_rel_dir = _parent_dir(package_json_paths[0])
                elif "package.json" in package_json_paths:
                    # Fallback: root package.json with no better hint
                    frontend_rel_dir = "."

                chosen_backend_pkg = _pick_by_prefix(["backend", "server"])
                if chosen_backend_pkg:
                    backend_rel_dir = _parent_dir(chosen_backend_pkg)

                return frontend_rel_dir, backend_rel_dir

            def _log(line: str) -> None:
                """Append a log line and mirror to logger."""
                info.logs.append(line)
                logger.info("[sandbox:%s] %s", project_id, line)

            def _capture(prefix: str, result: object) -> None:
                """Capture stdout/stderr from a command result."""
                stdout = getattr(result, "stdout", "") or ""
                stderr = getattr(result, "stderr", "") or ""
                for line in stdout.strip().splitlines():
                    _log(f"[{prefix}] {line}")
                for line in stderr.strip().splitlines():
                    _log(f"[{prefix}:err] {line}")

            # Detect frontend/backend roots now that helpers are defined
            frontend_rel_dir, backend_rel_dir = _detect_roots()
            frontend_cwd = f"{app_dir}/{frontend_rel_dir}" if frontend_rel_dir != "." else app_dir
            if frontend_rel_dir != ".":
                _log(f"[setup] Detected frontend at {frontend_rel_dir}/")
            else:
                _log("[setup] Detected single-root frontend at project root")
            if backend_rel_dir:
                _log(f"[setup] Detected backend candidate at {backend_rel_dir}/")

            # ── 1. Create directories ──
            _log("[setup] Creating project directories…")
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
            _log(f"[setup] Writing {len(files)} files…")
            for f in files:
                fpath = f["file_path"].lstrip("/")
                full_path = f"{app_dir}/{fpath}"
                await asyncio.to_thread(
                    sandbox.files.write, full_path, f["file_content"]
                )

            _log(f"[setup] Wrote {len(files)} files to sandbox")

            # ── 2b. Inject console bridge script ──
            _log("[setup] Injecting console bridge…")
            # Use the detected frontend root so the bridge is injected
            # into the actual app that the iframe renders.
            await self._inject_console_bridge(sandbox, frontend_cwd)

            # ── 3. npm install ──
            _log("[npm install] Running npm install…")
            install_result = await asyncio.to_thread(
                sandbox.commands.run,
                "npm install",
                cwd=frontend_cwd,
                timeout=None,
            )
            _capture("npm install", install_result)
            if install_result.exit_code != 0:
                raise RuntimeError(
                    f"npm install failed (exit {install_result.exit_code}): "
                    f"{install_result.stderr}"
                )

            # ── 4. Ensure Vite React plugin ──
            _log("[plugin] Installing @vitejs/plugin-react…")
            plugin_result = await asyncio.to_thread(
                sandbox.commands.run,
                "npm install @vitejs/plugin-react --save-dev",
                cwd=frontend_cwd,
                timeout=120,
            )
            _capture("plugin", plugin_result)
            if plugin_result.exit_code != 0:
                logger.warning(
                    "Optional @vitejs/plugin-react install failed: %s",
                    plugin_result.stderr,
                )

            # ── 5. Patch Vite config to allow E2B hosts ──
            _log("[vite] Patching Vite config…")
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
                sandbox.files.write, f"{frontend_cwd}/patch-vite.cjs", patch_script
            )
            patch_result = await asyncio.to_thread(
                sandbox.commands.run, "node patch-vite.cjs", cwd=frontend_cwd
            )
            _capture("vite", patch_result)

            # ── 6. Optional backend start + frontend API base mapping (split frontend/backend only) ──
            backend_public_url: str | None = None
            backend_port = 8080

            # Only apply backend URL mapping when the architecture is split into
            # a non-root frontend folder plus a backend folder.
            if backend_rel_dir and frontend_rel_dir != ".":
                backend_cwd = f"{app_dir}/{backend_rel_dir}"
                _log(
                    f"[backend] Installing backend dependencies in {backend_rel_dir}/ …"
                )
                try:
                    backend_install = await asyncio.to_thread(
                        sandbox.commands.run,
                        "npm install",
                        cwd=backend_cwd,
                        timeout=None,
                    )
                    _capture("backend:npm install", backend_install)
                    if backend_install.exit_code != 0:
                        _log(
                            "[backend:error] npm install failed; backend may not be available "
                            f"(exit {backend_install.exit_code})"
                        )
                    else:
                        _log(
                            f"[backend] Starting backend on port {backend_port} (npm run dev || npm start) in background…"
                        )
                        # Best-effort: many Node frameworks respect PORT/HOST.
                        backend_dev = await asyncio.to_thread(
                            sandbox.commands.run,
                            f"PORT={backend_port} HOST=0.0.0.0 npm run dev || PORT={backend_port} HOST=0.0.0.0 npm start",
                            cwd=backend_cwd,
                            background=True,
                        )
                        _capture("backend:dev", backend_dev)

                        # Map backend port to a public E2B host URL for the browser.
                        backend_host = await asyncio.to_thread(
                            sandbox.get_host, backend_port
                        )
                        backend_public_url = f"https://{backend_host}"
                        _log(f"[backend] Public backend URL: {backend_public_url}")

                        # Inject API base URL for the frontend dev server (Vite mode).
                        env_path = f"{frontend_cwd}/.env.sandbox"
                        env_body = f"VITE_API_BASE_URL={backend_public_url}\n"
                        await asyncio.to_thread(sandbox.files.write, env_path, env_body)
                        _log(
                            f"[frontend] Wrote sandbox env (.env.sandbox) with VITE_API_BASE_URL for {frontend_rel_dir}/"
                        )
                        await self._inject_network_bridge(
                            sandbox, frontend_cwd, backend_public_url
                        )
                except Exception as backend_exc:
                    _log(
                        f"[backend:error] Failed to start/map backend; frontend preview is still available ({backend_exc})"
                    )

            # ── 7. Start frontend dev server ──
            dev_cmd = "npm run dev -- --host 0.0.0.0"
            if backend_public_url:
                # Use Vite mode so .env.sandbox is loaded without clobbering .env.
                dev_cmd = "npm run dev -- --host 0.0.0.0 --mode sandbox"

            _log("[dev] Starting dev server…")
            await asyncio.to_thread(
                sandbox.commands.run,
                dev_cmd,
                background=True,
                cwd=frontend_cwd,
            )

            # Give Vite a moment to compile
            await asyncio.sleep(5)

            host = await asyncio.to_thread(sandbox.get_host, 5173)
            preview_url = f"https://{host}"

            info.preview_url = preview_url
            info.status = SandboxStatus.READY
            _log(f"[ready] Preview available at {preview_url}")

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

    async def _inject_console_bridge(self, sandbox: object, app_dir: str) -> None:
        """
        Write a console-bridge script that patches console.* and
        window.onerror to forward messages to the parent frame via
        postMessage.  Then patch index.html to include it.
        """
        bridge_js = dedent("""\
            (function() {
              if (window.__consoleBridgeInstalled) return;
              window.__consoleBridgeInstalled = true;

              var _origLog   = console.log;
              var _origWarn  = console.warn;
              var _origError = console.error;
              var _origInfo  = console.info;

              function _send(level, args) {
                try {
                  var parts = [];
                  for (var i = 0; i < args.length; i++) {
                    try {
                      parts.push(typeof args[i] === 'object' ? JSON.stringify(args[i]) : String(args[i]));
                    } catch(e) {
                      parts.push('[unserializable]');
                    }
                  }
                  window.parent.postMessage({
                    type: '__console_bridge__',
                    level: level,
                    message: parts.join(' '),
                    timestamp: Date.now()
                  }, '*');
                } catch(e) { /* ignore */ }
              }

              console.log   = function() { _send('log',   arguments); _origLog.apply(console, arguments); };
              console.warn  = function() { _send('warn',  arguments); _origWarn.apply(console, arguments); };
              console.error = function() { _send('error', arguments); _origError.apply(console, arguments); };
              console.info  = function() { _send('info',  arguments); _origInfo.apply(console, arguments); };

              window.onerror = function(msg, src, line, col, err) {
                _send('error', ['Uncaught: ' + msg + ' at ' + src + ':' + line + ':' + col]);
              };
              window.addEventListener('unhandledrejection', function(e) {
                _send('error', ['Unhandled rejection: ' + (e.reason || e)]);
              });
            })();
        """)

        await asyncio.to_thread(
            sandbox.files.write,
            f"{app_dir}/public/__console_bridge.js",
            bridge_js,
        )

        # Patch index.html to include the script early
        patch_html_script = dedent("""\
            const fs = require('fs');
            const path = require('path');
            const htmlPath = path.join(process.cwd(), 'index.html');
            try {
              let html = fs.readFileSync(htmlPath, 'utf8');
              if (!html.includes('__console_bridge')) {
                html = html.replace(
                  '<head>',
                  '<head><script src="/__console_bridge.js"></script>'
                );
                fs.writeFileSync(htmlPath, html);
                console.log('Injected console bridge into index.html');
              }
            } catch(e) {
              console.log('Could not patch index.html:', e.message);
            }
        """)

        await asyncio.to_thread(
            sandbox.files.write,
            f"{app_dir}/inject-bridge.cjs",
            patch_html_script,
        )
        await asyncio.to_thread(
            sandbox.commands.run,
            "node inject-bridge.cjs",
            cwd=app_dir,
        )

    async def _inject_network_bridge(
        self, sandbox: object, app_dir: str, backend_public_url: str
    ) -> None:
        """
        Inject a small network bridge that rewrites browser requests targeting
        localhost:8080 / 127.0.0.1:8080 to the sandbox backend public URL.

        This makes previews work even when generated frontend code hardcodes
        http://localhost:8080, without requiring template-specific changes.
        """
        bridge_js = dedent(
            f"""\
            (function() {{
              if (window.__sandboxNetworkBridgeInstalled) return;
              window.__sandboxNetworkBridgeInstalled = true;

              var backendBase = {backend_public_url!r};
              var targets = ['http://localhost:8080', 'http://127.0.0.1:8080', 'http://0.0.0.0:8080'];

              function rewrite(url) {{
                try {{
                  if (!url) return url;
                  if (typeof url !== 'string') return url;
                  for (var i = 0; i < targets.length; i++) {{
                    if (url.indexOf(targets[i]) === 0) {{
                      return backendBase + url.slice(targets[i].length);
                    }}
                  }}
                  return url;
                }} catch (e) {{
                  return url;
                }}
              }}

              // Patch fetch
              if (window.fetch) {{
                var _origFetch = window.fetch;
                window.fetch = function(input, init) {{
                  try {{
                    if (typeof input === 'string') {{
                      input = rewrite(input);
                    }} else if (input && typeof input.url === 'string') {{
                      // Request object: recreate with rewritten URL
                      var newUrl = rewrite(input.url);
                      input = new Request(newUrl, input);
                    }}
                  }} catch (e) {{}}
                  return _origFetch.call(this, input, init);
                }};
              }}

              // Patch XHR (axios)
              if (window.XMLHttpRequest) {{
                var _origOpen = window.XMLHttpRequest.prototype.open;
                window.XMLHttpRequest.prototype.open = function(method, url) {{
                  try {{
                    url = rewrite(url);
                  }} catch (e) {{}}
                  return _origOpen.apply(this, arguments.length >= 2 ? [method, url].concat([].slice.call(arguments, 2)) : arguments);
                }};
              }}
            }})();"""
        )

        await asyncio.to_thread(
            sandbox.files.write,
            f"{app_dir}/public/__sandbox_network_bridge.js",
            bridge_js,
        )

        patch_html_script = dedent(
            """\
            const fs = require('fs');
            const path = require('path');
            const htmlPath = path.join(process.cwd(), 'index.html');
            try {
              let html = fs.readFileSync(htmlPath, 'utf8');
              if (!html.includes('__sandbox_network_bridge')) {
                html = html.replace(
                  '<head>',
                  '<head><script src="/__sandbox_network_bridge.js"></script>'
                );
                fs.writeFileSync(htmlPath, html);
                console.log('Injected sandbox network bridge into index.html');
              }
            } catch(e) {
              console.log('Could not patch index.html for network bridge:', e.message);
            }
            """
        )

        await asyncio.to_thread(
            sandbox.files.write,
            f"{app_dir}/inject-network-bridge.cjs",
            patch_html_script,
        )
        await asyncio.to_thread(
            sandbox.commands.run,
            "node inject-network-bridge.cjs",
            cwd=app_dir,
        )

    async def _ping_sandbox(self, sandbox_id: str) -> bool:
        """Return True if the sandbox is still alive."""
        try:
            from e2b_code_interpreter import Sandbox

            await asyncio.to_thread(Sandbox.connect, sandbox_id)
            return True
        except Exception:
            return False
