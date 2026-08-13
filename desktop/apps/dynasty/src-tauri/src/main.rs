#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    nwr_desktop_runtime::run(
        tauri::generate_context!(),
        nwr_desktop_runtime::AppMode::Dynasty,
    );
}
