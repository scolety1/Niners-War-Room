use std::io;
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, ExitStatus};
use std::thread;
use std::time::{Duration, Instant};

#[cfg(windows)]
use std::ffi::c_void;
#[cfg(windows)]
use std::mem::size_of;
#[cfg(windows)]
use std::os::windows::ffi::OsStringExt;
#[cfg(windows)]
use std::os::windows::io::AsRawHandle;
#[cfg(windows)]
use std::ptr;
#[cfg(windows)]
use windows_sys::Win32::Foundation::{CloseHandle, ERROR_INSUFFICIENT_BUFFER, HANDLE, NO_ERROR};
#[cfg(windows)]
use windows_sys::Win32::NetworkManagement::IpHelper::{
    GetExtendedTcpTable, MIB_TCPROW_OWNER_PID, TCP_TABLE_OWNER_PID_LISTENER,
};
#[cfg(windows)]
use windows_sys::Win32::System::JobObjects::{
    AssignProcessToJobObject, CreateJobObjectW, IsProcessInJob, JobObjectExtendedLimitInformation,
    SetInformationJobObject, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
};
#[cfg(windows)]
use windows_sys::Win32::System::Threading::{
    OpenProcess, QueryFullProcessImageNameW, PROCESS_QUERY_LIMITED_INFORMATION,
};

pub(crate) struct GuardedChild {
    child: Child,
    #[cfg(windows)]
    job: Option<JobObject>,
    containment: &'static str,
    containment_warning: Option<String>,
}

impl GuardedChild {
    pub(crate) fn new(child: Child) -> Self {
        #[cfg(windows)]
        {
            match JobObject::assign(&child) {
                Ok(job) => Self {
                    child,
                    job: Some(job),
                    containment: "windows-job-object",
                    containment_warning: None,
                },
                Err(error) => Self {
                    child,
                    job: None,
                    containment: "exact-child-fallback",
                    containment_warning: Some(format!(
                        "Windows Job Object assignment failed; exact-child fallback is active: {error}"
                    )),
                },
            }
        }

        #[cfg(not(windows))]
        {
            Self {
                child,
                containment: "exact-child-fallback",
                containment_warning: Some(
                    "Windows Job Objects are unavailable on this development platform".to_owned(),
                ),
            }
        }
    }

    pub(crate) fn id(&self) -> u32 {
        self.child.id()
    }

    pub(crate) fn containment(&self) -> &'static str {
        self.containment
    }

    pub(crate) fn containment_warning(&self) -> Option<&str> {
        self.containment_warning.as_deref()
    }

    pub(crate) fn take_stdin(&mut self) -> Option<ChildStdin> {
        self.child.stdin.take()
    }

    pub(crate) fn take_stdout(&mut self) -> Option<ChildStdout> {
        self.child.stdout.take()
    }

    pub(crate) fn try_wait(&mut self) -> io::Result<Option<ExitStatus>> {
        self.child.try_wait()
    }

    #[cfg(windows)]
    pub(crate) fn verify_loopback_listener(
        &self,
        port: u16,
        announced_pid: u32,
        expected_image: &Path,
    ) -> io::Result<()> {
        let actual_pid = loopback_listener_pid(port)?;
        if actual_pid != announced_pid {
            return Err(io::Error::new(
                io::ErrorKind::PermissionDenied,
                "announced API PID does not own the loopback listener",
            ));
        }

        let process = ProcessHandle::open(actual_pid)?;
        let Some(job) = &self.job else {
            return Err(io::Error::new(
                io::ErrorKind::PermissionDenied,
                "Windows Job Object containment is required to verify the API listener",
            ));
        };
        job.verify_member(&process)?;

        let actual_image = process.image_path()?.canonicalize()?;
        let expected_image = expected_image.canonicalize()?;
        if !paths_equal_windows(&actual_image, &expected_image) {
            return Err(io::Error::new(
                io::ErrorKind::PermissionDenied,
                "API listener image does not match the launched backend",
            ));
        }
        Ok(())
    }

    #[cfg(not(windows))]
    pub(crate) fn verify_loopback_listener(
        &self,
        _port: u16,
        announced_pid: u32,
        _expected_image: &Path,
    ) -> io::Result<()> {
        if announced_pid != self.id() {
            return Err(io::Error::new(
                io::ErrorKind::PermissionDenied,
                "announced API PID does not match the exact child",
            ));
        }
        Ok(())
    }

    pub(crate) fn shutdown(&mut self) -> io::Result<()> {
        if self.child.try_wait()?.is_some() {
            return Ok(());
        }

        #[cfg(windows)]
        if let Some(job) = self.job.take() {
            // Closing a kill-on-close job terminates only the API child and its descendants.
            drop(job);
            if self.wait_for_exit(Duration::from_secs(2))? {
                return Ok(());
            }
        }

        // This is intentionally Child::kill, never taskkill or a name-based process sweep.
        if self.child.try_wait()?.is_none() {
            self.child.kill()?;
        }
        let _ = self.child.wait()?;
        Ok(())
    }

    fn wait_for_exit(&mut self, timeout: Duration) -> io::Result<bool> {
        let deadline = Instant::now() + timeout;
        loop {
            if self.child.try_wait()?.is_some() {
                return Ok(true);
            }
            if Instant::now() >= deadline {
                return Ok(false);
            }
            thread::sleep(Duration::from_millis(25));
        }
    }
}

