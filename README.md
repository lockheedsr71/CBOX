# CBOX — Secure CLI Toolkit for Windows

CBOX is a small, dependency-light command-line toolkit for Windows. It bundles two
interactive shells (a batch-based one and a Python refactor) plus a set of standalone
CLI tools for directory listing, ping, traceroute, and WHOIS lookups.

Everything runs locally. Tools only reach the network when you explicitly ask them to.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Project Layout](#project-layout)
- [Usage](#usage)
  - [CBOX shell (Python)](#cbox-shell-python)
  - [CBOX shell (Batch)](#cbox-shell-batch)
  - [cdir — directory lister](#cdir--directory-lister)
  - [cpi — ping tool](#cpi--ping-tool)
  - [cro — traceroute tool](#cro--traceroute-tool)
  - [cwho — whois tool](#cwho--whois-tool)
- [Building EXEs](#building-exes)
  - [maker.bat (interactive)](#makerbat-interactive)
  - [build.ps1 (parameterized)](#buildps1-parameterized)
- [cmd AutoRun integration](#cmd-autorun-integration)
- [Technical Notes](#technical-notes)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## Features

- **Two interactive shells** — `cbox.py` (Python, current) and `cbox.cmd` (batch, original).
- **Unix-style short commands** inside the shell: `ls`, `ps`, `kill`, `df`, `ip`, `pi`, `tr`, ...
- **Pass-through execution** — any command that isn't a CBOX command is handed to the system shell.
- **Rich table output** for directory listings, including hidden/system flags, owner, and
  permissions.
- **Color-coded ping** with latency grading and optional log files.
- **Traceroute with optional Geo-IP and ASN lookup** per hop.
- **WHOIS reports** for domains and IPs, optionally saved to a file.
- **EXE packaging helpers** based on PyInstaller, with optional icon and version metadata.
- **Zero-config AutoRun** option to start the shell in every new `cmd` window.

---

## Requirements

| Component | Requirement |
| --- | --- |
| `cbox.py` | Python 3.8+, standard library only |
| `cbox.cmd` | Windows, no Python needed |
| `cdir.py` | Python 3.8+, `rich`, optionally `pywin32` |
| `cpi.py` | Python 3.8+, `colorama` |
| `cro.py` | Python 3.8+, `colorama`, `requests` |
| `cwho.py` | Python 3.8+, `python-whois` |
| Build scripts | Windows PowerShell 5.1+, PyInstaller |

Install the Python dependencies once:

```powershell
python -m pip install rich pywin32 colorama requests python-whois
```

`pywin32` is optional — it only enables the owner column in `cdir.py`. Without it the
column shows `N/A`.

---

## Installation

Clone the repository and run directly. There is nothing to compile.

```powershell
git clone https://github.com/lockheedsr71/CBOX.git
cd CBOX
python cbox.py
```

For the batch shell, no install step is needed — just launch it:

```powershell
.\cbox.cmd
```

---

## Project Layout

```
CBOX/
├── cbox.py        # Interactive shell (Python refactor, v1.0.1)
├── cbox.cmd       # Interactive shell (batch, v1.0)
├── cdir.py        # Directory lister with rich table output
├── cpi.py         # Color-coded continuous ping
├── cro.py         # Traceroute with optional Geo-IP / ASN info
├── cwho.py        # WHOIS lookup and report
├── build.ps1      # PyInstaller build helper (currently targets tping.py)
├── reginit.reg    # Registry file to hook cbox.cmd into cmd AutoRun
├── exemaker/
│   ├── build.ps1      # PyInstaller helper (targets tping.py)
│   ├── buildtr.ps1   # PyInstaller helper (targets troute.py)
│   └── maker.bat     # Interactive builder with version metadata + icon
└── .gitignore
```

> Note: the `exemaker\*.ps1` helpers and the top-level `build.ps1` still reference the
> earlier script names `tping.py` and `troute.py`, which are now `cpi.py` and `cro.py`.
> Pass `-Name` / update the script path, or copy the file to the expected name first.

---

## Usage

### CBOX shell (Python)

```powershell
python cbox.py
```

```
#######################################################
CBOX v1.0.1  Secure CLI for Windows
Advanced Command-Line Interface (Python Refactor)
FOXNET Group | https://software.foxnet.ir
#######################################################
Type '?' for command list. Use 'exit' to quit.
```

The prompt shows the current working directory on every iteration:

```
 C:\Users\you\projects
CBOX > ls
```

Available commands:

| Command | Description |
| --- | --- |
| `ls [path]` | List directory contents |
| `pi <host>` | Ping a host |
| `tr <host>` | Trace route to a host |
| `ip` / `ipa` | Network configuration (`ipconfig`) |
| `df` | Free space on all drives |
| `task` / `ps` | Running process list |
| `kill <PID>` | Force-kill a process by PID |
| `who` | Current user |
| `ver` | OS version |
| `cl` | Clear screen |
| `?` | Show command list |
| `exit` / `quit` | Leave the shell |
| *anything else* | Passed through to the system shell |

`Ctrl+C` asks for confirmation before exiting. While a command is running, `Ctrl+C`
terminates the child process instead of the shell.

### CBOX shell (Batch)

```powershell
.\cbox.cmd
```

The batch shell covers the same short commands plus a few extras that only exist here:
`netstat`, `arp`, `nslookup`, `cp`, `mv`, `del`, `mkd`, `rmd`, `endtask`, `info`, and
`explore`. Each recognized command prints a small help card describing it before running.

### cdir — directory lister

```powershell
python cdir.py                        # list current directory
python cdir.py "C:\Windows"           # list an explicit path
python cdir.py -H                      # include hidden entries
python cdir.py -s                      # include system entries
python cdir.py -a                      # add Owner and Permissions columns
python cdir.py --sort size             # name | size | date
```

`--sort size` and `--sort date` sort largest/newest first. Sizes are shown in KB and
directories display as `DIR`.

### cpi — ping tool

```powershell
python cpi.py google.com               # ping until interrupted
python cpi.py 8.8.8.8 -n 10            # 10 requests
python cpi.py 8.8.8.8 -i 0.5           # 500 ms interval
python cpi.py 8.8.8.8 -o ping.log      # append results to a log
```

Latency is color-graded: green under 50 ms, yellow under 150 ms, orange under 300 ms,
red at or above 300 ms. Timeouts print as `Request Timed Out!`.

### cro — traceroute tool

```powershell
python cro.py 8.8.8.8                  # standard traceroute
python cro.py 8.8.8.8 -m 15            # limit to 15 hops
python cro.py 8.8.8.8 -g               # add country / city per hop
python cro.py 8.8.8.8 -a               # add ISP and AS number per hop
python cro.py 8.8.8.8 -g -a -o route.log
```

Per-hop lookups use the `ip-api.com` HTTP endpoint and only happen when `-g` or `-a` is
passed. Private ranges (`10.x`, `172.16-31.x`, `192.168.x`, `127.x`) are labeled
`[Internal Network]` without any network call.

### cwho — whois tool

```powershell
python cwho.py google.com
python cwho.py 8.8.8.8 -o whois.txt
```

Reports domain name, registrar, WHOIS server, creation and expiration dates, name
servers, status, emails, and country.

---

## Building EXEs

### maker.bat (interactive)

```powershell
cd exemaker
.\maker.bat
```

Prompts for the script name, version, company, and description, generates a
`version.txt` for Windows file properties, then runs PyInstaller. If `icon.ico` is
present in the working directory it is embedded along with `icon.png`. Output lands in
`dist\<scriptname>.exe`.

### build.ps1 (parameterized)

```powershell
.\build.ps1 -Name cpi -OneFile             # single console exe
.\build.ps1 -Name cpi -OneFile -Windowed   # no console window
.\build.ps1 -Name cpi -OneFile -Clean      # remove build/, dist/, spec first
```

The script installs PyInstaller automatically if it is missing, then runs
`python -m PyInstaller --onefile --name <Name> <script>.py`.

---

## cmd AutoRun integration

`reginit.reg` sets the Command Processor `AutoRun` value so `cbox.cmd` starts inside
every new `cmd` window:

```
[HKEY_CURRENT_USER\Software\Microsoft\Command Processor]
"AutoRun"="D:\\MyPrograms\\cmd\\cbox.cmd"
```

Apply it:

```powershell
reg import .\reginit.reg
```

Edit the path in the file first so it points at your actual location. To roll back:

```powershell
reg delete "HKCU\Software\Microsoft\Command Processor" /v AutoRun /f
```

---

## Technical Notes

- **Pass-through by design.** Both shells run unrecognized input through the system
  shell. That is convenient, but it also means any string the shell accepts is a valid
  command. Treat `cbox.cmd` and `cbox.py` as interactive tools, not as a sandbox.
- **Shell injection surface.** `cbox.py` interpolates arguments into shell command
  strings (`f'dir "{path}"'`). Paths containing shell metacharacters can break the
  command. Use the dedicated Python tools (`cdir.py`, `cpi.py`) when you need to pass
  untrusted input.
- **Process lifecycle.** `cbox.py` keeps a handle to the running child process so
  `Ctrl+C` terminates it rather than leaking an orphan.
- **Color output.** `cbox.py` and `cbox.cmd` emit raw ANSI escapes. `cdir.py` uses Rich
  markup, and the other tools use Colorama. Redirecting to a file will include the
  escape sequences.
- **Deprecated APIs.** `df` in both shells and the `ver` command rely on `wmic` and
  `systeminfo`, which are being phased out of recent Windows releases. Prefer
  `Get-Volume` in PowerShell if these stop working.
- **Registry hooks are persistent.** `reginit.reg` modifies the current user's Command
  Processor settings. Remove it with the `reg delete` command above if you don't want it.

---

## Disclaimer

For educational and administrative use on systems you own or are authorized to test.
Geo-IP data comes from the free `ip-api.com` endpoint; WHOIS data comes from the public
WHOIS servers. Respect local law and the terms of those services.

---

## License

Released under the MIT License.