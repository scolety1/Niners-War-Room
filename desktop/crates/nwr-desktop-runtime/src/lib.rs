mod process_guard;

use hmac::{Hmac, Mac};
use process_guard::GuardedChild;
use serde::{Deserialize, Serialize};
use sha2::Sha256;
use std::env;
use std::error::Error;
use std::fmt;
use std::fs::{self, OpenOptions};
use std::io::{self, BufRead, BufReader, Read, Write};
use std::net::{Ipv4Addr, SocketAddrV4, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{ChildStdout, Command, Stdio};
use std::sync::{mpsc, Mutex};
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tauri::{AppHandle, Manager, RunEvent, State, Wry};
use uuid::Uuid;

#[cfg(windows)]
use std::os::windows::process::CommandExt;
#[cfg(windows)]
use windows_sys::Win32::System::Threading::CREATE_NO_WINDOW;

const CONTRACT_VERSION: &str = "1.0.0";
const STARTUP_PROTOCOL: &str = "nwr-desktop-startup-v1";
const LOOPBACK_HOST: &str = "127.0.0.1";
const DEFAULT_STARTUP_TIMEOUT_MS: u64 = 90_000;
const MAX_HTTP_RESPONSE_BYTES: u64 = 16 * 1024;
const MAX_STARTUP_REPORT_BYTES: usize = 4 * 1024;
const HIGH_EPHEMERAL_PORT_MIN: u16 = 49_152;
const SECRET_ENV_NAMES: [&str; 4] = [
    "NWR_DYNASTY_API_TOKEN",
    "NWR_REDRAFT_API_TOKEN",
    "NWR_DESKTOP_API_TOKEN",
    "NWR_DESKTOP_STARTUP_PROOF_KEY",
];
const PORT_ENV_NAMES: [&str; 3] = [
    "NWR_DYNASTY_API_PORT",
    "NWR_REDRAFT_API_PORT",
    "NWR_DESKTOP_API_PORT",
];
#[cfg(not(debug_assertions))]
const SIDECAR_RUNTIME_NAME: &str = "nwr-desktop-api.exe";

#[cfg(any(not(debug_assertions), test))]
const DYNASTY_RESOURCE_FILES: [&str; 10] = [
    "config/nwr_future_pick_context_v1.csv",
    "docs/draft_day_exports/final_board_v1_20260622/app_props/mock_draft/mock_pick_context.csv",
    "docs/hq/master/nwr_model_v4_2026_rookie_board_review_v1_20260730/2026_ROOKIE_IDENTITY_BLOCKERS.csv",
    "docs/hq/master/nwr_model_v4_2026_rookie_board_review_v1_20260730/MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv",
    "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/MANIFEST.json",
    "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/OUTCOME_V3_INTEGRATION_PACK.csv",
    "docs/hq/model/current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708/rebuilt_full_player_board_value_review_rows.csv",
    "docs/hq/model/nwr_unified_research_preview_v1_20260808/MANIFEST.json",
    "docs/hq/model/nwr_unified_research_preview_v1_20260808/ROOKIE_VETERAN_NEIGHBORHOODS.csv",
    "docs/hq/model/nwr_unified_research_preview_v1_20260808/UNIFIED_DYNASTY_RESEARCH_PREVIEW.csv",
];
#[cfg(any(not(debug_assertions), test))]
const REDRAFT_RESOURCE_FILES: [&str; 3] = [
    "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/BLOCKED_2026_ROOKIES.csv",
    "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv",
    "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/NWR_DATA_GOVERNANCE.json",
];
#[cfg(any(not(debug_assertions), test))]
const FORBIDDEN_RESOURCE_TREES: [&str; 4] =
    ["sample_data", "templates", "data_packs", "assets/branding"];

type HmacSha256 = Hmac<Sha256>;

struct BackendProgram {
    executable: PathBuf,
    script: Option<PathBuf>,
    kind: &'static str,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct StartupReport {
    protocol: String,
    host: String,
    port: u16,
    mode: String,
    pid: u32,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct StartupCredentials<'a> {
    api_token: &'a str,
    startup_proof_key: &'a str,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct StartupProofEnvelope {
    contract_version: String,
    mode: String,
    data: StartupProofData,
    warnings: Vec<serde_json::Value>,
    errors: Vec<serde_json::Value>,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct StartupProofData {
    status: String,
    transport: String,
    startup_proof: String,
}

#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct HealthEnvelope {
    contract_version: String,
    mode: String,
    data: HealthData,
    warnings: Vec<serde_json::Value>,
    errors: Vec<serde_json::Value>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct HealthData {
    status: String,
    transport: String,
    authenticated: bool,
}

#[derive(Clone, Copy, Debug)]
pub enum AppMode {
    Dynasty,
    Redraft,
}

impl AppMode {
    fn as_str(self) -> &'static str {
        match self {
            Self::Dynasty => "dynasty",
            Self::Redraft => "redraft",
        }
    }

    #[cfg(debug_assertions)]
    fn port_env(self) -> &'static str {
        match self {
            Self::Dynasty => "NWR_DYNASTY_API_PORT",
            Self::Redraft => "NWR_REDRAFT_API_PORT",
        }
    }

    #[cfg(debug_assertions)]
    fn token_env(self) -> &'static str {
        match self {
            Self::Dynasty => "NWR_DYNASTY_API_TOKEN",
            Self::Redraft => "NWR_REDRAFT_API_TOKEN",
        }
    }
}

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeDescriptor {
    mode: &'static str,
    api_base_url: String,
    token: String,
    contract_version: &'static str,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct PersistedRuntimeState<'a> {
    mode: &'static str,
    api_base_url: &'a str,
    contract_version: &'static str,
    pid: u32,
    running: bool,
    containment: &'static str,
    started_at_unix_ms: u64,
    stopped_at_unix_ms: Option<u64>,
}

struct DesktopState {
    descriptor: RuntimeDescriptor,
    backend: Mutex<Option<GuardedChild>>,
    state_path: PathBuf,
    lifecycle_log_path: PathBuf,
    pid: u32,
    containment: &'static str,
    started_at_unix_ms: u64,
}

impl DesktopState {
    fn launch(app: &AppHandle<Wry>, mode: AppMode) -> RuntimeResult<Self> {
        let app_data_dir = app.path().app_local_data_dir()?;
        let state_dir = app_data_dir.join("state");
        let log_dir = app.path().app_log_dir()?;
        fs::create_dir_all(&state_dir)?;
        fs::create_dir_all(&log_dir)?;

        let state_path = state_dir.join("runtime.json");
        let lifecycle_log_path = log_dir.join("lifecycle.log");
        let stdout_log = append_file(&log_dir.join("api.stdout.log"))?;
        let stderr = append_file(&log_dir.join("api.stderr.log"))?;

        let requested_port = resolve_requested_port(mode)?;
        let token = resolve_token(mode)?;
        let startup_proof_key = generate_distinct_secret(&token);
        let repo_root = resolve_repo_root(app, mode)?;
        let backend_program = resolve_backend_program(app, &repo_root)?;

        append_lifecycle(
            &lifecycle_log_path,
            &format!(
                "starting mode={} transport=ephemeral-loopback repo_root={} backend={} executable={}",
                mode.as_str(),
                repo_root.display(),
                backend_program.kind,
                backend_program.executable.display()
            ),
        );

        let mut command = Command::new(&backend_program.executable);
        command.current_dir(&repo_root);
        if let Some(script) = &backend_program.script {
            command.arg(script);
        }
        command
            .arg("--host")
            .arg(LOOPBACK_HOST)
            .arg("--port")
            .arg(requested_port.to_string())
            .arg("--mode")
            .arg(mode.as_str())
            .arg("--repo-root")
            .arg(&repo_root)
            .env("NWR_DESKTOP_MODE", mode.as_str())
            .env("NWR_DESKTOP_STATE_DIR", &state_dir)
            .env("NWR_DESKTOP_LOG_DIR", &log_dir)
            .env("NWR_REDRAFT_HOME", state_dir.join("redraft"))
            .env(
                "NWR_PERSONAL_WORKSPACE_ROOT",
                state_dir.join("personal-workspace"),
            )
            .env("PYTHONDONTWRITEBYTECODE", "1")
            .env("PYTHONUNBUFFERED", "1")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::from(stderr));

        // A parent may use token/port overrides for development, but the child receives
        // neither through its inherited environment. Secrets cross only the private stdin pipe.
        for name in SECRET_ENV_NAMES {
            command.env_remove(name);
        }
        for name in PORT_ENV_NAMES {
            command.env_remove(name);
        }
        command.env_remove("NWR_DESKTOP_API_BASE_URL");

        #[cfg(windows)]
        command.creation_flags(CREATE_NO_WINDOW);

        let child = command.spawn().map_err(|error| {
            RuntimeError::message(format!(
                "failed to start the desktop API with {}: {error}",
                backend_program.executable.display()
            ))
        })?;
        let mut backend = GuardedChild::new(child);
        let launcher_pid = backend.id();
        let containment = backend.containment();
        if let Some(warning) = backend.containment_warning() {
            append_lifecycle(&lifecycle_log_path, warning);
        }

        // PyInstaller one-file launches a worker descendant. Without a kill-on-close job,
        // exact-child fallback cannot guarantee cleanup of that worker, so Windows fails
        // before either launch secret is written to the child.
        #[cfg(windows)]
        if containment != "windows-job-object" {
            let error = RuntimeError::message(
                "Windows Job Object containment is required before desktop API authentication",
            );
            append_lifecycle(&lifecycle_log_path, &format!("startup failed: {error}"));
            return Err(error);
        }

        let stdout = backend
            .take_stdout()
            .ok_or_else(|| RuntimeError::message("desktop API stdout pipe was unavailable"))?;
        let report_receiver = capture_startup_report(stdout, stdout_log);

        let mut stdin = backend
            .take_stdin()
            .ok_or_else(|| RuntimeError::message("desktop API stdin pipe was unavailable"))?;
        let credentials = serde_json::to_vec(&StartupCredentials {
            api_token: &token,
            startup_proof_key: &startup_proof_key,
        })?;
        stdin.write_all(&credentials)?;
        stdin.write_all(b"\n")?;
        stdin.flush()?;
        drop(stdin);

        let timeout = resolve_startup_timeout()?;
        let deadline = Instant::now() + timeout;
        let report = receive_startup_report(
            &mut backend,
            report_receiver,
            mode,
            requested_port,
            deadline,
        )
        .map_err(|error| {
            append_lifecycle(&lifecycle_log_path, &format!("startup failed: {error}"));
            error
        })?;

        verify_listener_until(
            &mut backend,
            report.port,
            report.pid,
            &backend_program.executable,
            deadline,
        )
        .map_err(|error| {
            append_lifecycle(&lifecycle_log_path, &format!("startup failed: {error}"));
            error
        })?;

        verify_startup_proof(
            &mut backend,
            report.port,
            &startup_proof_key,
            mode,
            deadline,
        )
        .map_err(|error| {
            append_lifecycle(&lifecycle_log_path, &format!("startup failed: {error}"));
            error
        })?;

        wait_for_health(
            &mut backend,
            report.port,
            report.pid,
            &backend_program.executable,
            &token,
            mode,
            deadline,
        )
        .map_err(|error| {
            append_lifecycle(&lifecycle_log_path, &format!("startup failed: {error}"));
            error
        })?;
        if let Some(status) = backend.try_wait()? {
            let error = RuntimeError::message(format!(
                "desktop API exited after authenticated startup: {status}"
            ));
            append_lifecycle(&lifecycle_log_path, &format!("startup failed: {error}"));
            return Err(error);
        }

        let api_base_url = format!("http://{LOOPBACK_HOST}:{}", report.port);
        let descriptor = RuntimeDescriptor {
            mode: mode.as_str(),
            api_base_url,
            token,
            contract_version: CONTRACT_VERSION,
        };
        let started_at_unix_ms = unix_time_ms();
        let state = Self {
            descriptor,
            backend: Mutex::new(Some(backend)),
            state_path,
            lifecycle_log_path,
            pid: report.pid,
            containment,
            started_at_unix_ms,
        };
        state.persist(true, None)?;
        append_lifecycle(
            &state.lifecycle_log_path,
            &format!(
                "ready launcher_pid={launcher_pid} listener_pid={} port={} containment={containment} startup_proof=hmac-sha256",
                report.pid, report.port
            ),
        );
        Ok(state)
    }

    fn shutdown(&self) {
        let mut backend_slot = self
            .backend
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner());
        let Some(mut backend) = backend_slot.take() else {
            return;
        };

        if let Err(error) = backend.shutdown() {
            append_lifecycle(
                &self.lifecycle_log_path,
                &format!("desktop API exact-child shutdown failed: {error}"),
            );
        } else {
            append_lifecycle(&self.lifecycle_log_path, "desktop API stopped");
        }
        let _ = self.persist(false, Some(unix_time_ms()));
    }

    fn persist(&self, running: bool, stopped_at_unix_ms: Option<u64>) -> RuntimeResult<()> {
        // Session tokens and startup proof material are deliberately never persisted to disk.
        let value = PersistedRuntimeState {
            mode: self.descriptor.mode,
            api_base_url: &self.descriptor.api_base_url,
            contract_version: CONTRACT_VERSION,
            pid: self.pid,
            running,
            containment: self.containment,
            started_at_unix_ms: self.started_at_unix_ms,
            stopped_at_unix_ms,
        };
        let json = serde_json::to_vec_pretty(&value)?;
        fs::write(&self.state_path, json)?;
        Ok(())
    }
}

