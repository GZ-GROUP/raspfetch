# RASPFETCH

Administration tool for the Raspberry Pi. It shows system information, diagnoses the
connection to the local network and performs basic configuration from the terminal.

**Team:** [iangl2](https://github.com/iangl2), [RAGG1911](https://github.com/RAGG1911)

## Structure

| File | Content |
|---|---|
| `main.py` | Interactive menu (Textual text interface). Runs each action's script and shows its output in a pop-up. |
| `feature1.sh` … `feature10.sh` | One Bash script per action. Each one defines a function and runs it. |
| `common.sh` | Code shared by the scripts: translations and helper functions. |
| `i18n.py` | Translations for `main.py`. |
| `locales/*.lang` | Message catalogs, one per language (`en` English, `es` Spanish). |
| `requirements.txt` | Python dependencies for the menu. |

The scripts work on the **working directory**, which is the folder the tool is run from. It
must be inside the home directory (`$HOME`). The tool does not need `sudo`.

## How to run it

### 1. Install the dependencies (once)

On the Raspberry Pi, with Internet access:

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

The lab has no Internet access. In that case, download the packages on another computer
and copy them to the Raspberry Pi. They are pure Python packages, so they work on any
architecture:

```bash
# On a computer with Internet access
pip download -r requirements.txt -d packages
# On the Raspberry Pi, after copying the "packages" folder
python3 -m venv venv
venv/bin/pip install --no-index --find-links packages -r requirements.txt
```

### 2. Run

```bash
cd ~/sistemas-operativos
venv/bin/python main.py
```

| Key | Action |
|---|---|
| `↑` `↓` | Move through the menu |
| `Enter` | Run the selected action |
| `l` | Switch language (English / Spanish) |
| `Tab` | Move between fields inside a dialog |
| `Esc` | Close the result window or cancel a dialog |
| `q` or option **0. Exit** | Quit the tool |

Each script can also be run on its own:

```bash
bash feature5.sh 192.168.1.20              # connectivity test
bash feature8.sh my_folder                 # creates ./my_folder
bash feature9.sh test_file.txt read        # owner: read only
RASPFETCH_LANG=es bash feature1.sh         # output in Spanish
```

## Actions and commands

| # | Action | Script | Commands | What the commands do |
|---|---|---|---|---|
| 1 | System information | `feature1.sh` | `hostname`, `uname -r`, `uname -m`, `uptime -p`, `uptime -s` | Hostname, kernel version, architecture, uptime and boot time. |
| 2 | Memory check | `feature2.sh` | `free -m`, `free -h`, `awk` | Total, used and available RAM. `awk` extracts the values used to compute the percentage. |
| 3 | Storage check | `feature3.sh` | `df -hP /`, `df -h -x tmpfs …` | Usage of the root file system and of the other real file systems. |
| 4 | Network configuration | `feature4.sh` | `ip -br address`, `ip route` | Interfaces with their state and IP addresses, routes and the default gateway. |
| 5 | Connectivity test | `feature5.sh` | `ping -c 4 -W 2 <ip>` | Sends 4 packets to another host on the LAN, after checking that the IPv4 address is valid. |
| 6 | CPU temperature | `feature6.sh` | `vcgencmd measure_temp`, `/sys/class/thermal/thermal_zone0/temp` | Temperature in °C. If there is no sensor, the script says so. |
| 7 | Active processes | `feature7.sh` | `ps -eo pid,user,%cpu,%mem,comm --sort=-%cpu`, `/proc/loadavg` | Number of processes, load average and the processes using the most CPU and memory. |
| 8 | Create directory | `feature8.sh` | `mkdir`, `realpath`, `ls -ld` | Creates the folder inside the working directory. The parent folder is chosen in a tree. |
| 9 | File permissions | `feature9.sh` | `chmod u+r,u-w`, `chmod u+rw`, `ls -l`, `stat -c %a` | Sets the owner to read only or to read and write, then checks both permissions. |
| 10 | Diagnostic report | `feature10.sh` | `date`, `whoami`, `hostname` and scripts 1, 2, 3, 4 and 6 | Saves the summary to `diagnostic_report.txt`. |

## Input validation

- **Connectivity test:** rejects an empty IP address or one with a wrong format (for example `300.1.1.1`).
- **Create directory:** rejects empty names, names with spaces or special characters, `.` and `..`,
  folders that already exist and parent folders outside the working directory.
- **File permissions:** rejects folders, files outside the working directory, files owned by
  another user and any mode other than `read` or `readwrite`.
- Actions that create files or folders refuse to run outside `$HOME`.

## Permission test

Action 9 creates `test_file.txt` in the working directory if it does not exist yet, and
selects it by default. Another file can be picked in the tree.

1. Choose **Read only**: `ls -l` shows `-r--…`. The content can be read, but the attempt to
   append a line is reported as **DENIED**.
2. Choose **Read and write**: `ls -l` shows `-rw-…`. The tool appends a `Modified on …` line
   and shows the content as proof.

To check it by hand:

```bash
cat test_file.txt                  # read
echo "test" >> test_file.txt       # write: "Permission denied" when read only
```

For any other file the tool only checks the permission (`[ -w file ]`), so the content is
never modified.

## Translations (i18n)

Every message lives in `locales/<language>.lang`. Both the Bash scripts (`common.sh`) and
the menu (`i18n.py`) read these files:

```
# key=text   (%s = argument, %% = literal percent sign)
ping.reachable=Result: host %s REPLIES.
```

- The language is chosen with the `RASPFETCH_LANG` variable (`en` by default). Inside the
  menu, the `l` key switches it.
- Any key missing in a language falls back to English (`en.lang`).
- To add a language, copy `en.lang` to `locales/<code>.lang` and translate the text after `=`.
  The new language then appears automatically in the `l` key's rotation.
