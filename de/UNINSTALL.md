# Deinstallation

Diese Anleitung zeigt dir verschiedene Wege, BridgePatcher und/oder die Patches zu deinstallieren.

## Alles löschen und zu nativem macOS zurückkehren

1. Erstelle einen USB-Stick mit dem neuesten offiziell unterstützten macOS-Installer oder verwende alternativ [auf den meisten Macs](https://apple.stackexchange.com/questions/383985/which-macs-support-macos-internet-recovery) die Internet-Wiederherstellung.
   * Halte `cmd` + `Option (Alt)` + `R` für die Internet-Wiederherstellung.
   * Wenn du die Internet-Wiederherstellung nutzt, überspringe Schritt 2.
   * Achtung: Die Internet-Wiederherstellung installiert nicht immer die neueste offiziell unterstützte macOS-Version.
3. Starte neu und boote den Computer vom Installer-USB-Stick, indem du `Option (Alt)` gedrückt hältst.
4. Öffne das Festplattendienstprogramm und wähle Darstellung -> Alle Geräte einblenden.
5. Lösche die gesamte Festplatte, indem du in der linken Seitenleiste den obersten Eintrag des Laufwerks auswählst und auf „Löschen“ klickst.
6. Starte die macOS-Installation.
7. Wenn sie abgeschlossen ist, starte noch einmal neu und [setze den NVRAM zurück](https://support.apple.com/HT204063), um ein vollständig sauberes Originalsystem zu erhalten.


## Manuelle Methoden

Die manuelle Deinstallation von BridgePatcher besteht aus drei Teilen: der Anwendung, OpenCore und den Root-Patches. Wenn du BridgePatcher und die Patches vollständig entfernen möchtest, arbeite alle drei nacheinander ab. Andernfalls erledige nur die Teile, die du brauchst.

### Root-Patches entfernen

Öffne die BridgePatcher-Anwendung, gehe in das Menü „Post Install Root Patch“ und wähle „Revert Root Patches“.

*  **Unterstützt ab Monterey. Big Sur unterstützt das Zurücksetzen von Snapshots nicht und erfordert eine Neuinstallation. Diese kann ohne Löschen erfolgen, wenn die verwendete macOS-Installer-Version gleich oder neuer ist.**

### Die Anwendung deinstallieren

Um die BridgePatcher-Anwendung einschließlich LaunchAgent und PrivilegedHelperTool zu deinstallieren, lade das Deinstallationspaket von [der Releases-Seite](https://github.com/bridgepatcher/BridgePatcher/releases) herunter.

### Den Bootloader deinstallieren

1. Entferne OpenCore entweder vom USB-Stick oder vom internen Laufwerk

  * Hänge die EFI-Partition des Laufwerks ein und lösche die Ordner `EFI/OC` und `System`
    * Hinweis: Lösche **nicht** den gesamten EFI-Ordner – dadurch würden sehr wahrscheinlich bestehende Windows- und Linux-Installationen unbrauchbar.
    * [Hier findest du ein Beispiel zum Einhängen](https://dortania.github.io/OpenCore-Post-Install/universal/oc2hdd.html)
    * Nutzer eines 5K-iMac löschen zusätzlich `boot.efi` im Stammverzeichnis der EFI-Partition.

2. [Setze den NVRAM zurück](https://support.apple.com/HT204063)

:::warning Warnung

Beachte, dass dein Mac nach dem Entfernen von OpenCore nicht mehr startet und das „Verboten“-Symbol anzeigt. Halte einen bootfähigen USB-Stick mit OpenCore oder einer nativ unterstützten macOS-Version bereit, bevor du den Bootloader deinstallierst.

* Das gilt nicht für nativ unterstützte Macs, die OpenCore nur für Funktionen wie AirPlay zum Mac und Sidecar nutzen. Trotzdem wird empfohlen, macOS nach dem Entfernen von OpenCore neu zu installieren, wenn SMBIOS-Spoofing verwendet wurde, um die universelle Steuerung und andere Funktionen zu aktivieren.
:::