impl Drop for GuardedChild {
    fn drop(&mut self) {
        let _ = self.shutdown();
    }
}

#[cfg(windows)]
struct JobObject(HANDLE);

#[cfg(windows)]
impl JobObject {
    fn assign(child: &Child) -> io::Result<Self> {
        // SAFETY: null security attributes/name request an unnamed job with default ACLs.
        let handle = unsafe { CreateJobObjectW(ptr::null(), ptr::null()) };
        if handle.is_null() {
            return Err(io::Error::last_os_error());
        }
        let job = Self(handle);

        let mut limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION::default();
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        // SAFETY: `limits` is the exact structure required for this information class and
        // remains alive for the call. The job handle is owned by `job`.
        let configured = unsafe {
            SetInformationJobObject(
                job.0,
                JobObjectExtendedLimitInformation,
                (&limits as *const JOBOBJECT_EXTENDED_LIMIT_INFORMATION).cast::<c_void>(),
                size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as u32,
            )
        };
        if configured == 0 {
            return Err(io::Error::last_os_error());
        }

        // SAFETY: std owns a valid process handle for the live child. Assignment does not
        // transfer ownership of either handle.
        let assigned =
            unsafe { AssignProcessToJobObject(job.0, child.as_raw_handle().cast::<c_void>()) };
        if assigned == 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(job)
    }

    fn verify_member(&self, process: &ProcessHandle) -> io::Result<()> {
        let mut result = 0;
        // SAFETY: both handles are live and `result` points to writable BOOL storage.
        let checked = unsafe { IsProcessInJob(process.0, self.0, &mut result) };
        if checked == 0 {
            return Err(io::Error::last_os_error());
        }
        if result == 0 {
            return Err(io::Error::new(
                io::ErrorKind::PermissionDenied,
                "API listener is outside the launcher Job Object",
            ));
        }
        Ok(())
    }
}

#[cfg(windows)]
unsafe impl Send for JobObject {}

#[cfg(windows)]
impl Drop for JobObject {
    fn drop(&mut self) {
        // SAFETY: this type owns the non-null job handle and closes it exactly once.
        unsafe {
            CloseHandle(self.0);
        }
    }
}

#[cfg(windows)]
struct ProcessHandle(HANDLE);

