# Probleme beim Booten, mit dem Installer und Sonstiges

#### Booten

* [Hängt bei `This version of Mac OS X is not supported on this platform` oder beim (🚫) Verboten-Symbol](#hangt-bei-this-version-of-mac-os-x-is-not-supported-on-this-platform-oder-beim-🚫-verboten-symbol)
* [macOS bootet nicht ohne den USB-Stick](#macos-bootet-nicht-ohne-den-usb-stick)
* [Endlosschleife beim Booten in die Recovery](#endlosschleife-beim-booten-in-die-recovery)
* [Hängt beim Booten nach dem Root-Patching](#hangt-beim-booten-nach-dem-root-patching)
* [Recovery über BridgePatcher booten](#recovery-uber-bridgepatcher-booten)
* [Schwarzer Bildschirm auf dem MacBookPro11,3 unter macOS Monterey](#schwarzer-bildschirm-auf-dem-macbookpro11-3-unter-macos-monterey)

#### Installer

* [Hängt bei der Laufwerksauswahl mit ausgegrauten Schaltflächen im Installer](#hangt-bei-der-laufwerksauswahl-mit-ausgegrauten-schaltflachen-im-installer)
* [Installer schlägt mit „an error occurred preparing the software update“ fehl](#installer-schlagt-mit-„an-error-occurred-preparing-the-software-update-fehl)
* [Hängt bei „Weniger als eine Minute verbleibend …“](#hangt-bei-„weniger-als-eine-minute-verbleibend)
* [Hängt bei „Your Mac needs a firmware update“](#hangt-bei-„your-mac-needs-a-firmware-update)

#### Sonstiges

* [Neustart beim Wechsel in den Ruhezustand (`Sleep Wake Failure`)](#neustart-beim-wechsel-in-den-ruhezustand-sleep-wake-failure)
* [Fehler „Volume Hash Mismatch“ unter macOS Monterey](#fehler-„volume-hash-mismatch-unter-macos-monterey)
* [SIP lässt sich in recoveryOS nicht deaktivieren](#sip-lasst-sich-in-recoveryos-nicht-deaktivieren)


## Hängt bei `This version of Mac OS X is not supported on this platform` oder beim (🚫) Verboten-Symbol

Das bedeutet, dass macOS ein SMBIOS erkannt hat, das es nicht unterstützt. Um das zu beheben, stelle sicher, dass du im Bootpicker OpenCore **vor** dem macOS-Installer bootest. Zur Erinnerung: Die Option heißt `EFI Boot`.

Sobald du OpenCore mindestens einmal gebootet hast, sollte deine Hardware es automatisch booten, bis entweder ein NVRAM-Reset erfolgt oder du das Laufwerk mit OpenCore entfernst.

Erscheint das 🚫-Symbol jedoch erst, nachdem der Bootvorgang bereits begonnen hat (der Startbildschirm erscheint bzw. der Verbose-Boot startet), hat dein USB-Stick möglicherweise die Integritätsprüfungen von macOS nicht bestanden. Erstelle in diesem Fall einen neuen Installer auf einem anderen USB-Stick (am besten eines anderen Modells).

## macOS bootet nicht ohne den USB-Stick

Standardmäßig installiert BridgePatcher OpenCore während der Installation nicht selbst auf dem internen Laufwerk.

Nach der Installation von macOS sollte BridgePatcher dich automatisch auffordern, OpenCore auf dem internen Laufwerk zu installieren. Erscheint diese Aufforderung nicht, musst du OpenCore entweder [manuell](https://dortania.github.io/OpenCore-Post-Install/universal/oc2hdd.html) auf die EFI des internen Laufwerks übertragen oder erneut „Build and Install“ ausführen und dein internes Laufwerk auswählen.

Denk daran, dass du OpenCore danach noch einmal im Bootpicker auswählen musst, damit sich deine Hardware diesen Eintrag merkt und ab dann automatisch davon bootet.

## Endlosschleife beim Booten in die Recovery

Mit BridgePatcher nutzen wir Apple Secure Boot, damit Betriebssystem-Updates unter Big Sur korrekt und zuverlässig funktionieren. Dabei werden allerdings NVRAM-Variablen gesetzt, die deinen Mac verwirren, wenn er ohne OpenCore läuft. Um das zu beheben, deinstalliere einfach OpenCore und [setze den NVRAM zurück](https://support.apple.com/de-de/HT201255).

* Hinweis: Auch Geräte mit verändertem Root-Volume landen in einer endlosen Recovery-Schleife, bis die Integrität wiederhergestellt ist.

## Hängt beim Booten nach dem Root-Patching

**Gilt für macOS Monterey und neuer. Big Sur unterstützt das Zurücksetzen von Snapshots nicht.**

Boote in die Recovery, indem du die Leertaste drückst, während dein Laufwerk im BridgePatcher-Bootpicker ausgewählt ist (falls du den Bootpicker ausgeblendet hast, halte beim Start ESC gedrückt).

* **Hinweis:** Wenn dein Laufwerk nicht „Macintosh HD“ heißt, passe den Pfad entsprechend an. Den Namen deines Laufwerks findest du mit `ls /Volumes` heraus.

Öffne das Terminal und hänge zuerst das Laufwerk ein:
```sh
mount -uw "/Volumes/Macintosh HD"
```
Setze dann den Snapshot zurück:
```sh
bless --mount "/Volumes/Macintosh HD" --bootefi --last-sealed-snapshot
```
Jetzt bereinigen wir den Ordner /Library/Extensions von störenden Kexts und behalten die benötigten.

Führe Folgendes aus und **tippe es sorgfältig ab**:

::: warning Achtung
Wenn du **FileVault 2 aktiviert** hast, musst du zuerst das Datenvolume einhängen. Das geht im Festplattendienstprogramm: Suche dein macOS-Volume, wähle das zugehörige Datenvolume („- Data“) aus und klicke in der Symbolleiste auf „Aktivieren“.
:::

```sh
cd "/Volumes/Macintosh HD - Data/Library/Extensions" && ls | grep -v "HighPoint*\|SoftRAID*" | xargs rm -rf
```

Starte dann neu. Dein System sollte jetzt auf den ungepatchten Snapshot zurückgesetzt sein und wieder booten.

## Recovery über BridgePatcher booten

Wenn du mit der normalen Tastenkombination (cmd+R) in die Recovery bootest, erscheint ein „Verboten“-Bildschirm, da die Prüfungen einen nicht unterstützten Mac erkennen.

Um die Recovery zu erreichen, musst du sie über OpenCore im Bootpicker starten. Standardmäßig blendet der Patcher zusätzliche Bootoptionen wie die Recovery aus. Um sie anzuzeigen, drücke im Bootpicker von OpenCore die `Leertaste`; dann werden alle Bootoptionen aufgelistet, und du kannst die Recovery für die passende macOS-Version auswählen.

## Schwarzer Bildschirm auf dem MacBookPro11,3 unter macOS Monterey

Da Apple die Unterstützung für NVIDIA Kepler in macOS Monterey eingestellt hat, [hat der GMUX des MacBookPro11,3 Schwierigkeiten, zurück auf die iGPU zu wechseln, um macOS korrekt anzuzeigen.](https://github.com/dortania/OpenCore-Legacy-Patcher/issues/522) Um das zu umgehen, boote das MacBookPro11,3 im sicheren Modus und führe nach der Installation von macOS die Post-Install-Root-Patches von BridgePatcher aus, um die GPU-Beschleunigung für die dedizierte NVIDIA-GPU zu aktivieren.

* Den sicheren Modus startest du, indem du `Shift` + `Enter` gedrückt hältst, während du macOS Monterey im Bootmenü von BridgePatcher auswählst.

## Hängt bei der Laufwerksauswahl mit ausgegrauten Schaltflächen im Installer

Stelle die Sprache des Installers auf Englisch um. Erscheint die Sprachauswahl nicht, [setze den NVRAM zurück](https://support.apple.com/de-de/102603) und boote erneut in den Installer.

Nach der Installation von macOS kannst du wieder auf eine andere Sprache umstellen.

## Installer schlägt mit „an error occurred preparing the software update“ fehl

Dieses Problem kann in der zweiten Phase des Installers (schwarzer Hintergrund mit Apple-Logo) auftreten; die Ursache ist unbekannt. Möglicherweise hilft es, mehrmals hintereinander in „macOS Installer“ (die zweite Phase) neu zu booten, bis es schließlich durchläuft.

## Hängt bei „Weniger als eine Minute verbleibend …“

Hier scheinen Systeme häufig „hängen zu bleiben“, vor allem Geräte ohne den CPU-Befehl `AES` bzw. ältere mobile Hardware. In dieser Phase finden viele aufwendige kryptografische Berechnungen statt, wodurch das System festzuhängen scheint. Tatsächlich arbeitet es hart daran, die Installation abzuschließen.

Da dieser Schritt je nach Laufwerksgeschwindigkeit einige Stunden oder länger dauern kann, sei geduldig und schalte deinen Mac nicht manuell aus oder starte ihn neu – das macht die Installation kaputt, und du musst neu installieren. Wenn du glaubst, dass dein System hängt, drücke die Feststelltaste: Geht deren Lampe an, ist das System beschäftigt und nicht wirklich eingefroren.

## Hängt bei „Your Mac needs a firmware update“

Vollständige Fehlermeldung: „Your Mac needs a firmware update in order to install to this Volume. Please select a Mac OS Extended (Journaled) volume instead.“

Dieser Fehler tritt auf, wenn macOS feststellt, dass die aktuelle Firmware APFS nicht vollständig unterstützt. Um das zu beheben, öffne beim Installieren von OpenCore die „Patcher Settings“ und aktiviere „Moderate SMBIOS Patching“ oder höher. Dadurch meldet die Firmware volle APFS-Unterstützung.


## Neustart beim Wechsel in den Ruhezustand (`Sleep Wake Failure`)

[Bekanntes Problem bei einigen Modellen](https://github.com/dortania/Opencore-Legacy-Patcher/issues/72). Als vorübergehende Lösung kannst du den Ruhezustand (Hibernation) deaktivieren, indem du im Terminal folgenden Befehl ausführst:

```
sudo pmset -a hibernatemode 0
```

## Fehler „Volume Hash Mismatch“ unter macOS Monterey

Eine relativ häufige Meldung, die manche Nutzer sehen, ist der Fehler „Volume Hash Mismatch“:

<p align="left">
<img src="../images/Hash-Mismatch.png">
</p>

*Screenshot: Dokumentation von Dortanias OpenCore Legacy Patcher.*

Dieser Fehler bedeutet, dass das Betriebssystem erkennt, dass der Hash des Bootvolumes nicht dem erwarteten Wert entspricht. Er ist in der Regel rein kosmetisch und kann ignoriert werden. Stürzt dein System kurz danach jedoch spontan ab, solltest du macOS neu installieren und zunächst keine Daten importieren.

* Beachte, dass dieser Fehler auch nativ unterstützte Macs betrifft und nicht auf nicht unterstützte Macs zurückzuführen ist: [OSX Daily: “Volume Hash Mismatch” Error in MacOS Monterey](https://osxdaily.com/2021/11/10/volume-hash-mismatch-error-in-macos-monterey/)

Außerdem kann es helfen, FeatureUnlock unter Settings -> Misc Settings zu deaktivieren, da dieses Werkzeug Systeme mit weniger stabilem Arbeitsspeicher stark belasten kann.


## SIP lässt sich in recoveryOS nicht deaktivieren

Mit BridgePatcher überschreibt der Patcher beim Booten immer den aktuellen SIP-Wert, damit Nutzer ihre Installation nach einem NVRAM-Reset nicht unbrauchbar machen. Wer SIP vollständig deaktivieren will, kann das aber ganz einfach tun.

Öffne die Oberfläche, gehe zu den Patcher-Einstellungen und schalte die SIP-Bits aus, die du deaktivieren möchtest:

| SIP aktiviert | SIP gelockert (Root-Patching) | SIP deaktiviert |
| :--- | :--- | :--- |
| ![](../images/OCLP-GUI-Settings-SIP-Enabled.png) | ![](../images/OCLP-GUI-Settings-SIP-Root-Patch.png) | ![](../images/OCLP-GUI-Settings-SIP-Disabled.png) |