impl Drop for DesktopState {
    fn drop(&mut self) {
        self.shutdown();
    }
}

enum ManagedDesktopState {
    Ready(DesktopState),
    Failed,
}

impl ManagedDesktopState {
    fn shutdown(&self) {
        if let Self::Ready(state) = self {
            state.shutdown();
        }
    }
}

#[tauri::command]
fn desktop_runtime(state: State<'_, ManagedDesktopState>) -> Result<RuntimeDescriptor, String> {
    match state.inner() {
        ManagedDesktopState::Ready(runtime) => Ok(runtime.descriptor.clone()),
        ManagedDesktopState::Failed => Err(
            "The local NWR service did not start. Close this window and open NWR again."
                .to_string(),
        ),
    }
}

pub fn run(context: tauri::Context<Wry>, mode: AppMode) {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.unminimize();
                let _ = window.set_focus();
            }
        }))
        .invoke_handler(tauri::generate_handler![desktop_runtime])
        .setup(move |app| {
            let state = match DesktopState::launch(app.handle(), mode) {
                Ok(state) => ManagedDesktopState::Ready(state),
                Err(_) => ManagedDesktopState::Failed,
            };
            if !app.manage(state) {
                return Err(Box::new(RuntimeError::message(
                    "desktop runtime state was already registered",
                )) as Box<dyn Error>);
            }
            let window = app.get_webview_window("main").ok_or_else(|| {
                Box::new(RuntimeError::message("main window was not created")) as Box<dyn Error>
            })?;
            window.show()?;
            window.set_focus()?;
            Ok(())
        })
        .build(context)
        .expect("failed to build NWR Desktop");

    let exit_code = app.run_return(|app_handle, event| {
        if matches!(event, RunEvent::ExitRequested { .. } | RunEvent::Exit) {
            if let Some(state) = app_handle.try_state::<ManagedDesktopState>() {
                state.shutdown();
            }
        }
    });
    std::process::exit(exit_code);
}

