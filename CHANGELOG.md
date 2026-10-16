# Changelog

All notable changes to CBOX are recorded here.

## [1.2.0]

Correctness, performance and a batch of new tools. See the `Fixed`, `Changed`
and `Added` sections below.

### Fixed

- `cbox.py`: the `netdetail` alias pointed at `net_info.py`, a file that never
  existed, so the command always failed. It now resolves to `netinf.py`.
- `cbox.py`: removed the `cnetw` alias, which had no implementation behind it.
- `cbox.py`: bundled tools were invoked as bare command names and therefore
  only worked when a compiled EXE happened to be on `PATH`. Resolution now goes
  through `cbox_core.tools`, which prefers `dist/<tool>.exe`, falls back to an
  installed EXE, and finally runs `python <tool>.py`. A fresh clone works with
  no build step.
- `cbox.py`: an installed EXE on `PATH` no longer shadows the source next to
  `cbox.py`. An older `cpi.EXE` in a directory on `PATH` was silently running
  stale code.
- `cbox.py`: `cd "C:\Program Files"` failed with `WinError 123` because the
  quotes reached `os.chdir`. Path quoting is now stripped.
- `cbox.py`: `df` was broken on Windows 11 24H2, where `wmic` no longer ships.
  It is now computed in-process with `GetLogicalDrives` + `shutil.disk_usage`.
- `cbox.py`: when a passthrough alias resolved but its target program was
  missing, the error said "not a recognized CBOX or System command". It now
  names the missing program.
- `netinf.py`: referenced `Colors.RED` in its error path without ever defining
  it, so any failure raised `AttributeError` instead of printing the error.
- `netinf.py`: `ipconfig` output was decoded with a hardcoded `cp1252`. Decoding
  now tries `utf-8`, then `cp1252`, then `latin-1`, and never raises.
- `netinf.py`: the field regexes hardcoded the exact number of padding dots in
  the `ipconfig` label column, which varies with label width and Windows
  version. They now match the dot run.
- `netinf.py`: a regex used `\s`, which matches newlines, so an absent field
  captured the value of the *next* row. Restricted to horizontal whitespace.
- `netinf.py`: adapter blocks were split with a regex that merged the preamble
  into the first adapter and produced names like `ETHERNET ADAPTER ETHERNET:`.
- `netinf.py`: `adapter.split("DNS Servers")[1]` could raise `IndexError` on an
  adapter with no DNS block.
- `ntstat.py`: `conn.laddr.ip` raised `AttributeError` on unbound UDP sockets.
- `nscn.py`: `args = parser.parse_class = parser.parse_args()` assigned a
  function to a stray attribute.
- `cdir.py`: the folder/file emoji crashed the whole listing with
  `UnicodeEncodeError` on a console running a legacy code page.
- `ntpmon.py`: the up/down arrows in the I/O readout raised the same
  `UnicodeEncodeError` on a cp1252 console.
- `csweep.py`: passing `-p` made the probe timeout resolve to `None`, so the
  sockets became blocking. A port sweep that took 0.5 s took **21 s**.
- `cbox_core.lineedit`: `sys.stdin.fileno()` was called without a guard.
  `hasattr(stdin, "fileno")` is not sufficient — pytest's capture object and
  stream wrappers expose the attribute but raise from it.
- `cbox_core.lineedit`: tab completion treated a trailing space as "complete the
  first token", so `cdir <Tab>` offered command names instead of paths.
- `cbox_core.config`: `alias name = cmd` parsed as the command `= cmd`, because
  the `=` was only stripped for settings, not aliases.
- `cbox_core.config`: a UTF-8 BOM turned the first setting into `﻿theme`,
  so `~/.cboxrc` written by Notepad or PowerShell 5.1 failed to load.
- Script mode: a BOM made the first comment line look like a command, and
  echoing a UTF-8 script on a cp1252 console raised `UnicodeEncodeError`.
- Every `except:` that swallowed `KeyboardInterrupt`, `SystemExit` and
  `AccessDenied` was narrowed to `except Exception`, or to the specific
  exceptions that can actually occur.

### Changed

- Geo-IP lookups moved from `http://ip-api.com` to `https://ipwho.is`. The old
  endpoint is HTTP-only on its free tier (HTTPS answers 403) and rate-limits to
  45 requests/minute, which `ntpmon` exceeded immediately by querying once per
  connection per refresh tick. Lookups are cached, failures are cached too, and
  an unreachable endpoint degrades to a placeholder.
- `is_private_ip` uses `ipaddress` instead of regexes, so link-local
  (`169.254/16`), CGNAT (`100.64/10`), multicast and IPv6 unique-local
  addresses are now classified correctly.
- `nscn.py` checks for Npcap and Administrator privileges before starting and
  exits with an actionable message instead of a scapy traceback.
- `nscn.py` port and subnet scans now run concurrently (128 probes by default).
  The serial version spent 0.15 s × 254 waiting on ARP even when every host
  answered immediately.