#[cfg(windows)]
impl ProcessHandle {
    fn open(pid: u32) -> io::Result<Self> {
        // SAFETY: OpenProcess returns an owned handle or null.
        let handle = unsafe { OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid) };
        if handle.is_null() {
            Err(io::Error::last_os_error())
        } else {
            Ok(Self(handle))
        }
    }

    fn image_path(&self) -> io::Result<PathBuf> {
        let mut buffer = vec![0u16; 32_768];
        let mut size = buffer.len() as u32;
        // SAFETY: the buffer is writable for `size` UTF-16 code units and the handle is live.
        let queried =
            unsafe { QueryFullProcessImageNameW(self.0, 0, buffer.as_mut_ptr(), &mut size) };
        if queried == 0 {
            return Err(io::Error::last_os_error());
        }
        buffer.truncate(size as usize);
        Ok(PathBuf::from(std::ffi::OsString::from_wide(&buffer)))
    }
}

#[cfg(windows)]
impl Drop for ProcessHandle {
    fn drop(&mut self) {
        // SAFETY: this type owns the non-null process handle and closes it exactly once.
        unsafe {
            CloseHandle(self.0);
        }
    }
}

#[cfg(windows)]
fn loopback_listener_pid(port: u16) -> io::Result<u32> {
    const AF_INET: u32 = 2;
    let mut bytes = 0u32;
    // SAFETY: a null first buffer asks Windows for the required table size.
    let status = unsafe {
        GetExtendedTcpTable(
            ptr::null_mut(),
            &mut bytes,
            0,
            AF_INET,
            TCP_TABLE_OWNER_PID_LISTENER,
            0,
        )
    };
    if status != ERROR_INSUFFICIENT_BUFFER {
        return Err(io::Error::from_raw_os_error(status as i32));
    }

    let mut buffer = vec![0u8; bytes as usize];
    // SAFETY: Windows writes at most `bytes` bytes to the allocated buffer.
    let status = unsafe {
        GetExtendedTcpTable(
            buffer.as_mut_ptr().cast::<c_void>(),
            &mut bytes,
            0,
            AF_INET,
            TCP_TABLE_OWNER_PID_LISTENER,
            0,
        )
    };
    if status != NO_ERROR {
        return Err(io::Error::from_raw_os_error(status as i32));
    }
    if buffer.len() < size_of::<u32>() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "Windows returned an invalid TCP listener table",
        ));
    }

    // SAFETY: the length check above covers the unaligned DWORD read.
    let count = unsafe { ptr::read_unaligned(buffer.as_ptr().cast::<u32>()) } as usize;
    let row_size = size_of::<MIB_TCPROW_OWNER_PID>();
    let table_size = size_of::<u32>()
        .checked_add(count.checked_mul(row_size).ok_or_else(|| {
            io::Error::new(io::ErrorKind::InvalidData, "TCP listener table overflow")
        })?)
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "TCP listener table overflow"))?;
    if table_size > bytes as usize || table_size > buffer.len() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "Windows returned a truncated TCP listener table",
        ));
    }

    // MIB_TCPROW_OWNER_PID stores the IPv4 address and port in network byte order.
    let loopback = u32::from_ne_bytes([127, 0, 0, 1]);
    let base = size_of::<u32>();
    let mut owner = None;
    for index in 0..count {
        // SAFETY: `table_size` was checked and unaligned rows are read by value.
        let row = unsafe {
            ptr::read_unaligned(
                buffer
                    .as_ptr()
                    .add(base + index * row_size)
                    .cast::<MIB_TCPROW_OWNER_PID>(),
            )
        };
        if row.dwLocalAddr == loopback && u16::from_be(row.dwLocalPort as u16) == port {
            if owner.replace(row.dwOwningPid).is_some() {
                return Err(io::Error::new(
                    io::ErrorKind::PermissionDenied,
                    "multiple owners reported for the API listener",
                ));
            }
        }
    }
    owner.ok_or_else(|| {
        io::Error::new(
            io::ErrorKind::NotFound,
            "loopback API listener owner was not found",
        )
    })
}

#[cfg(windows)]
fn paths_equal_windows(left: &Path, right: &Path) -> bool {
    left.as_os_str()
        .to_string_lossy()
        .eq_ignore_ascii_case(&right.as_os_str().to_string_lossy())
}