#[cfg(debug_assertions)]
fn resolve_requested_port(mode: AppMode) -> RuntimeResult<u16> {
    for name in [mode.port_env(), "NWR_DESKTOP_API_PORT"] {
        if let Some(value) = nonempty_env(name) {
            return value.parse::<u16>().map_err(|_| {
                RuntimeError::message(format!("{name} must be a TCP port between 0 and 65535"))
            });
        }
    }
    Ok(0)
}

#[cfg(not(debug_assertions))]
fn resolve_requested_port(_mode: AppMode) -> RuntimeResult<u16> {
    // Release launches always bind a fresh random high loopback port in the Python child.
    Ok(0)
}

#[cfg(debug_assertions)]
fn resolve_token(mode: AppMode) -> RuntimeResult<String> {
    for name in [mode.token_env(), "NWR_DESKTOP_API_TOKEN"] {
        if let Some(value) = nonempty_env(name) {
            validate_secret(name, &value)?;
            return Ok(value);
        }
    }
    Ok(random_secret())
}

#[cfg(not(debug_assertions))]
fn resolve_token(_mode: AppMode) -> RuntimeResult<String> {
    // Release credentials are never sourced from the parent environment.
    Ok(random_secret())
}

fn generate_distinct_secret(api_token: &str) -> String {
    loop {
        let value = random_secret();
        if value != api_token {
            return value;
        }
    }
}

