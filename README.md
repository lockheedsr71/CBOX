# CBOX — Secure CLI Toolkit for Windows

**[English](#english) · [فارسی](#فارسی)**

CBOX is a small, dependency-light command-line toolkit for Windows. It bundles two
interactive shells (a batch-based one and a Python refactor) plus a set of standalone
CLI tools for directory listing, ping, traceroute, and WHOIS lookups.

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
- [Technical Notes](#technical-notes)
- [Disclaimer](#disclaimer)
- [License](#license)

---

### Features

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

### Requirements

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

### Installation

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

### Project Layout

```
CBOX/
├── cbox.py        # Interactive shell (Python refactor, v1.0.1)
├── cbox.cmd       # Interactive shell (batch, v1.0)
├── cdir.py        # Directory lister with rich table output
├── cpi.py         # Color-coded continuous ping
├── cro.py         # Traceroute with optional Geo-IP / ASN info
├── cwho.py        # WHOIS lookup and report
├── build.ps1      # PyInstaller build helper
├── reginit.reg    # Registry file to hook cbox.cmd into cmd AutoRun
├── exemaker/
│   ├── build.ps1      # PyInstaller helper
│   ├── buildtr.ps1   # PyInstaller helper (traceroute build)
│   └── maker.bat     # Interactive builder with version metadata + icon
└── .gitignore
```

---

### Usage

#### CBOX shell (Python)

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

Per-hop lookups use the `ip-api.com` endpoint and only happen when `-g` or `-a` is
passed. Private ranges (`10.x`, `172.16-31.x`, `192.168.x`, `127.x`) are labeled
`[Internal Network]` without any network call.

#### cwho — whois tool

```powershell
python cwho.py google.com
python cwho.py 8.8.8.8 -o whois.txt
```

Reports domain name, registrar, WHOIS server, creation and expiration dates, name
servers, status, emails, and country.

---

### Complete Command Reference

#### `cbox.py` — interactive shell commands

| Command | Syntax | Description |
| --- | --- | --- |
| `ls` | `ls [path]` | Lists a directory via `dir`. Defaults to the current directory. |
| `pi` | `pi <host>` | Pings a host. Requires an argument. |
| `tr` | `tr <host>` | Traces the route to a host via `tracert -d`. Requires an argument. |
| `ip` | `ip` | Shows network configuration (`ipconfig`). |
| `ipa` | `ipa` | Same as `ip`. Alias kept for muscle memory. |
| `df` | `df` / `dirfree` | Shows size, free space, and caption of every logical drive. |
| `task` | `task` | Lists running processes via `tasklist`. |
| `ps` | `ps` | Same as `task`. |
| `kill` | `kill <PID>` | Force-kills a process by numeric PID (`taskkill /PID <pid> /F`). |
| `who` | `who` | Prints the current user (`whoami`). |
| `ver` | `ver` | Prints the OS version (`systeminfo | findstr /B /C:"OS Version"`). |
| `cl` | `cl` | Clears the screen. |
| `?` | `?` | Prints the command list. |
| `exit` / `quit` | `exit` | Leaves the shell. Case-insensitive. |

**Keyboard behavior**

| Key | Action |
| --- | --- |
| `Ctrl+C` at the prompt | Asks `Exit CBOX? (y/N)`. `y` exits, anything else continues. |
| `Ctrl+C` while a command runs | Terminates the child process, keeps the shell alive. |

**Pass-through rule** — anything not in the table above is executed as a raw Windows
command line.

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

#### maker.bat (interactive)

```powershell
cd exemaker
.\maker.bat
```

Prompts for the script name, version, company, and description, generates a
`version.txt` for the Windows file properties dialog, then runs PyInstaller. If
`icon.ico` is present in the working directory it is embedded along with `icon.png`.
Output lands in `dist\<scriptname>.exe`. The temporary `version.txt` is deleted
afterwards.

#### build.ps1 (parameterized)

```powershell
.\build.ps1 -Name cpi -OneFile             # single console exe
.\build.ps1 -Name cpi -OneFile -Windowed   # no console window
.\build.ps1 -Name cpi -OneFile -Clean      # remove build/, dist/, spec first
```

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `-Name` | string | `tping` | Output executable name. |
| `-OneFile` | switch | `true` | Produce a single self-contained exe. |
| `-Windowed` | switch | off | Build without a console window. |
| `-Clean` | switch | off | Delete `build\`, `dist\`, and `<Name>.spec` before building. |

Exit codes: `2` Python not found, `3` PyInstaller install failed, `4` entry script
missing, otherwise the PyInstaller exit code.

> **Note:** the bundled `build.ps1`, `exemaker\build.ps1`, and `exemaker\buildtr.ps1`
> still reference the earlier script names `tping.py` and `troute.py`, which are now
> `cpi.py` and `cro.py`. Update the `$scriptPath` line or copy the file to the expected
> name first.

---

### cmd AutoRun integration

`reginit.reg` sets the Command Processor `AutoRun` value so `cbox.cmd` starts inside
every new `cmd` window:

```
[HKEY_CURRENT_USER\Software\Microsoft\Command Processor]
"AutoRun"="D:\\MyPrograms\\cmd\\cbox.cmd"
```

| Step | Command |
| --- | --- |
| 1. Edit the path in `reginit.reg` to your actual location | — |
| 2. Apply | `reg import .\reginit.reg` |
| 3. Roll back | `reg delete "HKCU\Software\Microsoft\Command Processor" /v AutoRun /f` |

---

### Technical Notes

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
- **Plain HTTP lookup.** `cro.py` queries `http://ip-api.com` without TLS.
- **Registry hooks are persistent.** `reginit.reg` modifies the current user's Command
  Processor settings. Remove it with the `reg delete` command above if you don't want it.
- **No `requirements.txt`.** Dependency list lives in this README. Consider adding one.

---

### Disclaimer

For educational and administrative use on systems you own or are authorized to test.
Geo-IP data comes from the free `ip-api.com` endpoint; WHOIS data comes from the public
WHOIS servers. Respect local law and the terms of those services.

---

### License

Released under the MIT License.

---
---

# فارسی

CBOX یک جعبه‌ابزار خط فرمان سبک و کم‌وابستگی برای ویندوز است. شامل دو پوسته تعاملی
(یکی مبتنی بر batch و یکی بازنویسی‌شده با پایتون) به‌همراه چند ابزار مستقل برای
نمایش محتوای پوشه، ping، traceroute و استعلام WHOIS.

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
- [نکات فنی](#نکات-فنی)
- [سلب مسئولیت](#سلب-مسئولیت)
- [مجوز](#مجوز-1)

---

### ویژگی‌ها

- **دو پوسته تعاملی** — `cbox.py` (پایتون، نسخه فعلی) و `cbox.cmd` (batch، نسخه اصلی).
- **دستورات کوتاه به سبک یونیکس** — `ls`، `ps`، `kill`، `df`، `ip`، `pi`، `tr` و ...
- **اجرای عبوری** — هر دستوری که مربوط به CBOX نباشد مستقیماً به شل سیستم سپرده می‌شود.
- **خروجی جدولی غنی (Rich)** برای لیست کردن پوشه‌ها، شامل پرچم‌های hidden/system،
  مالک فایل و مجوزها.
- **Ping رنگ‌بندی‌شده** با درجه‌بندی تأخیر و امکان ذخیره لاگ.
- **Traceroute با قابلیت جست‌وجوی اختیاری Geo-IP و ASN** برای هر hop.
- **گزارش WHOIS** برای دامنه و IP، با امکان ذخیره در فایل.
- **ابزار بسته‌بندی EXE** بر مبنای PyInstaller، با پشتیبانی از آیکون و متادیتای نسخه.
- **AutoRun بدون پیکربندی** برای اجرای خودکار پوسته در هر پنجره جدید `cmd`.

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
| اسکریپت‌های build | Windows PowerShell 5.1 به بالا، PyInstaller |

نصب یک‌باره‌ی وابستگی‌های پایتون:

```powershell
python -m pip install rich pywin32 colorama requests python-whois
```

`pywin32` اختیاری است و تنها ستون مالک فایل در `cdir.py` را فعال می‌کند. بدون آن،
مقدار این ستون `N/A` نمایش داده می‌شود.

---

### نصب

ابتدا مخزن را کلون کنید و مستقیم اجرا کنید؛ نیازی به کامپایل نیست.

```powershell
git clone https://github.com/lockheedsr71/CBOX.git
cd CBOX
python cbox.py
```

برای پوسته batch نیازی به نصب نیست:

```powershell
.\cbox.cmd
```

---

### ساختار پروژه

```
CBOX/
├── cbox.py        # پوسته تعاملی (بازنویسی پایتون، نسخه ۱.۰.۱)
├── cbox.cmd       # پوسته تعاملی (batch، نسخه ۱.۰)
├── cdir.py        # ابزار نمایش محتوای پوشه با خروجی جدولی Rich
├── cpi.py         # ابزار ping پیوسته با رنگ‌بندی
├── cro.py         # traceroute با اطلاعات اختیاری Geo-IP / ASN
├── cwho.py        # استعلام WHOIS و تولید گزارش
├── build.ps1      # اسکریپت کمکی PyInstaller
├── reginit.reg    # فایل رجیستری برای اجرای خودکار cbox.cmd در cmd
├── exemaker/
│   ├── build.ps1      # اسکریپت کمکی PyInstaller
│   ├── buildtr.ps1   # اسکریپت کمکی PyInstaller برای traceroute
│   └── maker.bat     # سازنده تعاملی با متادیتای نسخه و آیکون
└── .gitignore
```

---

### راهنمای استفاده

#### پوسته CBOX (پایتون)

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

مسیر جاری در هر تکرار روی صفحه نمایش داده می‌شود:

```
 C:\Users\you\projects
CBOX > ls
```

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

اطلاعات هر hop از `ip-api.com` گرفته می‌شود و تنها در صورت استفاده از `-g` یا `-a`
درخواست می‌شود. محدوده‌های خصوصی (`10.x`، `172.16-31.x`، `192.168.x`، `127.x`) بدون
هیچ درخواست شبکه‌ای با برچسب `[Internal Network]` مشخص می‌شوند.

#### cwho — ابزار WHOIS

```powershell
python cwho.py google.com
python cwho.py 8.8.8.8 -o whois.txt
```

اطلاعات نام دامنه، ثبت‌کننده، سرور WHOIS، تاریخ ایجاد و انقضا، نیم‌سرورها، وضعیت،
ایمیل‌ها و کشور را گزارش می‌دهد.

---

### مرجع کامل دستورات

#### `cbox.py` — دستورات پوسته تعاملی

| دستور | نحو | توضیح |
| --- | --- | --- |
| `ls` | `ls [path]` | فهرست محتوای یک پوشه با `dir`. در نبود آرگومان، پوشه جاری. |
| `pi` | `pi <host>` | ارسال ping به میزبان. آرگومان الزامی است. |
| `tr` | `tr <host>` | ردیابی مسیر تا میزبان با `tracert -d`. آرگومان الزامی است. |
| `ip` | `ip` | نمایش پیکربندی شبکه (`ipconfig`). |
| `ipa` | `ipa` | همان `ip`، به‌عنوان نام مستعار. |
| `df` | `df` / `dirfree` | نمایش حجم، فضای آزاد و نام همه درایوهای منطقی. |
| `task` | `task` | فهرست پروسه‌های در حال اجرا با `tasklist`. |
| `ps` | `ps` | همان `task`. |
| `kill` | `kill <PID>` | خاتمه اجباری پروسه با شماره PID (`taskkill /PID <pid> /F`). |
| `who` | `who` | نمایش کاربر جاری (`whoami`). |
| `ver` | `ver` | نمایش نسخه سیستم‌عامل. |
| `cl` | `cl` | پاک کردن صفحه. |
| `?` | `?` | نمایش فهرست دستورات. |
| `exit` / `quit` | `exit` | خروج از پوسته. بدون حساسیت به بزرگی حروف. |

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

#### maker.bat (تعاملی)

```powershell
cd exemaker
.\maker.bat
```

نام اسکریپت، نسخه، نام شرکت و توضیح را می‌پرسد، یک `version.txt` برای پنجره خواص فایل
ویندوز تولید می‌کند و سپس PyInstaller را اجرا می‌کند. اگر `icon.ico` در پوشه جاری
موجود باشد، همراه با `icon.png` جاسازی می‌شود. خروجی در `dist\<scriptname>.exe` قرار
می‌گیرد. فایل موقت `version.txt` پس از پایان حذف می‌شود.

#### build.ps1 (پارامتری)

```powershell
.\build.ps1 -Name cpi -OneFile             # یک فایل exe کنسولی
.\build.ps1 -Name cpi -OneFile -Windowed   # بدون پنجره کنسول
.\build.ps1 -Name cpi -OneFile -Clean      # حذف build/، dist/ و spec پیش از ساخت
```

| پارامتر | نوع | پیش‌فرض | توضیح |
| --- | --- | --- | --- |
| `-Name` | رشته | `tping` | نام فایل خروجی. |
| `-OneFile` | سوییچ | `true` | تولید یک exe مستقل. |
| `-Windowed` | سوییچ | خیر | ساخت بدون پنجره کنسول. |
| `-Clean` | سوییچ | خیر | حذف `build\`، `dist\` و `<Name>.spec` پیش از ساخت. |

کدهای خروج: `۲` پایتون پیدا نشد، `۳` نصب PyInstaller ناموفق بود، `۴` اسکریپت ورودی
پیدا نشد، و در سایر موارد کد خروج PyInstaller.

> **توجه:** فایل‌های `build.ps1`، `exemaker\build.ps1` و `exemaker\buildtr.ps1` هنوز
> نام‌های قدیمی `tping.py` و `troute.py` را ارجاع می‌دهند، در حالی که فایل‌های فعلی
> `cpi.py` و `cro.py` هستند. خط `$scriptPath` را ویرایش کنید یا فایل را با نام مورد
> انتظار کپی کنید.

---

### اتصال خودکار به cmd

فایل `reginit.reg` مقدار `AutoRun` در Command Processor را تنظیم می‌کند تا `cbox.cmd`
در هر پنجره جدید `cmd` به‌طور خودکار اجرا شود:

```
[HKEY_CURRENT_USER\Software\Microsoft\Command Processor]
"AutoRun"="D:\\MyPrograms\\cmd\\cbox.cmd"
```

| گام | دستور |
| --- | --- |
| ۱. ویرایش مسیر داخل `reginit.reg` | — |
| ۲. اعمال تنظیمات | `reg import .\reginit.reg` |
| ۳. بازگردانی | `reg delete "HKCU\Software\Microsoft\Command Processor" /v AutoRun /f` |

---

### نکات فنی

- **عبور به‌عنوان طراحی اصلی.** هر دو پوسته ورودی‌های ناشناخته را از طریق شل سیستم
  اجرا می‌کنند. این روش راحت است، اما به این معنا نیز هست که هر رشته‌ای که پوسته بپذیرد،
  یک دستور معتبر است. `cbox.cmd` و `cbox.py` را ابزار تعاملی بدانید، نه یک محیط ایزوله.
- **خطر تزریق شل.** در `cbox.py` آرگومان‌ها مستقیماً در رشته‌های دستور شل قرار می‌گیرند
  (`f'dir "{path}"'`). مسیرهایی که شامل کاراکترهای ویژه شل دارند می‌توانند دستور را خراب
  کنند. برای ورودی‌های غیرقابل اعتماد از ابزارهای اختصاصی پایتون (`cdir.py`، `cpi.py`)
  استفاده کنید.
- **مدیریت پروسه.** `cbox.py` یک ارجاع به پروسه فرزند در حال اجرا نگه می‌دارد تا
  `Ctrl+C` آن را متوقف کند و پروسه یتیم رها نشود.
- **خروجی رنگی.** `cbox.py` و `cbox.cmd` کدهای ANSI خام چاپ می‌کنند. `cdir.py` از
  نشانه‌گذاری Rich و بقیه ابزارها از Colorama استفاده می‌کنند. در صورت هدایت خروجی به
  فایل، کدهای رنگ نیز در فایل ذخیره می‌شوند.
- **APIهای منسوخ.** دستور `df` در هر دو پوسته و دستور `ver` به `wmic` و `systeminfo`
  وابسته هستند که در نسخه‌های اخیر ویندوز در حال کنار گذاشته شده‌اند. در صورت عدم کارکرد،
  از `Get-Volume` در پاورشل استفاده کنید.
- **درخواست بدون TLS.** `cro.py` به `http://ip-api.com` بدون رمزنگاری درخواست می‌دهد.
- **تغییرات رجیستری دائمی هستند.** `reginit.reg` تنظیمات Command Processor کاربر جاری را
  تغییر می‌دهد. اگر آن را نمی‌خواهید، با دستور `reg delete` آن را حذف کنید.
- **`requirements.txt` وجود ندارد.** فهرست وابستگی‌ها در همین README آمده است. اضافه
  کردن این فایل پیشنهاد می‌شود.

---

### سلب مسئولیت

برای استفاده آموزشی و اداری روی سامانه‌هایی که در اختیار دارید یا مجاز به آزمون آن‌ها
هستید. داده‌های Geo-IP از سرویس رایگان `ip-api.com` و داده‌های WHOIS از سرورهای عمومی
WHOIS می‌آید. قوانین محلی و شرایط استفاده این سرویس‌ها را رعایت کنید.

---

### مجوز

تحت مجوز MIT منتشر شده است.

---

<div align="center">

**CBOX** — ساخته‌شده توسط FOXNET Group

</div>