- `csweep.py` caps concurrency at 1024 and the target at 8192 addresses, to
  avoid saturating a link or tripping a firewall's SYN-flood threshold.
- `csweep.py` resolves PTR records off the probe path, with a timeout.
  Inlining them made a 32-probe sweep take 21 s instead of 0.5 s.
- Missing optional dependencies (`rich`, `scapy`, `python-whois`) now produce a
  one-line install hint instead of an `ImportError` traceback.
- Colour definitions, tool resolution, IP helpers, dependency handling and JSON
  output moved into a shared `cbox_core` package; the per-file copies are gone.
- ANSI enabling moved from the `os.system('')` side-effect hack to
  `cbox_core.colors.init_color()`, which respects `NO_COLOR` and skips the hack
  where terminals handle ANSI natively.
- `ntpmon.py` reports disk I/O as a delta per interval. `psutil.io_counters()`
  is a lifetime total, so the footer was re-printing the same cumulative number
  instead of a rate.
- `cpi.py` reports distinct messages for timeout, unreachable host and missing
  `ping` executable, and validates `--interval` / `--count`.
- `cro.py` strips ANSI codes before writing the log file.
- `cwho.py` no longer crashes on `None` WHOIS fields.
- `build.ps1` still targeted `tping.py`, a file that was removed long ago, so
  every build failed. It is now a thin wrapper around the Python builder.

### Added

**Shell**

- Line editing with persistent history (Up/Down), tab completion for command
  names and paths, and `Ctrl+A/E/K/U/W/L`. Implemented on `msvcrt` because
  Python's `readline` does not exist on Windows. Falls back to plain `input()`
  when stdin is not a terminal.
- `cd -` returns to the previous directory and toggles back and forth.
- `~/.cboxrc` for aliases, theme, history size, banner, colour and completion
  toggles. Unparseable lines are reported with their line number and skipped.
- Destructive-command guard: `del`, `erase`, `rmdir`, `rd`, `format`,
  `diskpart` and `kill` ask for confirmation when the target is a drive root or
  your home directory. Disable with `confirm_destructive = no`.
- Script mode: `cbox -f script.cbox` runs one command per line; `cbox -c CMD`
  runs a single command.
- `--no-config` and `--rc PATH` to control which configuration file is read.

**Tools**

- `cport.py` — listening ports with the owning process, flagging anything bound
  to every interface.
- `csweep.py` — parallel host and port discovery with configurable workers and
  timeouts, subnet/range/single-host targets, and optional reverse DNS.
- `chash.py` — file and directory hashing (md5/sha1/sha256/sha512) in a single
  pass per file, plus `--check` verification mode.
- `cwlan.py` — wireless interface status with signal, channel and link rates,
  matching both English and Farsi `netsh` labels.
- `--json` output on `cdir`, `ntstat`, `cport`, `csweep`, `cwlan` and `chash`.
  Errors are reported inside the document so a consumer parsing stdout does not
  have to tell "failed" from "empty".
- `ntpmon.py` gained a resources panel with host CPU/RAM/disk usage and a
  per-process table of PID, name, RSS and thread count.
- `nscn.py` gained `--json`, `--workers` and `--timeout`.

**Build and docs**

- `requirements.txt`, `pyproject.toml` and an MIT `LICENSE`.
- `tests/` with 156 pytest cases and `.github/workflows/ci.yml` running the
  suite on Windows and Linux, byte-compiling every tool, and building all EXEs
  on tag.
- `2exe.py` is the single builder; `compilit.py` was a 90% duplicate and has
  been removed. The tool list and version come from `cbox_core`.
- Generated version-resource files are written under `build/` instead of
  polluting the repository root.
- `install-autorun.cmd` writes the real `cbox.cmd` path into the registry and
  can uninstall it again. `reginit.reg` is now a documented template; the
  hardcoded `D:\MyPrograms\cmd\cbox.cmd` path is gone.
- `CHANGELOG.md`.

### Known limitations

- `nscn.py` port scanning and ARP discovery still require Administrator and
  Npcap on Windows; scapy cannot send raw packets without a packet driver.
- `csweep.py` host sweeps shell out to `ping.exe`, so a `/24` costs 256 process
  launches and takes a few seconds. Port sweeps use raw sockets and are far
  faster. A batched raw-ICMP path via scapy was tried and removed: it needs
  Npcap, returns nothing without it, and emits driver errors on cleanup.
- Geo-IP data comes from a third-party API and needs outbound network access.
  Results are cached in-process only, so each run starts cold.
- `cwlan.py` depends on `netsh`, which Windows no longer exposes on some
  builds. It reports that rather than showing an empty table.
- CPU and GPU temperature are not available: `psutil.sensors_temperatures` does
  not exist on Windows. `ntpmon.py` shows CPU load, not temperature.
- History and tab completion are unavailable when stdin is not a terminal.