fn random_secret() -> String {
    format!("{}{}", Uuid::new_v4().simple(), Uuid::new_v4().simple())
}

#[cfg(debug_assertions)]
fn validate_secret(name: &str, value: &str) -> RuntimeResult<()> {
    if !(32..=512).contains(&value.len()) || !value.bytes().all(|byte| byte.is_ascii_graphic()) {
        return Err(RuntimeError::message(format!(
            "{name} must contain 32-512 printable ASCII characters"
        )));
    }
    Ok(())
}

fn resolve_startup_timeout() -> RuntimeResult<Duration> {
    let Some(value) = nonempty_env("NWR_DESKTOP_API_STARTUP_TIMEOUT_MS") else {
        return Ok(Duration::from_millis(DEFAULT_STARTUP_TIMEOUT_MS));
    };
    let milliseconds = value.parse::<u64>().map_err(|_| {
        RuntimeError::message("NWR_DESKTOP_API_STARTUP_TIMEOUT_MS must be an integer")
    })?;
    if !(500..=120_000).contains(&milliseconds) {
        return Err(RuntimeError::message(
            "NWR_DESKTOP_API_STARTUP_TIMEOUT_MS must be between 500 and 120000",
        ));
    }
    Ok(Duration::from_millis(milliseconds))
}

#[cfg(debug_assertions)]
fn resolve_repo_root(_app: &AppHandle<Wry>, _mode: AppMode) -> RuntimeResult<PathBuf> {
    if let Some(value) = env::var_os("NWR_DESKTOP_REPO_ROOT").filter(|value| !value.is_empty()) {
        let path = PathBuf::from(value);
        if !path.is_absolute() {
            return Err(RuntimeError::message(
                "NWR_DESKTOP_REPO_ROOT must be an absolute path",
            ));
        }
        return canonical_directory(path, "NWR_DESKTOP_REPO_ROOT");
    }

    let development_root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..");
    if development_root
        .join("scripts")
        .join("run_nwr_desktop_api.py")
        .is_file()
    {
        return canonical_directory(development_root, "development repository");
    }

    Err(RuntimeError::message(
        "could not locate scripts/run_nwr_desktop_api.py; set NWR_DESKTOP_REPO_ROOT for development",
    ))
}

#[cfg(not(debug_assertions))]
fn resolve_repo_root(app: &AppHandle<Wry>, mode: AppMode) -> RuntimeResult<PathBuf> {
    validate_bundled_resource_root(app.path().resource_dir()?, mode)
}

#[cfg(any(not(debug_assertions), test))]
fn required_resource_files(mode: AppMode) -> &'static [&'static str] {
    match mode {
        AppMode::Dynasty => &DYNASTY_RESOURCE_FILES,
        AppMode::Redraft => &REDRAFT_RESOURCE_FILES,
    }
}

#[cfg(any(not(debug_assertions), test))]
fn validate_bundled_resource_root(resource_root: PathBuf, mode: AppMode) -> RuntimeResult<PathBuf> {
    let resource_root = canonical_directory(resource_root, "bundled resource directory")?;
    for relative in required_resource_files(mode) {
        if !resource_root.join(relative).is_file() {
            return Err(RuntimeError::message(format!(
                "bundled {} resources are incomplete: missing {relative}",
                mode.as_str()
            )));
        }
    }
    for relative in FORBIDDEN_RESOURCE_TREES {
        if resource_root.join(relative).exists() {
            return Err(RuntimeError::message(format!(
                "bundled {} resources contain forbidden tree {relative}",
                mode.as_str()
            )));
        }
    }
    if mode.as_str() == AppMode::Dynasty.as_str()
        && REDRAFT_RESOURCE_FILES
            .iter()
            .any(|relative| resource_root.join(relative).exists())
    {
        return Err(RuntimeError::message(
            "bundled Dynasty resources contain Redraft-only evidence",
        ));
    }
    if mode.as_str() == AppMode::Redraft.as_str()
        && DYNASTY_RESOURCE_FILES
            .iter()
            .any(|relative| resource_root.join(relative).exists())
    {
        return Err(RuntimeError::message(
            "bundled Redraft resources contain Dynasty-only evidence",
        ));
    }
    Ok(resource_root)
}

