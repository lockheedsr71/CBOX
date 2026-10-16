# CBOX — Secure CLI Toolkit for Windows

**[English](#english) · [فارسی](#فارسی)**

CBOX is a small, dependency-light command-line toolkit for Windows. It bundles two
interactive shells (a batch-based one and a Python refactor) plus eight standalone
CLI tools: directory listing, ping, traceroute, WHOIS, network diagnostics, a
socket table, a per-process network monitor, and a LAN/port scanner.

Everything runs locally. Tools only reach the network when you explicitly ask them to.

---

## English

### Table of Contents

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
- [Complete Command Reference](#complete-command-reference)
- [Building EXEs](#building-exes)
- [cmd AutoRun integration](#cmd-autorun-integration)
- [Development](#development)
- [Technical Notes](#technical-notes)
- [Disclaimer](#disclaimer)
- [License](#license)

---

### Features

- **Two interactive shells** — `cbox.py` (Python, current) and `cbox.cmd` (batch, original).
- **Unix-style short commands** inside the shell: `ls`, `ps`, `kill`, `df`, `ip`, `pi`, `tr`, ...
- **Line editing** — persistent history on Up/Down, Tab completion for commands and paths,
  and `Ctrl+A/E/K/U/W`. Built on `msvcrt`, since `readline` does not exist on Windows.
- **User configuration** via `~/.cboxrc`: aliases, theme, history size, and a safety switch.
- **Pass-through execution** — any command that isn't a CBOX command is handed to the system shell.
- **Destructive-command guard** — `del`/`rmdir`/`kill` and friends ask before running.
- **Script mode** — `cbox -f script.cbox` runs a file of shell commands.
- **Rich table output** for directory listings, including hidden/system flags, owner, and
  permissions.
- **Color-coded ping** with latency grading, side-by-side target comparison and custom TTL/size.
- **Traceroute with optional Geo-IP and ASN lookup** per hop.
- **WHOIS reports** for domains and IPs, optionally saved to a file.
- **Advanced network diagnostics** — per-adapter IPv4/IPv6/DNS/DHCP breakdown.
- **Socket table** with the owning process name for every connection.
- **Listening-port report** flagging anything bound to every interface.
- **Per-process network monitor** dashboard with live Geo-IP, disk I/O and top CPU/RAM.
- **LAN and port scanner** — parallel ARP discovery and TCP port sweeps.
- **Parallel host/port sweep** with configurable concurrency and timeouts.
- **File hashing and checksum verification** (md5/sha1/sha256/sha512).
- **Wireless status** with signal, channel and link rate.
- **`--json` output** on every listing tool, for piping to `jq` or PowerShell.
- **EXE packaging** driven by a single builder script and one version source.
- **Optional AutoRun** integration with a supported installer and uninstaller.

---

### Requirements

| Component | Requirement |
| --- | --- |
| `cbox.py` | Python 3.8+, standard library only |
| `cbox.cmd` | Windows, no Python needed |
| `cdir.py` | Python 3.8+, `rich`, optionally `pywin32` |
| `cpi.py` | Python 3.8+, `colorama` |
| `cro.py` | Python 3.8+, `colorama`, `requests` |
| `cwho.py` | Python 3.8+, `python-whois` |
| `cport.py` | Python 3.8+, `rich`, `psutil` |
| `csweep.py` | Python 3.8+, `rich`, `psutil` |
| `chash.py` | Python 3.8+, `rich` |
| `cwlan.py` | Python 3.8+, `rich`, Windows `netsh` |
| `netinf.py` | Python 3.8+, standard library only |
| `ntstat.py` | Python 3.8+, `rich`, `psutil` |
| `ntpmon.py` | Python 3.8+, `rich`, `psutil`, `requests` |
| `nscn.py` | Python 3.8+, `rich`, `psutil`, `requests`, `scapy`, Npcap, Administrator |
| Build scripts | Windows PowerShell 5.1+, PyInstaller |

Install the Python dependencies once:

```powershell
python -m pip install -r requirements.txt
```

Optional extras:

- `pywin32` — only enables the owner column in `cdir.py`. Without it the column
  shows `N/A`.
- `scapy` — required by `nscn.py` only. On Windows it additionally needs
  [Npcap](https://npcap.com) and an elevated shell. `nscn.py` checks for both
  up front and explains what is missing instead of raising a traceback.

Every tool degrades gracefully: if an optional package is absent you get a
one-line install hint rather than an `ImportError`.

---

### Installation

Clone the repository and run directly. There is nothing to compile.

```powershell
git clone https://github.com/lockheedsr71/CBOX.git
cd CBOX
python -m pip install -r requirements.txt
python cbox.py
```

The shell finds each tool in this order: a freshly built `dist/<tool>.exe`, an
installed EXE on `PATH`, then `python <tool>.py` next to `cbox.py`. A fresh
clone therefore works with no build step.

For the batch shell, no install step is needed — just launch it:

```powershell
.\cbox.cmd
```

---

### Project Layout

```
CBOX/
├── cbox.py                # Interactive shell (Python, current)
├── cbox.cmd               # Interactive shell (batch, original)
├── cbox_core/             # Shared helpers used by every tool
│   ├── __init__.py        #   __version__ and the TOOLS registry
│   ├── colors.py          #   ANSI palette + console enablement
│   ├── config.py          #   ~/.cboxrc parsing
│   ├── console.py         #   optional-dependency handling, safe glyphs
│   ├── jsonout.py         #   shared --json output
│   ├── lineedit.py        #   history + tab completion (no readline)
│   ├── netutil.py         #   IP classification + cached Geo-IP lookup
│   └── tools.py           #   tool discovery (EXE → PATH → script)
├── cdir.py                # Directory lister with rich table output
├── cpi.py                 # Color-coded continuous ping
├── cro.py                 # Traceroute with optional Geo-IP / ASN info
├── cwho.py                # WHOIS lookup and report
├── cport.py               # Listening ports and owning process
├── csweep.py              # Parallel host / port discovery
├── chash.py               # File hashing and checksum verification
├── cwlan.py               # Wireless interface status
├── netinf.py              # Deep network diagnostics (IPv4/IPv6/DNS/DHCP)
├── ntstat.py              # Socket table with process owner
├── ntpmon.py              # Per-process network monitor dashboard
├── nscn.py                # LAN discovery + TCP port scanner
├── 2exe.py                # The single PyInstaller builder for all tools
├── build.ps1              # Thin PowerShell wrapper around 2exe.py
├── install-autorun.cmd    # Optional AutoRun installer / uninstaller
├── reginit.reg            # AutoRun registry template (documented)
├── tests/                 # pytest suite
├── pyproject.toml         # Packaging, pytest and ruff config
├── requirements.txt
├── CHANGELOG.md
├── LICENSE
├── exemaker/              # Legacy single-tool builders
├── .github/workflows/     # CI: test on Windows+Linux, build EXEs on tag
└── .gitignore
```

---

### Usage

#### CBOX shell (Python)

```powershell
python cbox.py
python cbox.py -c "cpi 8.8.8.8 -n 3"     # run one command, then exit
python cbox.py -f backup.cbox            # run a script of commands, then exit
python cbox.py --no-config               # ignore ~/.cboxrc this session
```

```
#######################################################
CBOX v1.2.0  Secure CLI for Windows
Advanced Command-Line Interface (Dynamic Logic)
FOXNET Group | https://software.foxnet.ir
#######################################################
Type '?' for command list. Use 'exit' to quit.
```

The prompt shows the current working directory on every iteration:

```
 C:\Users\you\projects
CBOX > ls
```

`cd` expands `~` and `%VAR%`. `?`, `help`, `-h` and `--help` all print the
command list.

**Line editing**

Python's `readline` module does not exist on Windows, so CBOX implements its
own editor on `msvcrt`. Nothing extra to install.

| Key | Action |
| --- | --- |
| `Up` / `Down` | Walk through history (persisted to `~/.cbox_history`) |
| `Tab` | Complete a command name, or a path after `ls` / `cdir` / `chash` |
| `Tab`, `Tab` | With several matches, cycle through them |
| `Left` / `Right` / `Home` / `End` | Move within the line |
| `Ctrl+A` / `Ctrl+E` | Start / end of line |
| `Ctrl+U` / `Ctrl+K` | Delete to start / end of line |
| `Ctrl+W` | Delete the previous word |
| `Ctrl+L` | Clear the screen |
| `Ctrl+C` | Ask to exit |
| `Ctrl+D` | Exit |

When stdin is not a terminal (piped input, CI) the editor falls back to plain
`input()` — no history or completion, but nothing breaks.

**Configuration — `~/.cboxrc`**

```
# CBOX shell configuration

theme = dark                # dark | light | plain
banner = yes
color = yes
history = yes
history_size = 500
completion = yes
confirm_destructive = yes

# Aliases extend or override the built-in command table.
alias lg = cdir -a --sort size
alias net = cwho
alias purge = del /q
```

A missing file is fine. Unparseable lines are reported with their line number
and skipped, so one typo does not stop the shell from starting. The file is
read as `utf-8-sig`, so a BOM from Notepad is harmless.

**Destructive-command guard**

`del`, `erase`, `rmdir`, `rd`, `format`, `diskpart` and `kill` ask for
confirmation before running. The guard fires when the command targets a drive
root or your home directory, and `confirm_destructive = no` in `~/.cboxrc`
turns it off.

```
CBOX > del C:\
Refusing to run a destructive command:
  del C:\
Run it anyway? [y/N]: n
Cancelled.
```

**Script mode**

`cbox -f script.cbox` runs one command per line. Blank lines and `#` comments
are skipped, `exit` stops the script, and every line goes through the same
dispatcher as interactive input.

```
# check-connectivity.cbox
cpi 8.8.8.8 -n 4
cro 8.8.8.8 -m 8 -g
cport --json
exit
```

```powershell
python cbox.py -f check-connectivity.cbox
```

#### CBOX shell (Batch)

```powershell
.\cbox.cmd
```

The batch shell covers the same short commands plus a few extras that only exist there:
`netstat`, `arp`, `nslookup`, `cp`, `mv`, `del`, `mkd`, `rmd`, `endtask`, `info`, and
`explore`. Each recognized command prints a small help card describing it before running.

#### cdir — directory lister

```powershell
python cdir.py                        # list current directory
python cdir.py "C:\Windows"           # list an explicit path
python cdir.py -H                      # include hidden entries
python cdir.py -s                      # include system entries
python cdir.py -a                      # add Owner and Permissions columns
python cdir.py --sort size             # name | size | date
```

#### cpi — ping tool

```powershell
python cpi.py google.com               # ping until interrupted
python cpi.py 8.8.8.8 -n 10            # 10 requests
python cpi.py 8.8.8.8 -i 0.5           # 500 ms interval
python cpi.py 8.8.8.8 -o ping.log      # append results to a log
```

Latency is color-graded: green under 50 ms, yellow under 150 ms, orange under 300 ms,
red at or above 300 ms. Timeouts print as `Request Timed Out!`.

#### cro — traceroute tool

```powershell
python cro.py 8.8.8.8                  # standard traceroute
python cro.py 8.8.8.8 -m 15            # limit to 15 hops
python cro.py 8.8.8.8 -g               # add country / city per hop
python cro.py 8.8.8.8 -a               # add ISP and AS number per hop
python cro.py 8.8.8.8 -g -a -o route.log
```

Per-hop lookups use the `ipwho.is` endpoint over HTTPS (no API key) and only
happen when `-g` or `-a` is passed. Results are cached for the process
lifetime. Private and reserved ranges (`10.x`, `172.16-31.x`, `192.168.x`,
`127.x`, `169.254.x`, `100.64-127.x`, IPv6 ULA/link-local) are labeled
`[Internal Network]` without any network call. When the endpoint is unreachable
the hop shows `[geo unavailable]` instead of failing the trace.

#### cwho — whois tool

```powershell
python cwho.py google.com
python cwho.py 8.8.8.8 -o whois.txt
```

Reports domain name, registrar, WHOIS server, creation and expiration dates, name
servers, status, emails, and country. Absent fields render as `N/A`.

#### netinf — network diagnostics

```powershell
python netinf.py
```

Prints a per-adapter breakdown of physical address, IPv4, IPv6, link-local IPv6,
subnet mask, default gateway, DHCP server and status, and DNS servers. Virtual
adapters with no address are skipped. `ipconfig /all` is decoded with a UTF-8 /
cp1252 / latin-1 fallback chain, so a localised console does not garble or
abort the report.

#### ntstat — socket table

```powershell
python ntstat.py                          # every socket
python ntstat.py -p tcp -s ESTABLISHED    # only established TCP
python ntstat.py -dst 8.8.8.8 -v          # matching destination, verbose
```

| Flag | Meaning |
| --- | --- |
| `-p`, `--proto` | `tcp` or `udp` |
| `-s`, `--status` | Exact status match, e.g. `LISTEN`, `CLOSE_WAIT` |
| `-src`, `--source` | Substring match against the local address |
| `-dst`, `--dest` | Substring match against the remote address |
| `-v`, `--verbose` | Add family and socket handle columns |

The owning process name is resolved per row; rows you lack permission to see
show `N/A` rather than being dropped. Unbound UDP sockets render as `-`.
Running as Administrator is needed to see other users' sockets.

#### ntpmon — per-process network monitor

```powershell
python ntpmon.py chrome                 # monitor by process name
python ntpmon.py 4321 -i 0.25           # monitor by PID, refresh 4x/second
```

A live dashboard of every remote endpoint the target process holds, with
status, connection duration, Geo-IP location and cumulative bytes sent/received.

- **Press `ESC` to exit.** `Ctrl+C` is deliberately suppressed so a refresh
  tick cannot tear the dashboard down mid-frame.
- Without Administrator, only your own processes are visible.

#### nscn — LAN and port scanner

```powershell
python nscn.py -s                          # sweep the current /24 via ARP
python nscn.py -t 192.168.1.5 -p 80-443    # scan a port range
python nscn.py -t 192.168.1.1 -p 445       # check a single port
```

The subnet sweep is interactive — press Enter to accept the detected subnet.
Each discovered host gets an IP, MAC, TTL-derived OS guess, RTT and OUI vendor
lookup (via `api.macvendors.com`, cached, best-effort).

> **Requires Administrator and [Npcap](https://npcap.com) on Windows.** `nscn.py`
> verifies both before starting and exits with an explanation rather than a
> scapy traceback. Probes run concurrently (128 by default, `-w` to change).
> Only scan networks you are authorized to test.

#### cport — listening ports

```powershell
python cport.py                      # wildcard and loopback binds
python cport.py --all                # include binds to a specific address
python cport.py -P 22,80,443         # only these ports
python cport.py -P 8000-8100         # only this range
python cport.py -p udp               # UDP instead of TCP
python cport.py --json | jq .        # machine-readable
```

Wildcard binds (`0.0.0.0`, `::`) are highlighted in red: they are reachable
from outside the machine. Every row carries the owning process name. Running as
Administrator is needed to see other users' sockets.

#### csweep — parallel host and port discovery

```powershell
python csweep                                    # this machine's /24
python csweep 192.168.1.0/24                     # explicit subnet
python csweep 192.168.1.10-50                    # host range
python csweep 192.168.1.0/24 -p 22,80,443        # ports across the subnet
python csweep -t 10.0.0.5 -p 1-1024 --timeout 0.2
python csweep 192.168.1.0/24 --json
```

| Flag | Default | Meaning |
| --- | --- | --- |
| `-w`, `--workers` | 128 | Concurrent probes |
| `--timeout` | 0.4s | Per-probe timeout |
| `--no-resolve` | off | Skip reverse-DNS lookups |

Concurrency is capped at 1024 and the target is limited to 8192 addresses, to
avoid saturating a link or tripping a firewall's SYN-flood threshold.

Host sweeps shell out to `ping.exe`, so a `/24` costs 256 process launches and
takes a few seconds. Port sweeps use raw sockets and are far faster. A batched
raw-ICMP path via scapy was tried and removed — it needs Npcap, returns nothing
without it, and emits driver errors on cleanup.

#### chash — hashing and verification

```powershell
python chash.py README.md                          # sha256
python chash.py README.md -a md5 -a sha1           # several algorithms
python chash.py . -r -a sha256                     # whole tree
python chash.py --check "README.md <digest>"       # verify one file
python chash.py --check "*.txt <digest>" --json    # machine-readable
```

Each file is read once and every requested algorithm is fed from that single
pass. In `--check` mode the algorithm is inferred from the digest length.
Without `--check`, a path with no files is reported rather than silently
producing an empty table.

#### cwlan — wireless status

```powershell
python cwlan.py
python cwlan.py --json
```

Shows interface name, SSID, connection state, signal percentage, channel and
receive/transmit link rates, with authentication and encryption below.

`netsh wlan show interfaces` is localised, so this tool matches labels in both
English and Farsi, and keys off the untranslated MAC line to find interface
blocks. If the output cannot be recognised at all it says so and prints the raw
text rather than showing an empty table.

---

### JSON output

Every listing tool accepts `--json` and writes a single JSON document to
stdout, with no ANSI escapes:

```powershell
python cport.py --json | jq '.ports[] | select(.exposure=="all")'
python csweep 192.168.1.0/24 --json | ConvertFrom-Json | Select-Object -Expand hosts
python ntstat.py -s ESTABLISHED --json > conns.json
```

Available on `cdir`, `ntstat`, `cport`, `csweep`, `cwlan` and `chash`.
Errors are reported inside the document on stdout rather than as a crash, so a
consumer parsing the stream does not have to tell "failed" from "empty".

---

### Complete Command Reference

#### `cbox.py` — interactive shell commands

| Command | Syntax | Description |
| --- | --- | --- |
| `ls` | `ls [path]` | Lists a directory via `dir`. Defaults to the current directory. |
| `cd` | `cd [path]` | Changes directory. Expands `~`, `%VAR%` and quotes. Defaults to your home. |
| `cd -` | `cd -` | Returns to the previous directory. Toggles back and forth. |
| `cd..` / `cd\` | `cd..` | One level up, or the drive root. |
| `pi` | `pi <host>` | Pings a host. |
| `tr` | `tr <host>` | Traces the route to a host via `tracert -d`. |
| `ip` | `ip` | Shows network configuration (`ipconfig`). |
| `ipa` | `ipa` | Shows the full configuration (`ipconfig /all`). |
| `df` | `df` / `dirfree` | Free/total per drive, colour-graded, computed in-process. |
| `task` | `task` | Lists running processes via `tasklist`. |
| `ps` | `ps` | Same as `task`. |
| `kill` | `kill <PID>` | Force-kills a process by numeric PID. Asks first. |
| `who` | `who` | Prints the current user (`whoami`). |
| `ver` | `ver` | Prints the OS version. |
| `cl` | `cl` | Clears the screen. |
| `cdir` | `cdir [flags] [path]` | Directory lister. |
| `cpi` | `cpi <target...>` | Colour-coded ping. |
| `cro` | `cro <host> [flags]` | Traceroute with Geo-IP/ASN. |
| `cwho` | `cwho <domain>` | WHOIS lookup. |
| `cport` | `cport [flags]` | Listening ports and owning process. |
| `csweep` | `csweep [subnet] [flags]` | Parallel host/port discovery. |
| `chash` | `chash <path...> [flags]` | Hashing and checksum verification. |
| `cwlan` | `cwlan` | Wireless interface status. |
| `netdetail` | `netdetail` | Deep network info (runs `netinf.py`). |
| `ntstat` | `ntstat [flags]` | Socket table with process owner. |
| `ntpmon` | `ntpmon <name\|pid>` | Per-process network monitor dashboard. |
| `nscn` | `nscn [flags]` | LAN / port scanner. |
| `?` | `?`, `help`, `-h`, `--help` | Prints the command list. |
| `exit` / `quit` | `exit` | Leaves the shell. Case-insensitive. |

`df` is implemented in Python rather than shelling out to `wmic logicaldisk`,
which no longer ships with Windows 11 24H2.

Bundled tools accept the same flags they do standalone, and are forwarded
without going through `cmd.exe` — quoted arguments stay intact:

```
CBOX > cro 8.8.8.8 -g -a
CBOX > cpi 8.8.8.8 1.1.1.1
CBOX > cdir -a --sort size "C:\Program Files"
```

**Keyboard behavior**

| Key | Action |
| --- | --- |
| `Ctrl+C` at the prompt | Asks `Exit CBOX? (y/N)`. `y` exits, anything else continues. |
| `Ctrl+C` while a command runs | Terminates the child process, keeps the shell alive. |
| `Ctrl+D` at the prompt | Exits cleanly (end of input). |

**Pass-through rule** — anything not in the table above is executed as a raw Windows
command line. Exit code `9009` (command not found) prints a hint pointing at `?`.

---

#### `cbox.cmd` — interactive shell commands

| Command | Syntax | Description |
| --- | --- | --- |
| `cl` | `cl` | Clears the screen. |
| `who` | `who` | Prints the current user. |
| `ver` | `ver` | Prints the CBOX version and OS version. |
| `info` | `info` | Full `systeminfo` output. |
| `netstat` | `netstat` | Shows active network connections. |
| `arp` | `arp` | Shows the ARP cache (`arp -a`). |
| `nslookup` | `nslookup` | Prompts for a host, then resolves it. |
| `task` | `task` | Lists running processes. |
| `ps` | `ps` | Same as `task`. |
| `kill` | `kill <PID>` | Kills a process by numeric PID (no `/F`). |
| `endtask` | `endtask` | Prompts for a process name, kills by image name (`taskkill /IM <name> /F`). |
| `dirfree` | `dirfree` | Free space on all drives. |
| `df` | `df` | Free space on all drives (alternate form). |
| `ls` | `ls` | Lists the current directory. |
| `ls <path>` | `ls <path>` | Lists an explicit path. |
| `pi` | `pi <host> [options]` | Pings a host; extra tokens are forwarded to `ping`, so `-t`, `-n 4`, `-l 1024` all work. |
| `tr` | `tr <host>` | Traces the route without DNS resolution (`tracert -d`). |
| `cp` | `cp <src> <dst>` | Copies a file. Both paths are quoted. |
| `mv` | `mv <src> <dst>` | Moves or renames a file. |
| `del` | `del <file>` | Deletes a file. |
| `mkd` | `mkd <folder>` | Creates a directory. |
| `rmd` | `rmd <dir> [/s]` | Removes a directory. Add `/s` for non-empty directories. |
| `ip` | `ip` | Network configuration. |
| `ipa` | `ipa` | Network configuration (alternate form). |
| `explore` | `explore` | Prompts for a folder path and lists it. |
| `?` | `?` | Full help screen. |
| `exit` / `quit` | `exit` | Leaves the shell. |

**Behavior notes**

- Each recognized command prints a mini help card (`Command`, `Description`) before running.
- Arguments are quoted for the file commands (`cp`, `mv`, `del`, `mkd`, `rmd`), so paths
  with spaces work.
- `nslookup`, `endtask`, and `explore` prompt interactively for their argument.
- Anything not in the table is echoed to the console and executed by `cmd` as-is.

---

#### `cdir.py` — directory lister

```
usage: cdir.py [-h] [-H] [-s] [-a] [--sort {name,size,date}] [path ...]
```

| Option | Short | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `--hidden` | `-H` | flag | off | Include entries with the hidden attribute. |
| `--system` | `-s` | flag | off | Include entries with the system attribute. |
| `--all` | `-a` | flag | off | Add `Owner` and `Permissions` columns. |
| `--sort` | — | choice | `name` | Sort key: `name`, `size`, or `date`. |
| `path` | — | positional | `.` | Target directory. Accepts multiple tokens; they are joined, so quoted paths with spaces work. |
| `--help` | `-h` | flag | — | Show the help screen. |

| Sort value | Behavior |
| --- | --- |
| `name` | Case-insensitive alphabetical, ascending. |
| `size` | Largest first; directories count as 0. |
| `date` | Most recently modified first. |

**Output columns**

| Column | Notes |
| --- | --- |
| `Attr` | Three characters: `H` hidden, `S` system, `R` read-only. `-` when not set. |
| `Name` | Folder or file name with a 📁 / 📄 marker. Folders are bold blue. |
| `Size` | KB with thousands separator, or `DIR` for folders. |
| `Last Modified` | `YYYY-MM-DD HH:MM`. |
| `Owner` | Only with `-a`. `DOMAIN\user` via `pywin32`, otherwise `N/A`. |
| `Permissions` | Only with `-a`. `stat.filemode()` output, e.g. `-rw-rw-rw-`. |

**Examples**

```powershell
python cdir.py                                  # current directory, name order
python cdir.py "C:\Program Files"               # explicit path
python cdir.py . -H -s                          # include hidden and system entries
python cdir.py -a                               # with owner and permissions
python cdir.py --sort size -a                   # largest first, with owner
python cdir.py --sort date                      # newest first
python cdir.py D:\backups                       # unquoted single-token path
```

---

#### `cpi.py` — ping tool

```
usage: cpi.py [-h] [-n COUNT] [-i INTERVAL] [-o OUTPUT] [target]
```

| Option | Short | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `target` | — | positional | none | IP address or domain. If omitted, prints help and exits with code 1. |
| `--count` | `-n` | integer | infinite | Number of echo requests. |
| `--interval` | `-i` | float | `1.0` | Seconds to wait between requests. |
| `--output` | `-o` | string | none | Log file path. Results are **appended**, not overwritten. |
| `--help` | `-h` | flag | — | Show the help screen. |

**Output columns**

```
Row | Date       | Time     | Target         | Latency  | TTL
```

**Latency color grading**

| Latency | Color |
| --- | --- |
| under 50 ms | green |
| under 150 ms | yellow |
| under 300 ms | orange |
| 300 ms and above | red |
| no reply | red, `Request Timed Out!` |

Under the hood each iteration runs a single-packet ping (`ping -n 1` on Windows,
`ping -c 1` elsewhere) and parses `time[=<]Nms` and `TTL=` with regular expressions.
Each ping has a 5-second timeout. `Ctrl+C` exits cleanly.

**Examples**

```powershell
python cpi.py google.com                       # continuous
python cpi.py 8.8.8.8 -n 20                    # exactly 20 requests
python cpi.py 8.8.8.8 -i 0.25                  # 4 pings per second
python cpi.py google.com -n 100 -o logs\ping.log
```

---

#### `cro.py` — traceroute tool

```
usage: cro.py [-h] [-m MAX_HOPS] [-g] [-a] [-o OUTPUT] [target]
```

| Option | Short | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `target` | — | positional | none | IP address or domain. If omitted, prints help and exits with code 1. |
| `--max-hops` | `-m` | integer | `20` | Maximum number of hops to trace. |
| `--geo` | `-g` | flag | off | Show country and city per hop. |
| `--asn` | `-a` | flag | off | Show ISP and AS number per hop. |
| `--output` | `-o` | string | none | Log file path. Results are **appended**. |
| `--help` | `-h` | flag | — | Show the help screen. |

**Under the hood**

| Platform | Command |
| --- | --- |
| Windows | `tracert -d -h <max_hops> <target>` |
| Linux / macOS | `traceroute -n -m <max_hops> <target>` |

**Per-hop line coloring**

| Hop condition | Color |
| --- | --- |
| `*` (no response) | red |
| Responded | green |
| Private IP (`10.x`, `172.16-31.x`, `192.168.x`, `127.x`) | labeled `[Internal Network]`, no lookup |
| Lookup timed out | labeled `[Lookup Timeout]` |

Geo and ASN data come from `ip-api.com` and are only requested when `-g` or `-a` is
set. Each hop has a 2-second timeout.

**Examples**

```powershell
python cro.py 8.8.8.8                          # plain, 20 hops
python cro.py google.com -m 30                 # deeper trace
python cro.py 8.8.8.8 -g                       # country and city
python cro.py 8.8.8.8 -a                       # ISP and AS number
python cro.py 8.8.8.8 -g -a -o logs\trace.log
```

---

#### `cwho.py` — whois tool

```
usage: cwho.py [-h] [-o OUTPUT] target
```

| Option | Short | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `target` | — | positional | **required** | Domain name or IP address. |
| `--output` | `-o` | string | none | Report file path. Appends with a separator line. |
| `--help` | `-h` | flag | — | Show the help screen. |

**Reported fields**

`Domain Name`, `Registrar`, `Whois Server`, `Creation Date`, `Expiration Date`,
`Name Servers`, `Status`, `Emails`, `Country`.

Field labels are yellow, values are white. List values (name servers, status, emails)
are joined with commas. Errors are printed in red and do not stop the tool.

**Examples**

```powershell
python cwho.py google.com
python cwho.py whois.arin.net
python cwho.py 8.8.8.8 -o logs\whois.txt
```

---

### Building EXEs

All build logic lives in one script, `2exe.py`. The tool list and version come
from `cbox_core`, so there is no hand-maintained file list to keep in sync.

#### 2exe.py (recommended)

```powershell
python 2exe.py                          # build every tool into dist\
python 2exe.py cpi cro                  # build only the named tools
python 2exe.py --no-metadata            # skip the Windows version resource
python 2exe.py --windowed               # no console window
python 2exe.py --no-confirm             # never prompt (used by CI)
```

Output lands in `dist\<tool>.exe`. Intermediate files and generated version
resources go to `build\`, never to the repository root.

#### build.ps1 (wrapper)

```powershell
.\build.ps1                              # build everything
.\build.ps1 -Name cro                     # build one tool
.\build.ps1 -Name cro -Windowed           # no console window
.\build.ps1 -Clean                        # wipe build\ and dist\ first
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `-Name` | string[] | all tools | Tool name(s) to build. |
| `-Windowed` | switch | off | Build without a console window. |
| `-Clean` | switch | off | Delete `build\` and `dist\` before building. |
| `-NoMetadata` | switch | off | Skip the version-info resource. |

#### exemaker\ (legacy)

`exemaker\maker.bat`, `exemaker\build.ps1` and `exemaker\buildtr.ps1` are the
original single-tool builders. They still reference the retired script names
`tping.py` and `troute.py`; use `2exe.py` instead.

---

### cmd AutoRun integration

`install-autorun.cmd` registers `cbox.cmd` as the Command Processor `AutoRun`
value, so a new `cmd.exe` window opens directly into CBOX:

```powershell
.\install-autorun.cmd              # register
.\install-autorun.cmd /uninstall   # remove and restore a normal prompt
```

It writes the real absolute path for you, shows the current value first, and
asks for confirmation. Uninstalling **deletes** the value rather than blanking
it — an empty `AutoRun` is still executed by `cmd.exe` and would open a second
console.

`reginit.reg` is kept as a documented template if you prefer `reg import`. Edit
the path before applying.

> This affects **every** `cmd.exe` window opened under the account, including
> ones launched by other programs. It is off by default and entirely optional.

---

### Development

```powershell
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest                        # 80 tests, no network required
python -m compileall -q .               # byte-compile every tool
```

`tests/` covers IP classification, geo-lookup caching, tool resolution, the
shell's alias table and dispatch, and the parsers of each tool. Every test is
offline — network calls are monkeypatched.

CI (`.github/workflows/ci.yml`) runs the suite on Windows and Linux, byte-compiles
every tool, and on a `v*` tag builds all EXEs and uploads them as artifacts.

---

### Technical Notes

- **Pass-through by design.** Both shells run unrecognized input through the system
  shell. That is convenient, but it also means any string the shell accepts is a valid
  command. Treat `cbox.cmd` and `cbox.py` as interactive tools, not as a sandbox.
- **Shell injection surface.** `cbox.py` runs passthrough input through `cmd.exe`, and
  the short aliases interpolate arguments into a command string. Paths containing
  shell metacharacters can therefore break the command. Bundled CBOX tools
  (`cdir`, `cpi`, `cro`, `cwho`, `netdetail`, `ntstat`, `ntpmon`, `nscn`) are launched
  with `shell=False`, so their arguments are never re-parsed. Prefer them when passing
  anything you do not control.
- **Process lifecycle.** `cbox.py` keeps a handle to the running child process so
  `Ctrl+C` terminates it rather than leaking an orphan.
- **Colour output.** `cbox.py` and `cbox.cmd` emit raw ANSI escapes. `cdir.py` uses Rich
  markup, and the other tools use Colorama. Set `NO_COLOR=1` to suppress colours.
  `cro.py` strips escapes before writing its log file.
- **Console encoding.** Legacy consoles (cp437/cp1252) cannot encode the folder/file
  glyphs; they degrade to `[D]` / `--` instead of raising `UnicodeEncodeError`.
  `ipconfig` output is decoded through a UTF-8 → cp1252 → latin-1 fallback chain.
- **Geo-IP caching is in-process only.** There is no on-disk cache, so every run
  starts cold. Failures are cached for 60 s so an unreachable endpoint cannot become a
  request storm.
- **Deprecated APIs.** `df` in both shells and the `ver` command rely on `wmic` and
  `systeminfo`, which are being phased out of recent Windows releases. Prefer
  `Get-Volume` in PowerShell if these stop working.
- **Privileges.** `nscn.py` needs Administrator plus Npcap for raw sockets;
  `ntstat.py` and `ntpmon.py` only see other users' sockets when elevated.
- **Registry hooks are persistent.** `install-autorun.cmd` modifies the current user's
  Command Processor settings. Remove it with the `/uninstall` switch.

---

### Disclaimer

For educational and administrative use on systems you own or are authorized to test.
Geo-IP data comes from the free `ipwho.is` and `api.macvendors.com` endpoints; WHOIS
data comes from the public WHOIS servers. Respect local law and the terms of those
services. Only scan networks you are authorized to test.

---

### License

Released under the MIT License. See [LICENSE](LICENSE).

---
---

# فارسی

CBOX یک جعبه‌ابزار خط فرمان سبک و کم‌وابستگی برای ویندوز است. شامل دو پوسته تعاملی
(یکی مبتنی بر batch و یکی بازنویسی‌شده با پایتون) به‌همراه هشت ابزار مستقل برای
نمایش محتوای پوشه، ping، traceroute، استعلام WHOIS، تشخیص شبکه، جدول سوکت‌ها،
مانیتور شبکهٔ هر پروسه و اسکن LAN/پورت.

همه‌چیز به‌صورت محلی اجرا می‌شود و ابزارها تنها زمانی به شبکه متصل می‌شوند که صراحتاً
از آن‌ها بخواهید.

### فهرست مطالب

- [ویژگی‌ها](#ویژگی‌ها-1)
- [پیش‌نیازها](#پیش‌نیازها-1)
- [نصب](#نصب-1)
- [ساختار پروژه](#ساختار-پروژه)
- [راهنمای استفاده](#راهنمای-استفاده)
- [مرجع کامل دستورات](#مرجع-کامل-دستورات)
- [ساخت فایل EXE](#ساخت-فایل-exe)
- [اتصال خودکار به cmd](#اتصال-خودکار-به-cmd)
- [توسعه](#توسعه)
- [نکات فنی](#نکات-فنی)
- [سلب مسئولیت](#سلب-مسئولیت)
- [مجوز](#مجوز-1)

---

### ویژگی‌ها

- **دو پوسته تعاملی** — `cbox.py` (پایتون، نسخه فعلی) و `cbox.cmd` (batch، نسخه اصلی).
- **دستورات کوتاه به سبک یونیکس** — `ls`، `ps`، `kill`، `df`، `ip`، `pi`، `tr` و ...
- **ویرایش خط** — تاریخچهٔ دائمی با کلیدهای بالا/پایین، تکمیل با Tab برای دستورات و مسیرها،
  و `Ctrl+A/E/K/U/W`. پیاده‌سازی‌شده روی `msvcrt` چون `readline` روی ویندوز وجود ندارد.
- **پیکربندی کاربر** با `~/.cboxrc`: نام مستعار، تم، اندازهٔ تاریخچه و کلید ایمنی.
- **اجرای عبوری** — هر دستوری که مربوط به CBOX نباشد مستقیماً به شل سیستم سپرده می‌شود.
- **محافظ عملیات خطرناک** — `del`/`rmdir`/`kill` و مشابه، پیش از اجرا تأیید می‌گیرند.
- **حالت اسکریپت** — `cbox -f script.cbox` یک فایل از دستورات را اجرا می‌کند.
- **خروجی جدولی غنی (Rich)** برای لیست کردن پوشه‌ها، شامل پرچم‌های hidden/system،
  مالک فایل و مجوزها.
- **Ping رنگ‌بندی‌شده** با درجه‌بندی تأخیر، مقایسه هم‌زمان دو مقصد و تنظیم TTL/اندازه بسته.
- **Traceroute با قابلیت جست‌وجوی اختیاری Geo-IP و ASN** برای هر hop.
- **گزارش WHOIS** برای دامنه و IP، با امکان ذخیره در فایل.
- **تشخیص عمیق شبکه** — گزارش per-adapter از IPv4/IPv6/DNS/DHCP.
- **جدول سوکت‌ها** به همراه نام پروسه مالک هر اتصال.
- **گزارش پورت‌های listening** با برجسته‌سازی مواردی که روی همهٔ اینترفیس‌ها باز هستند.
- **داشبورد مانیتور شبکه هر پروسه** با Geo-IP زنده، دیسک I/O و Top CPU/RAM.
- **اسکنر LAN و پورت** — کشف ARP موازی و اسکن TCP.
- **اسکن موازی میزبان/پورت** با کنترل تعداد worker و timeout.
- **هش فایل و تأیید چک‌سام** (md5/sha1/sha256/sha512).
- **وضعیت وایرلس** با سیگنال، کانال و نرخ لینک.
- **خروجی `--json`** روی همهٔ ابزارهای فهرست‌کننده، برای piping به `jq` یا پاورشل.
- **بسته‌بندی EXE** با یک اسکریپت سازنده و یک منبع واحد نسخه.
- **یکپارچگی اختیاری AutoRun** همراه با اسکریپت نصب و حذف.

---

### پیش‌نیازها

| مؤلفه | پیش‌نیاز |
| --- | --- |
| `cbox.py` | پایتون ۳.۸ به بالا، فقط کتابخانه استاندارد |
| `cbox.cmd` | ویندوز، بدون نیاز به پایتون |
| `cdir.py` | پایتون ۳.۸ به بالا، `rich`، و به‌صورت اختیاری `pywin32` |
| `cpi.py` | پایتون ۳.۸ به بالا، `colorama` |
| `cro.py` | پایتون ۳.۸ به بالا، `colorama`، `requests` |
| `cwho.py` | پایتون ۳.۸ به بالا، `python-whois` |
| `cport.py` | پایتون ۳.۸ به بالا، `rich`، `psutil` |
| `csweep.py` | پایتون ۳.۸ به بالا، `rich`، `psutil` |
| `chash.py` | پایتون ۳.۸ به بالا، `rich` |
| `cwlan.py` | پایتون ۳.۸ به بالا، `rich`، `netsh` ویندوز |
| `netinf.py` | پایتون ۳.۸ به بالا، فقط کتابخانه استاندارد |
| `ntstat.py` | پایتون ۳.۸ به بالا، `rich`، `psutil` |
| `ntpmon.py` | پایتون ۳.۸ به بالا، `rich`، `psutil`، `requests` |
| `nscn.py` | پایتون ۳.۸ به بالا، `rich`، `psutil`، `requests`، `scapy`، Npcap، دسترسی مدیر |
| اسکریپت‌های build | Windows PowerShell 5.1 به بالا، PyInstaller |

نصب یک‌باره‌ی وابستگی‌های پایتون:

```powershell
python -m pip install -r requirements.txt
```

افزونه‌های اختیاری:

- `pywin32` — تنها ستون مالک فایل در `cdir.py` را فعال می‌کند. بدون آن،
  مقدار این ستون `N/A` نمایش داده می‌شود.
- `scapy` — فقط برای `nscn.py` لازم است. در ویندوز به‌علاوهٔ
  [Npcap](https://npcap.com) و یک شل با دسترسی مدیر نیاز دارد. `nscn.py`
  پیش از شروع، هر دو را بررسی می‌کند و به‌جای traceback توضیح می‌دهد.

هر ابزار در نبود یک بستهٔ اختیاری به‌شکل نرم degrade می‌شود: به‌جای `ImportError`
یک راهنمای تک‌خطی نصب چاپ می‌شود.

---

### نصب

ابتدا مخزن را کلون کنید و مستقیم اجرا کنید؛ نیازی به کامپایل نیست.

```powershell
git clone https://github.com/lockheedsr71/CBOX.git
cd CBOX
python -m pip install -r requirements.txt
python cbox.py
```

پوسته هر ابزار را به این ترتیب پیدا می‌کند: `dist\<tool>.exe` ساخته‌شده، سپس EXE
نصب‌شده در `PATH`، و در نهایت `python <tool>.py` در کنار `cbox.py`. بنابراین یک کلون
تازه بدون هیچ مرحلهٔ build کار می‌کند.

برای پوسته batch نیازی به نصب نیست:

```powershell
.\cbox.cmd
```

---

### ساختار پروژه

```
CBOX/
├── cbox.py                # پوسته تعاملی (پایتون، نسخه فعلی)
├── cbox.cmd               # پوسته تعاملی (batch، نسخه اصلی)
├── cbox_core/             # توابع مشترک مورد استفادهٔ همهٔ ابزارها
│   ├── __init__.py        #   __version__ و فهرست TOOLS
│   ├── colors.py          #   پالت ANSI + فعال‌سازی کنسول
│   ├── config.py          #   تجزیهٔ ~/.cboxrc
│   ├── console.py         #   مدیریت وابستگی اختیاری، گلیف امن
│   ├── jsonout.py         #   خروجی مشترک --json
│   ├── lineedit.py        #   تاریخچه + تکمیل (بدون readline)
│   ├── netutil.py         #   دسته‌بندی IP + جست‌وجوی کش‌شدهٔ Geo-IP
│   └── tools.py           #   کشف ابزار (EXE → PATH → اسکریپت)
├── cdir.py                # ابزار نمایش محتوای پوشه با خروجی جدولی Rich
├── cpi.py                 # ابزار ping پیوسته با رنگ‌بندی
├── cro.py                 # traceroute با اطلاعات اختیاری Geo-IP / ASN
├── cwho.py                # استعلام WHOIS و تولید گزارش
├── cport.py               # پورت‌های listening و پروسهٔ مالک
├── csweep.py              # کشف موازی میزبان / پورت
├── chash.py               # هش فایل و تأیید چک‌سام
├── cwlan.py               # وضعیت اینترفیس بی‌سیم
├── netinf.py              # تشخیص عمیق شبکه (IPv4/IPv6/DNS/DHCP)
├── ntstat.py              # جدول سوکت‌ها به همراه پروسهٔ مالک
├── ntpmon.py              # داشبورد مانیتور شبکه هر پروسه
├── nscn.py                # کشف LAN + اسکنر پورت TCP
├── 2exe.py                # تنها اسکریپت PyInstaller برای همهٔ ابزارها
├── build.ps1              # پوستهٔ نازک PowerShell روی 2exe.py
├── install-autorun.cmd    # نصب/حذف اختیاری AutoRun
├── reginit.reg            # قالب رجیستری AutoRun (مستندشده)
├── tests/                 # مجموعه تست pytest
├── pyproject.toml         # پیکربندی بسته‌بندی، pytest و ruff
├── requirements.txt
├── CHANGELOG.md
├── LICENSE
├── exemaker/              # سازنده‌های تک‌ابزار قدیمی
├── .github/workflows/     # CI: تست روی ویندوز+لینوکس، build در تگ
└── .gitignore
```

---

### راهنمای استفاده

#### پوسته CBOX (پایتون)

```powershell
python cbox.py
python cbox.py -c "cpi 8.8.8.8 -n 3"     # اجرای یک دستور، سپس خروج
python cbox.py -f backup.cbox            # اجرای اسکریپت دستورات، سپس خروج
python cbox.py --no-config               # نادیده‌گرفتن ~/.cboxrc در این جلسه
```

```
#######################################################
CBOX v1.2.0  Secure CLI for Windows
Advanced Command-Line Interface (Dynamic Logic)
FOXNET Group | https://software.foxnet.ir
#######################################################
Type '?' for command list. Use 'exit' to quit.
```

مسیر جاری در هر تکرار روی صفحه نمایش داده می‌شود:

```
 C:\Users\you\projects
CBOX > ls
```

**ویرایش خط**

ماژول `readline` در ویندوز وجود ندارد، بنابراین CBOX ویرایشگر خودش را روی `msvcrt`
پیاده‌سازی کرده است. چیزی برای نصب لازم نیست.

| کلید | کار |
| --- | --- |
| `Up` / `Down` | حرکت در تاریخچه (ذخیره‌شده در `~/.cbox_history`) |
| `Tab` | تکمیل نام دستور، یا مسیر پس از `ls` / `cdir` / `chash` |
| `Tab`، `Tab` | با چند گزینه، چرخش بین آن‌ها |
| `Left` / `Right` / `Home` / `End` | جابه‌جایی در خط |
| `Ctrl+A` / `Ctrl+E` | ابتدا / انتهای خط |
| `Ctrl+U` / `Ctrl+K` | حذف تا ابتدا / انتهای خط |
| `Ctrl+W` | حذف کلمهٔ قبلی |
| `Ctrl+L` | پاک کردن صفحه |
| `Ctrl+C` | پرسیدن برای خروج |
| `Ctrl+D` | خروج |

اگر ورودی از ترمینال نباشد (pipe، CI)، ویرایشگر به `input()` ساده برمی‌گردد — بدون
تاریخچه و تکمیل، ولی چیزی خراب نمی‌شود.

**پیکربندی — `~/.cboxrc`**

```
# پیکربندی پوسته CBOX

theme = dark                # dark | light | plain
banner = yes
color = yes
history = yes
history_size = 500
completion = yes
confirm_destructive = yes

# نام‌های مستعار جدول دستورات داخلی را گسترش می‌دهند یا بازنویسی می‌کنند.
alias lg = cdir -a --sort size
alias net = cwho
```

نبود فایل مشکلی نیست. خطوطی که قابل تجزیه نباشند با شمارهٔ خط گزارش و رد می‌شوند،
بنابراین یک غلط تایپی مانع بالا آمدن پوسته نمی‌شود. فایل به‌صورت `utf-8-sig`
خوانده می‌شود، بنابراین BOM نوت‌پد بی‌خطر است.

**محافظ عملیات خطرناک**

`del`، `erase`، `rmdir`، `rd`، `format`، `diskpart` و `kill` پیش از اجرا تأیید
می‌گیرند. زمانی که دستور هدفش ریشهٔ یک درایو یا پوشهٔ خانگی شما باشد محافظ فعال
می‌شود، و با `confirm_destructive = no` در `~/.cboxrc` غیرفعال می‌شود.

**حالت اسکریپت**

`cbox -f script.cbox` هر خط را به‌عنوان یک دستور اجرا می‌کند. خطوط خالی و کامنت‌های
`#` رد می‌شوند، `exit` اسکریپت را متوقف می‌کند، و هر خط دقیقاً مثل ورودی تعاملی از
همان dispatcher عبور می‌کند.

#### پوسته CBOX (batch)

```powershell
.\cbox.cmd
```

پوسته batch علاوه بر دستورات مشترک، چند دستور اختصاصی نیز دارد: `netstat`، `arp`،
`nslookup`، `cp`، `mv`، `del`، `mkd`، `rmd`، `endtask`، `info` و `explore`.
هر دستور شناخته‌شده پیش از اجرا یک کارت راهنمای کوتاه چاپ می‌کند.

#### cdir — نمایش محتوای پوشه

```powershell
python cdir.py                        # پوشه جاری
python cdir.py "C:\Windows"           # مسیر مشخص
python cdir.py -H                      # نمایش فایل‌های مخفی
python cdir.py -s                      # نمایش فایل‌های سیستمی
python cdir.py -a                      # افزودن ستون مالک و مجوزها
python cdir.py --sort size             # name | size | date
```

#### cpi — ابزار ping

```powershell
python cpi.py google.com               # تا زمان توقف با Ctrl+C
python cpi.py 8.8.8.8 -n 10            # ۱۰ درخواست
python cpi.py 8.8.8.8 -i 0.5           # بازه ۵۰۰ میلی‌ثانیه
python cpi.py 8.8.8.8 -o ping.log      # افزودن نتایج به فایل لاگ
```

تأخیر بر اساس رنگ درجه‌بندی می‌شود: سبز زیر ۵۰ms، زرد زیر ۱۵۰ms، نارنجی زیر ۳۰۰ms و
قرمز برای ۳۰۰ms به بالا. در صورت عدم پاسخ، `Request Timed Out!` چاپ می‌شود.

#### cro — ابزار traceroute

```powershell
python cro.py 8.8.8.8                  # traceroute معمولی
python cro.py 8.8.8.8 -m 15            # محدود به ۱۵ hop
python cro.py 8.8.8.8 -g               # نمایش کشور و شهر برای هر hop
python cro.py 8.8.8.8 -a               # نمایش ISP و شماره AS
python cro.py 8.8.8.8 -g -a -o route.log
```

اطلاعات هر hop از `ipwho.is` روی HTTPS (بدون نیاز به کلید API) گرفته می‌شود و تنها در
صورت استفاده از `-g` یا `-a` درخواست می‌شود. نتایج برای طول عمر پروسه کش می‌شوند.
محدوده‌های خصوصی و رزرو‌شده (`10.x`، `172.16-31.x`، `192.168.x`، `127.x`،
`169.254.x`، `100.64-127.x`، و IPv6 ULA/link-local) بدون هیچ درخواست شبکه‌ای با
برچسب `[Internal Network]` مشخص می‌شوند. اگر سرویس در دسترس نباشد، به‌جای شکست
trace برچسب `[geo unavailable]` نمایش داده می‌شود.

#### cwho — ابزار WHOIS

```powershell
python cwho.py google.com
python cwho.py 8.8.8.8 -o whois.txt
```

اطلاعات نام دامنه، ثبت‌کننده، سرور WHOIS، تاریخ ایجاد و انقضا، نیم‌سرورها، وضعیت،
ایمیل‌ها و کشور را گزارش می‌دهد. فیلدهای موجود نبوده `N/A` نمایش داده می‌شوند.

#### netinf — تشخیص شبکه

```powershell
python netinf.py
```

گزارش per-adapter از آدرس فیزیکال، IPv4، IPv6، IPv6 لینک‌-local، ماسک زیرشبکه،
gateway پیش‌فرض، سرور DHCP و وضعیت آن و سرورهای DNS. آداپتورهای مجازی بدون آدرس
نادیده گرفته می‌شوند. خروجی `ipconfig /all` با زنجیرهٔ fallback
UTF-8 → cp1252 → latin-1 دیکد می‌شود تا کنسول محلی‌سازی‌شده گزارش را خراب نکند.

#### ntstat — جدول سوکت‌ها

```powershell
python ntstat.py                          # همهٔ سوکت‌ها
python ntstat.py -p tcp -s ESTABLISHED    # فقط TCPهای برقرار
python ntstat.py -dst 8.8.8.8 -v          # تطبیق مقصد، با جزئیات
```

| سوییچ | کاربرد |
| --- | --- |
| `-p`, `--proto` | `tcp` یا `udp` |
| `-s`, `--status` | تطبیق دقیق وضعیت، مثل `LISTEN` یا `CLOSE_WAIT` |
| `-src`, `--source` | تطبیق بخشی از آدرس محلی |
| `-dst`, `--dest` | تطبیق بخشی از آدرس مقصد |
| `-v`, `--verbose` | افزودن ستون‌های family و socket handle |

نام پروسهٔ مالک برای هر ردیف حل می‌شود؛ ردیف‌هایی که دسترسی به آن‌ها ندارید `N/A`
نمایش داده می‌شوند و حذف نمی‌شوند. سوکت‌های UDP بدون مقصد با `-` نمایش داده می‌شوند.
برای دیدن سوکت‌های سایر کاربران باید با دسترسی مدیر اجرا شود.

#### ntpmon — مانیتور شبکه هر پروسه

```powershell
python ntpmon.py chrome                 # مانیتور بر اساس نام پروسه
python ntpmon.py 4321 -i 0.25           # مانیتور بر اساس PID، تازه‌سازی ۴ بار در ثانیه
```

داشبورد زنده از تمام مقصدهای ریموتی که پروسهٔ هدف نگه داشته، به‌همراه وضعیت، مدت
اتصال، موقعیت Geo-IP و مجموع بایت‌های ارسال/دریافت.

- **برای خروج `ESC` را بزنید.** `Ctrl+C` عمداً سرکوب شده تا تیک تازه‌سازی نتواند
  داشبورد را وسط کار خراب کند.
- بدون دسترسی مدیر، فقط پروسه‌های خودتان دیده می‌شوند.

#### nscn — اسکنر LAN و پورت

```powershell
python nscn.py -s                          # جاروب کل /24 با ARP
python nscn.py -t 192.168.1.5 -p 80-443    # اسکن یک بازهٔ پورت
python nscn.py -t 192.168.1.1 -p 445       # بررسی یک پورت
```

جست‌وجوی زیرشبکه تعاملی است — برای پذیرش زیرشبکهٔ تشخیص‌داده‌شده Enter بزنید. هر
میزبان کشف‌شده آدرس IP، MAC، حدس سیستم‌عامل از روی TTL، RTT و نام سازنده از طریق
`api.macvendors.com` را دریافت می‌کند (کش‌شده و به‌بهترین‌وجه).

> **در ویندوز به دسترسی مدیر و [Npcap](https://npcap.com) نیاز دارد.** `nscn.py`
> پیش از شروع هر دو را بررسی می‌کند و به‌جای traceback توضیح می‌دهد. اسکن به‌صورت
> ترتیبی انجام می‌شود — یک میزبان یا یک پورت در هر لحظه. تنها شبکه‌هایی را اسکن
> کنید که مجاز به تست آن‌ها هستید.

---

### مرجع کامل دستورات

#### `cbox.py` — دستورات پوسته تعاملی

| دستور | نحو | توضیح |
| --- | --- | --- |
| `ls` | `ls [path]` | فهرست محتوای یک پوشه با `dir`. در نبود آرگومان، پوشه جاری. |
| `cd` | `cd [path]` | تغییر پوشه. `~`، `%VAR%` و کوتیشن‌ها را بسط می‌دهد. در نبود آرگومان، پوشهٔ خانگی. |
| `cd -` | `cd -` | بازگشت به پوشهٔ قبلی. رفت‌وبرگشت می‌کند. |
| `cd..` / `cd\` | `cd..` | یک سطح بالاتر، یا ریشهٔ درایو. |
| `pi` | `pi <host>` | ارسال ping به میزبان. |
| `tr` | `tr <host>` | ردیابی مسیر تا میزبان با `tracert -d`. |
| `ip` | `ip` | نمایش پیکربندی شبکه (`ipconfig`). |
| `ipa` | `ipa` | نمایش پیکربندی کامل (`ipconfig /all`). |
| `df` | `df` / `dirfree` | فضای آزاد/کل هر درایو با رنگ‌بندی هشدار، محاسبه‌شده در خود پایتون. |
| `task` | `task` | فهرست پروسه‌های در حال اجرا با `tasklist`. |
| `ps` | `ps` | همان `task`. |
| `kill` | `kill <PID>` | خاتمه اجباری پروسه با شماره PID. ابتدا تأیید می‌گیرد. |
| `who` | `who` | نمایش کاربر جاری (`whoami`). |
| `ver` | `ver` | نمایش نسخه سیستم‌عامل. |
| `cl` | `cl` | پاک کردن صفحه. |
| `cdir` | `cdir [flags] [path]` | ابزار نمایش محتوای پوشه. |
| `cpi` | `cpi <target...>` | ping رنگ‌بندی‌شده. |
| `cro` | `cro <host> [flags]` | traceroute با Geo-IP/ASN. |
| `cwho` | `cwho <domain>` | استعلام WHOIS. |
| `cport` | `cport [flags]` | پورت‌های listening و پروسهٔ مالک. |
| `csweep` | `csweep [subnet] [flags]` | کشف موازی میزبان/پورت. |
| `chash` | `chash <path...> [flags]` | هش و تأیید چک‌سام. |
| `cwlan` | `cwlan` | وضعیت اینترفیس بی‌سیم. |
| `netdetail` | `netdetail` | تشخیص عمیق شبکه (اجرای `netinf.py`). |
| `ntstat` | `ntstat [flags]` | جدول سوکت‌ها به همراه پروسهٔ مالک. |
| `ntpmon` | `ntpmon <name\|pid>` | داشبورد مانیتور شبکه هر پروسه. |
| `nscn` | `nscn [flags]` | اسکنر LAN / پورت. |
| `?` | `?`، `help`، `-h`، `--help` | نمایش فهرست دستورات. |
| `exit` / `quit` | `exit` | خروج از پوسته. بدون حساسیت به بزرگی حروف. |

`df` به‌جای فراخوانی `wmic logicaldisk` مستقیماً با پایتون پیاده‌سازی شده، چون
`wmic` دیگر در ویندوز ۱۱ نسخهٔ 24H2 ارائه نمی‌شود.

ابزارهای داخلی CBOX همان سوییچ‌هایی را می‌پذیرند که به‌صورت مستقل دارند، و بدون
عبور از `cmd.exe` فراخوانی می‌شوند — بنابراین آرگومان‌های داخل کوتیشن دست‌نخورده
می‌مانند:

```
CBOX > cro 8.8.8.8 -g -a
CBOX > cpi 8.8.8.8 1.1.1.1
CBOX > cdir -a --sort size "C:\Program Files"
```

**رفتار کلیدها**

| کلید | عملکرد |
| --- | --- |
| `Ctrl+C` در خط فرمان | پرسش `Exit CBOX? (y/N)` می‌دهد. با `y` خارج می‌شود، هر چیز دیگر ادامه می‌دهد. |
| `Ctrl+C` حین اجرای دستور | پروسه فرزند را متوقف کرده و پوسته را زنده نگه می‌دارد. |

**قانون عبور** — هر ورودی که در جدول بالا نباشد، عیناً به‌عنوان دستور ویندوز اجرا می‌شود.

---

#### `cbox.cmd` — دستورات پوسته تعاملی

| دستور | نحو | توضیح |
| --- | --- | --- |
| `cl` | `cl` | پاک کردن صفحه. |
| `who` | `who` | نمایش کاربر جاری. |
| `ver` | `ver` | نمایش نسخه CBOX و نسخه سیستم‌عامل. |
| `info` | `info` | خروجی کامل `systeminfo`. |
| `netstat` | `netstat` | نمایش اتصالات شبکه فعال. |
| `arp` | `arp` | نمایش کش ARP (`arp -a`). |
| `nslookup` | `nslookup` | از کاربر میزبان را می‌پرسد و آن را resolve می‌کند. |
| `task` | `task` | فهرست پروسه‌های در حال اجرا. |
| `ps` | `ps` | همان `task`. |
| `kill` | `kill <PID>` | خاتمه پروسه با شماره PID (بدون `/F`). |
| `endtask` | `endtask` | نام پروسه را می‌پرسد و با نام فایل آن را می‌کشد (`taskkill /IM <name> /F`). |
| `dirfree` | `dirfree` | فضای آزاد همه درایوها. |
| `df` | `df` | فضای آزاد همه درایوها (شکل جایگزین). |
| `ls` | `ls` | فهرست پوشه جاری. |
| `ls <path>` | `ls <path>` | فهرست یک مسیر مشخص. |
| `pi` | `pi <host> [options]` | ارسال ping؛ آرگومان‌های اضافه مستقیم به `ping` منتقل می‌شوند، پس `-t`، `-n 4` و `-l 1024` کار می‌کنند. |
| `tr` | `tr <host>` | ردیابی مسیر بدون resolve نام (`tracert -d`). |
| `cp` | `cp <src> <dst>` | کپی فایل. هر دو مسیر داخل کوتیشن قرار می‌گیرند. |
| `mv` | `mv <src> <dst>` | جابه‌جایی یا تغییر نام فایل. |
| `del` | `del <file>` | حذف فایل. |
| `mkd` | `mkd <folder>` | ساخت پوشه. |
| `rmd` | `rmd <dir> [/s]` | حذف پوشه. برای پوشه‌های غیرخالی `/s` را اضافه کنید. |
| `ip` | `ip` | پیکربندی شبکه. |
| `ipa` | `ipa` | پیکربندی شبکه (شکل جایگزین). |
| `explore` | `explore` | مسیر پوشه را می‌پرسد و محتوای آن را فهرست می‌کند. |
| `?` | `?` | صفحه راهنمای کامل. |
| `exit` / `quit` | `exit` | خروج از پوسته. |

**نکات رفتاری**

- هر دستور شناخته‌شده پیش از اجرا یک کارت کوچک راهنما (`Command`، `Description`) چاپ می‌کند.
- برای دستورات فایل (`cp`، `mv`، `del`، `mkd`، `rmd`) مسیرها داخل کوتیشن قرار می‌گیرند،
  بنابراین مسیرهای دارای فاصله کار می‌کنند.
- `nslookup`، `endtask` و `explore` آرگومان خود را به‌صورت تعاملی می‌پرسند.
- هر ورودی دیگر در صفحه نمایش داده شده و بدون تغییر توسط `cmd` اجرا می‌شود.

---

#### `cdir.py` — نمایش محتوای پوشه

```
usage: cdir.py [-h] [-H] [-s] [-a] [--sort {name,size,date}] [path ...]
```

| گزینه | کوتاه | نوع | پیش‌فرض | توضیح |
| --- | --- | --- | --- | --- |
| `--hidden` | `-H` | پرچم | خیر | نمایش موارد با صفت hidden. |
| `--system` | `-s` | پرچم | خیر | نمایش موارد با صفت system. |
| `--all` | `-a` | پرچم | خیر | افزودن ستون‌های `Owner` و `Permissions`. |
| `--sort` | — | انتخابی | `name` | کلید مرتب‌سازی: `name`، `size` یا `date`. |
| `path` | — | موقعیتی | `.` | پوشه هدف. چند توکن را می‌پذیرد و به هم می‌چسباند، بنابراین مسیرهای دارای فاصله هم کار می‌کنند. |
| `--help` | `-h` | پرچم | — | نمایش صفحه راهنما. |

| مقدار `--sort` | رفتار |
| --- | --- |
| `name` | الفبایی، بدون حساسیت به بزرگی حروف، صعودی. |
| `size` | از بزرگ به کوچک؛ پوشه‌ها صفر شمرده می‌شوند. |
| `date` | از جدیدترین به قدیمی‌ترین. |

**ستون‌های خروجی**

| ستون | توضیح |
| --- | --- |
| `Attr` | سه کاراکتر: `H` مخفی، `S` سیستمی، `R` فقط‌خواندنی. در غیر این صورت `-`. |
| `Name` | نام پوشه یا فایل با نشانگر 📁 / 📄. پوشه‌ها آبی پررنگ هستند. |
| `Size` | کیلوبایت با جداکننده هزارگان، یا `DIR` برای پوشه‌ها. |
| `Last Modified` | قالب `YYYY-MM-DD HH:MM`. |
| `Owner` | فقط با `-a`. به‌شکل `DOMAIN\user` از طریق `pywin32`، در غیر این صورت `N/A`. |
| `Permissions` | فقط با `-a`. خروجی `stat.filemode()` مانند `-rw-rw-rw-`. |

**نمونه‌ها**

```powershell
python cdir.py                                  # پوشه جاری، مرتب‌سازی بر اساس نام
python cdir.py "C:\Program Files"               # مسیر مشخص
python cdir.py . -H -s                          # نمایش موارد مخفی و سیستمی
python cdir.py -a                               # همراه با مالک و مجوزها
python cdir.py --sort size -a                   # از بزرگ به کوچک، همراه مالک
python cdir.py --sort date                      # از جدید به قدیم
python cdir.py D:\backups                       # مسیر تک‌کلمه‌ای بدون کوتیشن
```

---

#### `cpi.py` — ابزار ping

```
usage: cpi.py [-h] [-n COUNT] [-i INTERVAL] [-o OUTPUT] [target]
```

| گزینه | کوتاه | نوع | پیش‌فرض | توضیح |
| --- | --- | --- | --- | --- |
| `target` | — | موقعیتی | ندارد | آدرس IP یا دامنه. در نبود آن، راهنما چاپ و کد خروج ۱ برگردانده می‌شود. |
| `--count` | `-n` | عدد صحیح | بی‌نهایت | تعداد درخواست‌های echo. |
| `--interval` | `-i` | اعشاری | `1.0` | فاصله زمانی بین درخواست‌ها بر حسب ثانیه. |
| `--output` | `-o` | رشته | ندارد | مسیر فایل لاگ. نتایج **افزوده** می‌شوند، نه بازنویسی. |
| `--help` | `-h` | پرچم | — | نمایش صفحه راهنما. |

**ستون‌های خروجی**

```
Row | Date       | Time     | Target         | Latency  | TTL
```

**درجه‌بندی رنگ تأخیر**

| تأخیر | رنگ |
| --- | --- |
| کمتر از ۵۰ms | سبز |
| کمتر از ۱۵۰ms | زرد |
| کمتر از ۳۰۰ms | نارنجی |
| ۳۰۰ms به بالا | قرمز |
| بدون پاسخ | قرمز، `Request Timed Out!` |

در هر تکرار یک ping تک‌بسته‌ای اجرا می‌شود (`ping -n 1` در ویندوز، `ping -c 1` در
سیستم‌های دیگر) و مقادیر `time[=<]Nms` و `TTL=` با عبارات باقاعده استخراج می‌شوند.
هر ping محدودیت زمانی ۵ ثانیه دارد. `Ctrl+C` خروج تمیز ایجاد می‌کند.

**نمونه‌ها**

```powershell
python cpi.py google.com                       # پیوسته
python cpi.py 8.8.8.8 -n 20                    # دقیقاً ۲۰ درخواست
python cpi.py 8.8.8.8 -i 0.25                  # ۴ ping در ثانیه
python cpi.py google.com -n 100 -o logs\ping.log
```

---

#### `cro.py` — ابزار traceroute

```
usage: cro.py [-h] [-m MAX_HOPS] [-g] [-a] [-o OUTPUT] [target]
```

| گزینه | کوتاه | نوع | پیش‌فرض | توضیح |
| --- | --- | --- | --- | --- |
| `target` | — | موقعیتی | ندارد | آدرس IP یا دامنه. در نبود آن، راهنما چاپ و کد خروج ۱ برگردانده می‌شود. |
| `--max-hops` | `-m` | عدد صحیح | `20` | حداکثر تعداد hop برای ردیابی. |
| `--geo` | `-g` | پرچم | خیر | نمایش کشور و شهر برای هر hop. |
| `--asn` | `-a` | پرچم | خیر | نمایش ISP و شماره AS برای هر hop. |
| `--output` | `-o` | رشته | ندارد | مسیر فایل لاگ. نتایج **افزوده** می‌شوند. |
| `--help` | `-h` | پرچم | — | نمایش صفحه راهنما. |

**جزئیات فنی**

| سیستم‌عامل | دستور اجرایی |
| --- | --- |
| ویندوز | `tracert -d -h <max_hops> <target>` |
| لینوکس / مک | `traceroute -n -m <max_hops> <target>` |

**رنگ‌بندی خطوط**

| وضعیت hop | رنگ |
| --- | --- |
| `*` (بدون پاسخ) | قرمز |
| پاسخ‌داده‌شده | سبز |
| IP خصوصی (`10.x`، `172.16-31.x`، `192.168.x`، `127.x`) | برچسب `[Internal Network]` بدون درخواست شبکه |
| انقضای زمانی جست‌وجو | برچسب `[Lookup Timeout]` |

داده‌های Geo و ASN از `ip-api.com` تأمین می‌شوند و تنها با `-g` یا `-a` درخواست
می‌شوند. برای هر hop محدودیت زمانی ۲ ثانیه در نظر گرفته شده است.

**نمونه‌ها**

```powershell
python cro.py 8.8.8.8                          # ساده، ۲۰ hop
python cro.py google.com -m 30                 # ردیابی عمیق‌تر
python cro.py 8.8.8.8 -g                       # کشور و شهر
python cro.py 8.8.8.8 -a                       # ISP و شماره AS
python cro.py 8.8.8.8 -g -a -o logs\trace.log
```

---

#### `cwho.py` — ابزار WHOIS

```
usage: cwho.py [-h] [-o OUTPUT] target
```

| گزینه | کوتاه | نوع | پیش‌فرض | توضیح |
| --- | --- | --- | --- | --- |
| `target` | — | موقعیتی | **الزامی** | نام دامنه یا آدرس IP. |
| `--output` | `-o` | رشته | ندارد | مسیر فایل گزارش. با خط جداکننده افزوده می‌شود. |
| `--help` | `-h` | پرچم | — | نمایش صفحه راهنما. |

**فیلدهای گزارش**

`Domain Name`، `Registrar`، `Whois Server`، `Creation Date`، `Expiration Date`،
`Name Servers`، `Status`، `Emails`، `Country`.

برچسب فیلدها زرد و مقادیر سفید چاپ می‌شوند. مقادیر فهرستی (نیم‌سرورها، وضعیت،
ایمیل‌ها) با کاما به هم چسبانده می‌شوند. خطاها قرمز چاپ می‌شوند و اجرای ابزار را متوقف
نمی‌کنند.

**نمونه‌ها**

```powershell
python cwho.py google.com
python cwho.py whois.arin.net
python cwho.py 8.8.8.8 -o logs\whois.txt
```

---

### ساخت فایل EXE

تمام منطق ساخت در یک اسکریپت، یعنی `2exe.py`، قرار دارد. فهرست ابزارها و نسخه از
`cbox_core` خوانده می‌شود، بنابراین دیگر فایل فهرست دستی برای هم‌گام‌سازی وجود ندارد.

#### 2exe.py (پیشنهادی)

```powershell
python 2exe.py                          # ساخت همهٔ ابزارها در dist\
python 2exe.py cpi cro                  # فقط ابزارهای نام‌برده
python 2exe.py --no-metadata            # رد کردن منبع نسخه ویندوز
python 2exe.py --windowed               # بدون پنجره کنسول
python 2exe.py --no-confirm             # بدون پرسش (استفاده در CI)
```

خروجی در `dist\<tool>.exe` قرار می‌گیرد. فایل‌های میانی و منابع نسخهٔ تولیدشده به
`build\` می‌روند، نه ریشهٔ مخزن.

#### build.ps1 (پوسته)

```powershell
.\build.ps1                              # ساخت همه
.\build.ps1 -Name cro                     # ساخت یک ابزار
.\build.ps1 -Name cro -Windowed           # بدون پنجره کنسول
.\build.ps1 -Clean                        # حذف build\ و dist\ پیش از ساخت
```

| پارامتر | نوع | پیش‌فرض | توضیح |
| --- | --- | --- | --- |
| `-Name` | رشته[] | همهٔ ابزارها | نام ابزارهایی که ساخته می‌شوند. |
| `-Windowed` | سوییچ | خیر | ساخت بدون پنجره کنسول. |
| `-Clean` | سوییچ | خیر | حذف `build\` و `dist\` پیش از ساخت. |
| `-NoMetadata` | سوییچ | خیر | رد کردن منبع نسخه. |

#### exemaker\ (قدیمی)

فایل‌های `exemaker\maker.bat`، `exemaker\build.ps1` و `exemaker\buildtr.ps1` سازنده‌های
تک‌ابزار اولیه هستند. هنوز نام‌های حذف‌شدهٔ `tping.py` و `troute.py` را ارجاع می‌دهند؛
به‌جای آن‌ها از `2exe.py` استفاده کنید.

---

### اتصال خودکار به cmd

`install-autorun.cmd` مقدار `AutoRun` در Command Processor را طوری ثبت می‌کند که یک
پنجرهٔ جدید `cmd.exe` مستقیماً داخل CBOX باز شود:

```powershell
.\install-autorun.cmd              # ثبت
.\install-autorun.cmd /uninstall   # حذف و بازگرداندن پرامپت معمولی
```

این اسکریپت مسیر مطلق واقعی را خودش می‌نویسد، ابتدا مقدار فعلی را نمایش می‌دهد و
برای تأیید می‌پرسد. هنگام حذف، مقدار **حذف** می‌شود نه خالی — چون `AutoRun` خالی هم
توسط `cmd.exe` اجرا می‌شود و یک کنسول دوم باز می‌کند.

`reginit.reg` به‌عنوان قالب مستند نگه داشته شده است اگر ترجیح می‌دهید از
`reg import` استفاده کنید. مسیر را پیش از اعمال ویرایش کنید.

> این تنظیم روی **هر** پنجرهٔ `cmd.exe` که با این حساب باز شود اثر می‌گذارد، از جمله
> پنجره‌هایی که برنامه‌های دیگر باز می‌کنند. به‌طور پیش‌فرض خاموش و کاملاً اختیاری است.

---

### توسعه

```powershell
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest                        # ۸۰ تست، بدون نیاز به شبکه
python -m compileall -q .               # بایت‌کامپایل همهٔ ابزارها
```

پوشهٔ `tests/` دسته‌بندی IP، کش جست‌وجوی Geo-IP، کشف ابزار، جدول alias و dispatch
پوسته و parserهای هر ابزار را پوشش می‌دهد. همهٔ تست‌ها آفلاین‌اند — فراخوانی‌های شبکه
با monkeypatch جایگزین می‌شوند.

CI (`.github/workflows/ci.yml`) مجموعه تست را روی ویندوز و لینوکس اجرا می‌کند، همهٔ
ابزارها را بایت‌کامپایل می‌کند و روی تگ `v*` همهٔ EXEها را می‌سازد و به‌عنوان artifact
بارگذاری می‌کند.

---

### نکات فنی

- **عبور به‌عنوان طراحی اصلی.** هر دو پوسته ورودی‌های ناشناخته را از طریق شل سیستم
  اجرا می‌کنند. این روش راحت است، اما به این معنا نیز هست که هر رشته‌ای که پوسته بپذیرد،
  یک دستور معتبر است. `cbox.cmd` و `cbox.py` را ابزار تعاملی بدانید، نه یک محیط ایزوله.
- **خطر تزریق شل.** `cbox.py` ورودی عبوری را از طریق `cmd.exe` اجرا می‌کند و aliasهای
  کوتاه آرگومان‌ها را در یک رشتهٔ دستور جای‌گذاری می‌کنند. بنابراین مسیرهایی که شامل
  کاراکترهای ویژهٔ شل هستند می‌توانند دستور را خراب کنند. ابزارهای داخلی CBOX
  (`cdir`، `cpi`، `cro`، `cwho`، `netdetail`، `ntstat`، `ntpmon`، `nscn`) با
  `shell=False` اجرا می‌شوند، پس آرگومان‌هایشان هرگز دوباره توسط شل تجزیه نمی‌شوند.
  برای ورودی‌های غیرقابل اعتماد از آن‌ها استفاده کنید.
- **مدیریت پروسه.** `cbox.py` یک ارجاع به پروسه فرزند در حال اجرا نگه می‌دارد تا
  `Ctrl+C` آن را متوقف کند و پروسه یتیم رها نشود.
- **خروجی رنگی.** `cbox.py` و `cbox.cmd` کدهای ANSI خام چاپ می‌کنند. `cdir.py` از
  نشانه‌گذاری Rich و بقیه ابزارها از Colorama استفاده می‌کنند. برای غیرفعال‌کردن
  رنگ `NO_COLOR=1` را تنظیم کنید. `cro.py` پیش از نوشتن در فایل لاگ، کدهای رنگ را
  حذف می‌کند.
- **انکدینگ کنسول.** کنسول‌های قدیمی (cp437/cp1252) نمی‌توانند گلیف پوشه/فایل را
  انکد کنند؛ این گلیف‌ها به `[D]` و `--` تبدیل می‌شوند به‌جای اینکه
  `UnicodeEncodeError` بدهند. خروجی `ipconfig` با زنجیرهٔ fallback
  UTF-8 → cp1252 → latin-1 دیکد می‌شود.
- **کش Geo-IP فقط در حافظهٔ پروسه است.** کش روی دیسک وجود ندارد، پس هر اجرا از صفر
  شروع می‌شود. خطاها هم به‌مدت ۶۰ ثانیه کش می‌شوند تا سرویس قطع‌شده به طوفان درخواست
  تبدیل نشود.
- **APIهای منسوخ.** دستور `df` در هر دو پوسته و دستور `ver` به `wmic` و `systeminfo`
  وابسته هستند که در نسخه‌های اخیر ویندوز در حال کنار گذاشته شده‌اند. در صورت عدم کارکرد،
  از `Get-Volume` در پاورشل استفاده کنید.
- **دسترسی مدیر.** `nscn.py` برای سوکت خام به دسترسی مدیر به‌علاوهٔ Npcap نیاز دارد؛
  `ntstat.py` و `ntpmon.py` فقط با دسترسی مدیر سوکت‌های سایر کاربران را می‌بینند.
- **تغییرات رجیستری دائمی هستند.** `install-autorun.cmd` تنظیمات Command Processor
  کاربر جاری را تغییر می‌دهد. با سوییچ `/uninstall` آن را حذف کنید.

---

### سلب مسئولیت

برای استفاده آموزشی و اداری روی سامانه‌هایی که در اختیار دارید یا مجاز به آزمون آن‌ها
هستید. داده‌های Geo-IP از سرویس‌های رایگان `ipwho.is` و `api.macvendors.com` و
داده‌های WHOIS از سرورهای عمومی WHOIS می‌آید. قوانین محلی و شرایط استفاده این
سرویس‌ها را رعایت کنید. تنها شبکه‌هایی را اسکن کنید که مجاز به تست آن‌ها هستید.

---

### مجوز

تحت مجوز MIT منتشر شده است. فایل [LICENSE](LICENSE) را ببینید.

---

<div align="center">

**CBOX** — ساخته‌شده توسط FOXNET Group

</div>