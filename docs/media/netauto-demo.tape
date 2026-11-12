# Record the NetAuto demo from the repository root:
#   vhs docs/media/netauto-demo.tape
#
# Requires vhs, ttyd, ffmpeg, and python3 on PATH. In a container, set
# VHS_NO_SANDBOX=1 if Chrome cannot start its sandbox.
#
# The Hide block sources docs/media/pace.sh, which cds into
# network-automation-project and paces stdout. The typed commands and the
# text on screen are a real `python netauto.py --demo` session. pace_lines.py
# does not change the output, it only releases lines slowly enough to read.
# Demo backups and logs are written under network-automation-project/ and are
# gitignored; delete them after a re-record if they are still on disk.

Output docs/media/netauto-demo.gif
Output docs/media/netauto-demo.mp4

Require python3

Set Shell bash
Set Theme "Catppuccin Mocha"
Set FontFamily "JetBrains Mono"
Set FontSize 18
Set LineHeight 1.15
Set Width 1200
Set Height 620
Set Padding 16
Set Framerate 12
Set PlaybackSpeed 1.0
Set TypingSpeed 42ms
Set WaitTimeout 45s
Set CursorBlink false
Set WindowBar Colorful
Set WindowBarSize 34
Set BorderRadius 8

Hide
Type "source docs/media/pace.sh"
Enter
Wait+Line@15s /network-automation-project \$/
Type "clear"
Enter
Wait+Line@8s /network-automation-project \$/
Show

Sleep 700ms
Type "python netauto.py --demo"
Enter
Sleep 600ms
Wait+Line@50s /network-automation-project \$/
Sleep 900ms

Type "clear"
Enter
Wait+Line@8s /network-automation-project \$/
Sleep 300ms

Type "python netauto.py --demo --interactive"
Enter
Wait+Line@25s /^Select a device number:$/
Sleep 1000ms
Type "1"
Enter
Wait+Line@20s /^Select an option:$/
Sleep 800ms
Type "2"
Enter
Sleep 400ms
# Cursor has left the previous prompt. Wait until the menu is drawn again under the table.
Wait+Line@25s /^Select an option:$/
Sleep 700ms
Type "0"
Enter
Sleep 400ms
Wait+Line@20s /network-automation-project \$/
Sleep 1200ms