#[cfg(debug_assertions)]
fn resolve_backend_program(
    _app: &AppHandle<Wry>,
    repo_root: &Path,
) -> RuntimeResult<BackendProgram> {
    Ok(BackendProgram {
        executable: resolve_python(repo_root)?,
        script: Some(resolve_api_script(repo_root)?),
        kind: "development-source-python",
    })
}

#[cfg(not(debug_assertions))]
fn resolve_backend_program(
    app: &AppHandle<Wry>,
    _repo_root: &Path,
) -> RuntimeResult<BackendProgram> {
    let current_exe = env::current_exe()?.canonicalize().map_err(|error| {
        RuntimeError::message(format!("failed to resolve app executable: {error}"))
    })?;
    let executable_root = current_exe
        .parent()
        .ok_or_else(|| RuntimeError::message("app executable has no parent directory"))?
        .to_path_buf();
    let resource_root =
        canonical_directory(app.path().resource_dir()?, "bundled resource directory")?;

    let mut roots = vec![executable_root];
    if !roots.contains(&resource_root) {
        roots.push(resource_root);
    }
    for root in &roots {
        if let Some(executable) = validated_sidecar(root)? {
            return Ok(BackendProgram {
                executable,
                script: None,
                kind: "bundled-sidecar",
            });
        }
    }

    Err(RuntimeError::message(format!(
        "bundled sidecar {SIDECAR_RUNTIME_NAME} was not found beside the application"
    )))
}

#[cfg(not(debug_assertions))]
fn validated_sidecar(root: &Path) -> RuntimeResult<Option<PathBuf>> {
    let candidate = root.join(SIDECAR_RUNTIME_NAME);
    let metadata = match fs::symlink_metadata(&candidate) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == io::ErrorKind::NotFound => return Ok(None),
        Err(error) => {
            return Err(RuntimeError::message(format!(
                "failed to inspect bundled sidecar {}: {error}",
                candidate.display()
            )))
        }
    };
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return Err(RuntimeError::message(format!(
            "bundled sidecar is not a regular file: {}",
            candidate.display()
        )));
    }
    let resolved = candidate.canonicalize().map_err(|error| {
        RuntimeError::message(format!(
            "failed to resolve bundled sidecar {}: {error}",
            candidate.display()
        ))
    })?;
    if resolved.parent() != Some(root) {
        return Err(RuntimeError::message(format!(
            "bundled sidecar escaped its trusted directory: {}",
            resolved.display()
        )));
    }
    Ok(Some(resolved))
}

#[cfg(debug_assertions)]
fn resolve_api_script(repo_root: &Path) -> RuntimeResult<PathBuf> {
    let candidate = match env::var_os("NWR_DESKTOP_API_SCRIPT").filter(|value| !value.is_empty()) {
        Some(value) => {
            let value = PathBuf::from(value);
            if value.is_absolute() {
                value
            } else {
                repo_root.join(value)
            }
        }
        None => repo_root.join("scripts").join("run_nwr_desktop_api.py"),
    };
    if !candidate.is_file() {
        return Err(RuntimeError::message(format!(
            "desktop API launcher does not exist: {}",
            candidate.display()
        )));
    }
    candidate
        .canonicalize()
        .map_err(|error| RuntimeError::message(format!("failed to resolve API launcher: {error}")))
}

#[cfg(debug_assertions)]
fn resolve_python(repo_root: &Path) -> RuntimeResult<PathBuf> {
    if let Some(value) = env::var_os("NWR_DESKTOP_PYTHON").filter(|value| !value.is_empty()) {
        let configured = PathBuf::from(value);
        let candidate = if configured.is_absolute() {
            configured
        } else {
            repo_root.join(configured)
        };
        if candidate.is_file() {
            return candidate.canonicalize().map_err(RuntimeError::from);
        }
        return Err(RuntimeError::message(format!(
            "NWR_DESKTOP_PYTHON does not identify a file: {}",
            candidate.display()
        )));
    }

    #[cfg(windows)]
    let virtualenv_python = repo_root.join(".venv").join("Scripts").join("python.exe");
    #[cfg(not(windows))]
    let virtualenv_python = repo_root.join(".venv").join("bin").join("python3");
    if virtualenv_python.is_file() {
        return virtualenv_python.canonicalize().map_err(RuntimeError::from);
    }

    #[cfg(windows)]
    let executable_name = "python.exe";
    #[cfg(not(windows))]
    let executable_name = "python3";
    find_on_path(executable_name).ok_or_else(|| {
        RuntimeError::message(format!(
            "could not locate {executable_name}; set NWR_DESKTOP_PYTHON for development"
        ))
    })
}

#[cfg(debug_assertions)]
fn find_on_path(executable_name: &str) -> Option<PathBuf> {
    env::var_os("PATH")
        .into_iter()
        .flat_map(|value| env::split_paths(&value).collect::<Vec<_>>())
        .map(|directory| directory.join(executable_name))
        .find(|candidate| candidate.is_file())
        .and_then(|candidate| candidate.canonicalize().ok())
}

fn canonical_directory(path: PathBuf, label: &str) -> RuntimeResult<PathBuf> {
    if !path.is_dir() {
        return Err(RuntimeError::message(format!(
            "{label} is not a directory: {}",
            path.display()
        )));
    }
    path.canonicalize()
        .map_err(|error| RuntimeError::message(format!("failed to resolve {label}: {error}")))
}

