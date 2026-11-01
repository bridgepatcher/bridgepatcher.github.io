# Debuggen mit OpenCore

Wenn du auf einen seltsamen Fehler gestoßen bist und nicht sicher bist, ob es sich um einen Bedienfehler oder ein Problem im Patcher handelt, empfehlen wir, in unseren [GitHub Discussions](https://github.com/oclp-t2/BridgePatcher/discussions) um Hilfe zu bitten.

## Selbst debuggen

Am einfachsten debuggst du selbst über die Patcher-Einstellungen. Dort gibt es viele verschiedene Einstellungen, die drei wichtigsten Optionen sind jedoch:

* „Enable Verbose Mode“
* „Enable OpenCore DEBUG“
* „Enable Kext DEBUG“

<div align="left">
             <img src="../images/ocdebugimage.png" alt="BridgePatcher-Debug" width="600" />
</div>


Wenn du diese drei Optionen aktiviert hast, erstelle OpenCore neu und installiere es auf dein Laufwerk. Dadurch erhältst du deutlich mehr Debug-Informationen, und Logs werden auf die EFI-Partition geschrieben.

## OpenCore-Logs vom Laufwerk holen

Mit aktiviertem „Enable OpenCore DEBUG“ wird bei jedem Start eine .txt-Datei auf der EFI-Partition erzeugt. Um diese Logs zu holen, [lade MountEFI herunter und starte es](https://github.com/corpnewt/MountEFI):

<div align="left">
             <img src="../images/mountefi.png" alt="EFI einhängen" width="600" />
</div>

Sobald du die EFI-Partition des Laufwerks eingehängt hast, auf dem macOS installiert ist, solltest du dort die Logs finden:

<div align="left">
             <img src="../images/logs-efi.png" alt="EFI einhängen" width="800" />
</div>

## Kernel-Logs aus macOS holen

Mit aktiviertem „Enable Kext DEBUG“ werden bei jedem Start deutlich detailliertere Logs im Betriebssystem gespeichert. Um sie zu erhalten, führe einfach den folgenden Befehl aus:

```sh
sudo dmesg > ~/Desktop/DMESG.txt
```

Danach liegt das Log auf deinem Schreibtisch.

## Ein Issue bei uns melden

Jetzt, wo du aussagekräftige Logs hast, kannst du [ein Issue bei uns erstellen](https://github.com/oclp-t2/BridgePatcher/issues). Denk daran, folgende Informationen anzugeben:

* Modell, für das du patchst (z. B. MacBookPro10,1)
* Ziel-Betriebssystem (z. B. macOS 11.2.3)
* Host-Betriebssystem (z. B. macOS 10.15.7)
* Upload deines OpenCore-Build-Ordners
* Upload deines OpenCore-Logs (falls zutreffend)
* Upload deines Kernel-Logs (falls zutreffend)

Bitte suche außerdem vorher, ob das Problem bereits gemeldet wurde. So vermeiden wir doppelte Issues.