fn capture_startup_report(
    stdout: ChildStdout,
    mut log: fs::File,
) -> mpsc::Receiver<Result<Vec<u8>, String>> {
    let (sender, receiver) = mpsc::channel();
    thread::spawn(move || {
        let mut reader = BufReader::new(stdout);
        match read_bounded_line(&mut reader, MAX_STARTUP_REPORT_BYTES) {
            Ok(line) => {
                if let Err(error) = log.write_all(&line).and_then(|_| log.flush()) {
                    let _ = sender.send(Err(format!(
                        "failed to record the desktop API startup report: {error}"
                    )));
                    return;
                }
                let _ = sender.send(Ok(line));
                let _ = io::copy(&mut reader, &mut log);
            }
            Err(error) => {
                let _ = sender.send(Err(format!(
                    "failed to read the desktop API startup report: {error}"
                )));
            }
        }
    });
    receiver
}

fn read_bounded_line<R: BufRead>(reader: &mut R, limit: usize) -> io::Result<Vec<u8>> {
    let mut line = Vec::new();
    loop {
        let available = reader.fill_buf()?;
        if available.is_empty() {
            return Err(io::Error::new(
                io::ErrorKind::UnexpectedEof,
                "startup report ended before a newline",
            ));
        }
        let take = available
            .iter()
            .position(|byte| *byte == b'\n')
            .map_or(available.len(), |index| index + 1);
        if line.len().saturating_add(take) > limit {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "startup report exceeded its byte limit",
            ));
        }
        let found_newline = available[take - 1] == b'\n';
        line.extend_from_slice(&available[..take]);
        reader.consume(take);
        if found_newline {
            return Ok(line);
        }
    }
}

fn receive_startup_report(
    backend: &mut GuardedChild,
    receiver: mpsc::Receiver<Result<Vec<u8>, String>>,
    mode: AppMode,
    requested_port: u16,
    deadline: Instant,
) -> RuntimeResult<StartupReport> {
    let remaining = remaining_until(deadline)?;
    let line = match receiver.recv_timeout(remaining) {
        Ok(Ok(line)) => line,
        Ok(Err(error)) => return Err(RuntimeError::message(error)),
        Err(mpsc::RecvTimeoutError::Timeout) => {
            return Err(RuntimeError::message(
                "desktop API did not announce its bound listener before the startup timeout",
            ))
        }
        Err(mpsc::RecvTimeoutError::Disconnected) => {
            return Err(RuntimeError::message(
                "desktop API startup-report pipe closed unexpectedly",
            ))
        }
    };
    if let Some(status) = backend.try_wait()? {
        return Err(RuntimeError::message(format!(
            "desktop API exited before its startup report was verified: {status}"
        )));
    }
    let report: StartupReport = serde_json::from_slice(&line)?;
    if report.protocol != STARTUP_PROTOCOL
        || report.host != LOOPBACK_HOST
        || report.mode != mode.as_str()
        || report.pid == 0
    {
        return Err(RuntimeError::message(
            "desktop API startup report did not match the launch contract",
        ));
    }
    if requested_port == 0 {
        if report.port < HIGH_EPHEMERAL_PORT_MIN {
            return Err(RuntimeError::message(
                "desktop API did not bind a high ephemeral loopback port",
            ));
        }
    } else if report.port != requested_port {
        return Err(RuntimeError::message(
            "desktop API bound a port other than the explicit development request",
        ));
    }
    Ok(report)
}

fn verify_listener_until(
    backend: &mut GuardedChild,
    port: u16,
    announced_pid: u32,
    expected_image: &Path,
    deadline: Instant,
) -> RuntimeResult<()> {
    loop {
        if let Some(status) = backend.try_wait()? {
            return Err(RuntimeError::message(format!(
                "desktop API exited before listener ownership was verified: {status}"
            )));
        }
        let error = match backend.verify_loopback_listener(port, announced_pid, expected_image) {
            Ok(()) => return Ok(()),
            Err(error) => error,
        };
        if Instant::now() >= deadline {
            return Err(RuntimeError::message(format!(
                "desktop API listener ownership could not be verified: {error}"
            )));
        }
        thread::sleep(Duration::from_millis(25));
    }
}

fn verify_startup_proof(
    backend: &mut GuardedChild,
    port: u16,
    startup_proof_key: &str,
    mode: AppMode,
    deadline: Instant,
) -> RuntimeResult<()> {
    if let Some(status) = backend.try_wait()? {
        return Err(RuntimeError::message(format!(
            "desktop API exited before startup proof verification: {status}"
        )));
    }
    let challenge = random_secret();
    let request = format!(
        "GET /startup-proof HTTP/1.1\r\nHost: {LOOPBACK_HOST}:{port}\r\nAccept: application/json\r\nX-NWR-Startup-Challenge: {challenge}\r\nConnection: close\r\n\r\n"
    );
    let response = loopback_http_request(port, &request, deadline)?;
    let body = response_body_200(&response)?;
    let envelope: StartupProofEnvelope = serde_json::from_slice(body)?;
    if envelope.contract_version != CONTRACT_VERSION
        || envelope.mode != mode.as_str()
        || envelope.data.status != "starting"
        || envelope.data.transport != "loopback"
        || !envelope.warnings.is_empty()
        || !envelope.errors.is_empty()
    {
        return Err(RuntimeError::message(
            "desktop API startup proof response did not match the launch contract",
        ));
    }

    let proof = decode_lower_hex_32(&envelope.data.startup_proof)?;
    let message = format!("{STARTUP_PROTOCOL}\n{}\n{port}\n{challenge}", mode.as_str());
    let mut mac = HmacSha256::new_from_slice(startup_proof_key.as_bytes())
        .map_err(|_| RuntimeError::message("desktop startup proof key was invalid"))?;
    mac.update(message.as_bytes());
    mac.verify_slice(&proof)
        .map_err(|_| RuntimeError::message("desktop API startup HMAC verification failed"))?;

    if let Some(status) = backend.try_wait()? {
        return Err(RuntimeError::message(format!(
            "desktop API exited after startup proof verification: {status}"
        )));
    }
    Ok(())
}

fn wait_for_health(
    backend: &mut GuardedChild,
    port: u16,
    announced_pid: u32,
    expected_image: &Path,
    token: &str,
    mode: AppMode,
    deadline: Instant,
) -> RuntimeResult<()> {
    loop {
        if let Some(status) = backend.try_wait()? {
            return Err(RuntimeError::message(format!(
                "desktop API exited before /healthz was ready: {status}"
            )));
        }

        let request = format!(
            "GET /healthz HTTP/1.1\r\nHost: {LOOPBACK_HOST}:{port}\r\nAccept: application/json\r\nX-NWR-Desktop-Token: {token}\r\nConnection: close\r\n\r\n"
        );
        let remaining = remaining_until(deadline)?;
        let io_timeout = remaining.min(Duration::from_millis(750));
        let address = SocketAddrV4::new(Ipv4Addr::LOCALHOST, port);
        if let Ok(mut stream) = TcpStream::connect_timeout(&address.into(), io_timeout) {
            let _ = stream.set_read_timeout(Some(io_timeout));
            let _ = stream.set_write_timeout(Some(io_timeout));

            // Establish the socket first, then verify its listening process before the
            // bearer crosses that same connection. A process that races a rebind cannot
            // inherit an already-established TCP connection.
            if backend
                .verify_loopback_listener(port, announced_pid, expected_image)
                .is_ok()
                && stream.write_all(request.as_bytes()).is_ok()
            {
                let mut response = Vec::with_capacity(1024);
                let read_result = (&mut stream)
                    .take(MAX_HTTP_RESPONSE_BYTES + 1)
                    .read_to_end(&mut response);
                if read_result.is_ok()
                    && response.len() as u64 <= MAX_HTTP_RESPONSE_BYTES
                    && health_response_matches(&response, mode)
                    && backend
                        .verify_loopback_listener(port, announced_pid, expected_image)
                        .is_ok()
                    && backend.try_wait()?.is_none()
                {
                    return Ok(());
                }
            }
        }

        if Instant::now() >= deadline {
            return Err(RuntimeError::message(format!(
                "desktop API did not become healthy on loopback port {port} before the startup timeout"
            )));
        }
        thread::sleep(Duration::from_millis(50));
    }
}

fn loopback_http_request(port: u16, request: &str, deadline: Instant) -> RuntimeResult<Vec<u8>> {
    let remaining = remaining_until(deadline)?;
    let io_timeout = remaining.min(Duration::from_millis(750));
    let address = SocketAddrV4::new(Ipv4Addr::LOCALHOST, port);
    let mut stream = TcpStream::connect_timeout(&address.into(), io_timeout)?;
    stream.set_read_timeout(Some(io_timeout))?;
    stream.set_write_timeout(Some(io_timeout))?;
    stream.write_all(request.as_bytes())?;

    let mut response = Vec::with_capacity(1024);
    (&mut stream)
        .take(MAX_HTTP_RESPONSE_BYTES + 1)
        .read_to_end(&mut response)?;
    if response.len() as u64 > MAX_HTTP_RESPONSE_BYTES {
        return Err(RuntimeError::message(
            "desktop API response exceeded its byte limit",
        ));
    }
    Ok(response)
}

fn response_body_200(response: &[u8]) -> RuntimeResult<&[u8]> {
    let Some(header_end) = response.windows(4).position(|window| window == b"\r\n\r\n") else {
        return Err(RuntimeError::message(
            "desktop API returned an invalid HTTP response",
        ));
    };
    let headers = &response[..header_end];
    if !(headers.starts_with(b"HTTP/1.1 200 ") || headers.starts_with(b"HTTP/1.0 200 ")) {
        return Err(RuntimeError::message(
            "desktop API returned a non-success HTTP response",
        ));
    }
    Ok(&response[(header_end + 4)..])
}

fn health_response_matches(response: &[u8], mode: AppMode) -> bool {
    let Ok(body) = response_body_200(response) else {
        return false;
    };
    let Ok(envelope) = serde_json::from_slice::<HealthEnvelope>(body) else {
        return false;
    };
    envelope.contract_version == CONTRACT_VERSION
        && envelope.mode == mode.as_str()
        && envelope.data.status == "ok"
        && envelope.data.transport == "loopback"
        && envelope.data.authenticated
        && envelope.warnings.is_empty()
        && envelope.errors.is_empty()
}

fn decode_lower_hex_32(value: &str) -> RuntimeResult<[u8; 32]> {
    let bytes = value.as_bytes();
    if bytes.len() != 64
        || !bytes
            .iter()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(byte))
    {
        return Err(RuntimeError::message(
            "desktop API startup proof was not strict lowercase hexadecimal",
        ));
    }
    let mut decoded = [0u8; 32];
    for (index, pair) in bytes.chunks_exact(2).enumerate() {
        decoded[index] = (hex_nibble(pair[0]) << 4) | hex_nibble(pair[1]);
    }
    Ok(decoded)
}

fn hex_nibble(value: u8) -> u8 {
    match value {
        b'0'..=b'9' => value - b'0',
        b'a'..=b'f' => value - b'a' + 10,
        _ => unreachable!("hex input is validated before conversion"),
    }
}

fn remaining_until(deadline: Instant) -> RuntimeResult<Duration> {
    deadline
        .checked_duration_since(Instant::now())
        .filter(|remaining| !remaining.is_zero())
        .ok_or_else(|| RuntimeError::message("desktop API startup timed out"))
}

fn append_file(path: &Path) -> RuntimeResult<fs::File> {
    OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(RuntimeError::from)
}

fn append_lifecycle(path: &Path, message: &str) {
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(path) {
        let _ = writeln!(file, "{} {message}", unix_time_ms());
    }
}

fn nonempty_env(name: &str) -> Option<String> {
    env::var(name).ok().filter(|value| !value.is_empty())
}

fn unix_time_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

type RuntimeResult<T> = Result<T, RuntimeError>;

#[derive(Debug)]
struct RuntimeError(String);

impl RuntimeError {
    fn message(message: impl Into<String>) -> Self {
        Self(message.into())
    }
}

impl fmt::Display for RuntimeError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl Error for RuntimeError {}

impl From<io::Error> for RuntimeError {
    fn from(error: io::Error) -> Self {
        Self(error.to_string())
    }
}

impl From<serde_json::Error> for RuntimeError {
    fn from(error: serde_json::Error) -> Self {
        Self(error.to_string())
    }
}

impl From<tauri::Error> for RuntimeError {
    fn from(error: tauri::Error) -> Self {
        Self(error.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::{
        decode_lower_hex_32, required_resource_files, validate_bundled_resource_root, AppMode,
        FORBIDDEN_RESOURCE_TREES,
    };
    use std::fs;
    use std::path::{Path, PathBuf};
    use uuid::Uuid;

    fn resource_fixture(mode: AppMode) -> PathBuf {
        let root = std::env::temp_dir().join(format!(
            "nwr-desktop-resource-test-{}",
            Uuid::new_v4().simple()
        ));
        fs::create_dir_all(&root).expect("create resource fixture");
        for relative in required_resource_files(mode) {
            let path = root.join(relative);
            fs::create_dir_all(path.parent().expect("resource parent"))
                .expect("create resource parent");
            fs::write(path, b"fixture").expect("write resource fixture");
        }
        root
    }

    fn remove_fixture(root: &Path) {
        fs::remove_dir_all(root).expect("remove resource fixture");
    }

    #[test]
    fn startup_proof_hex_is_strict_and_bounded() {
        assert!(decode_lower_hex_32(&"ab".repeat(32)).is_ok());
        assert!(decode_lower_hex_32(&"AB".repeat(32)).is_err());
        assert!(decode_lower_hex_32(&"ag".repeat(32)).is_err());
        assert!(decode_lower_hex_32(&"ab".repeat(31)).is_err());
    }

    #[test]
    fn bundled_resource_validation_is_mode_specific() {
        for mode in [AppMode::Dynasty, AppMode::Redraft] {
            let root = resource_fixture(mode);
            let result = validate_bundled_resource_root(root.clone(), mode);
            assert!(result.is_ok(), "{} fixture must validate", mode.as_str());

            let missing = root.join(required_resource_files(mode)[0]);
            fs::remove_file(&missing).expect("remove required fixture");
            let error = validate_bundled_resource_root(root.clone(), mode)
                .expect_err("missing resource must fail")
                .to_string();
            assert!(error.contains("missing"));
            remove_fixture(&root);
        }
    }

    #[test]
    fn bundled_resource_validation_rejects_forbidden_trees() {
        for mode in [AppMode::Dynasty, AppMode::Redraft] {
            for forbidden in FORBIDDEN_RESOURCE_TREES {
                let root = resource_fixture(mode);
                fs::create_dir_all(root.join(forbidden)).expect("create forbidden fixture");
                let error = validate_bundled_resource_root(root.clone(), mode)
                    .expect_err("forbidden resource tree must fail")
                    .to_string();
                assert!(error.contains(forbidden));
                remove_fixture(&root);
            }
        }
    }

    #[test]
    fn bundled_resource_validation_rejects_cross_mode_evidence() {
        for (mode, other) in [
            (AppMode::Dynasty, AppMode::Redraft),
            (AppMode::Redraft, AppMode::Dynasty),
        ] {
            let root = resource_fixture(mode);
            let cross_mode = root.join(required_resource_files(other)[0]);
            fs::create_dir_all(cross_mode.parent().expect("cross-mode parent"))
                .expect("create cross-mode parent");
            fs::write(cross_mode, b"fixture").expect("write cross-mode fixture");
            assert!(validate_bundled_resource_root(root.clone(), mode).is_err());
            remove_fixture(&root);
        }
    }
}
