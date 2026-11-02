# Windows im UEFI-Modus installieren

Moderne Windows-Versionen unterstützen offiziell zwei Arten von Firmware: UEFI und BIOS. Wer Windows über den BridgePatcher-Bootpicker starten möchte, sollte wissen, dass dort nur UEFI-Installationen von Windows angezeigt werden.
Viele ältere Macs unterstützen UEFI-Installationen von Windows nicht „offiziell“, was zu fehlgeschlagenen Installationen und seltsamem Verhalten führt. Mit BridgePatcher lassen sich jedoch fast alle dieser Probleme vermeiden.

::: warning Warnung

Wenn du Windows über OpenCore startest, wird dringend empfohlen, im Festplattendienstprogramm eine neue 200-MB-Partition im Format **MS-DOS (FAT)** anzulegen und OpenCore dort zu installieren. So verhinderst du, dass Windows OpenCore in der EFI-Partition durch seinen eigenen Bootloader überschreibt und Startprobleme verursacht.

:::


## Mindestanforderungen

Diese Anleitung behandelt die Installation eines modernen Windows (10/11) ohne Boot-Camp-Assistent.

* Aufgrund von Hardware- und Firmware-Einschränkungen werden UEFI-Installationen von Windows nur auf den folgenden Geräten empfohlen:

  * MacBook 2015 oder neuer (`MacBook8,x`+)
  * MacBook Air 2011 oder neuer (`MacBookAir4,x`+)
  * MacBook Pro 2011 oder neuer (`MacBookPro8,x`+)
  * Mac mini 2011 oder neuer (`Macmini5,x`+)
  * Mac Pro 2009* oder neuer (`MacPro4,1`+), aufgerüstete GPU empfohlen
  * iMac 2010 oder neuer (`iMac11,x`+), aufgerüstete GPU empfohlen
  * Xserve 2009* (`Xserve3,1`), aufgerüstete GPU empfohlen


*Auf `MacPro4,1`, `MacPro5,1` und `Xserve3,1` gibt es Probleme mit dem Windows-Installer – folge in diesem Fall den Anweisungen im Abschnitt zur DISM-Installation.

Wenn dein Gerät nicht aufgeführt ist, lässt sich UEFI-Windows wahrscheinlich trotzdem installieren, du musst aber mit Stabilitäts- oder Treiberproblemen rechnen.

## Partitionieren und Formatieren

Für die Installation brauchst du:
* Einen USB-Stick mit mindestens 8 GB für den Windows-Installer
* Mindestens 30 GB freien Speicher auf einem vorhandenen oder leeren Laufwerk für die Windows-Installation

### USB-Stick formatieren

Öffne in macOS das Festplattendienstprogramm und formatiere den USB-Stick als ExFAT mit dem Schema „Master Boot Record“:

![](../images/windows-mbr-format.png)

### Ziellaufwerk formatieren

Wähle anschließend im Festplattendienstprogramm das Laufwerk aus, auf dem Windows installiert werden soll, und lege eine ExFAT-Partition an (wenn du das gesamte Laufwerk formatierst, achte auf das Schema „GUID-Partitionstabelle“):

![](../images/windows-partition-1.png)


:::warning Warnung

Wenn du das falsche Laufwerk löschst, kann das zu Datenverlust führen! Prüfe bitte genau, ob du das richtige Laufwerk bzw. die richtige Partition löschst.

:::

Wenn du dasselbe Laufwerk für macOS und Windows nutzen möchtest, empfehlen wir eine eigene Partition nur für OpenCore. So hat Windows die ESP für sich allein, und OpenCore bleibt in seiner eigenen Blase.

Die empfohlene Größe beträgt 200 MB, und das Partitionsformat **muss** FAT32 sein, damit OpenCore korrekt funktioniert. Installiere OpenCore danach auf der neuen Partition – entweder, indem du es mit [MountEFI](https://github.com/corpnewt/MountEFI) aus der ESP verschiebst, oder indem du die BridgePatcher.app erneut ausführst.

* Hinweis 1: Bei Geräten mit einem eigenen Laufwerk für Windows ist eine separate OpenCore-Partition nicht nötig.
* Hinweis 2: Eine separate OpenCore-Partition ist auch nicht nötig, wenn die Windows-Bootdateien entfernt werden, die der Standard-Bootpicker erkennt. Mehr dazu unter „Windows-Option aus dem Standard-Bootpicker entfernen“.
* Hinweis 3: Wir empfehlen, OpenCore von der ESP/EFI-Partition zu deinstallieren, wenn du die neue OpenCore-Partition anlegst, um Verwechslungen bei der Auswahl von OpenCore-Builds im Bootpicker des Macs zu vermeiden.

![](../images/windows-partition-2.png)

## Windows-Installer erstellen

Die neuesten Windows-Installationsabbilder kannst du über die folgenden Links bei Microsoft herunterladen:

* [Windows-10-Datenträgerabbild (ISO-Datei) herunterladen](https://www.microsoft.com/de-de/software-download/windows10ISO)

* [Windows-11-Datenträgerabbild (ISO-Datei) herunterladen](https://www.microsoft.com/de-de/software-download/windows11)

Hänge das .iso-Abbild nach dem Download ein:

![](../images/windows-iso.png)

Öffne dann das Terminal und verwende den Befehl `rsync` mit dem Abbild als Quelle und deinem USB-Stick als Ziel. (Ersetze „CCCOMA_X64“ durch den Partitionsnamen des eingehängten Abbilds und „InstallWin10“ durch den Namen deines USB-Sticks.)

```
rsync -r -P /Volumes/CCCOMA_X64/ /Volumes/InstallWin10
```

![](../images/rsync-progess.png)

Der Befehl `rsync` braucht eine Weile – hol dir also einen Kaffee und lehn dich zurück. Danach sollte das Stammverzeichnis des USB-Sticks so aussehen:

![](../images/windows-rsync-done.png)

*Screenshot: Dokumentation von Dortanias OpenCore Legacy Patcher, Ordner- und Benutzernamen geändert.*

* Stelle sicher, dass diese Ordner und Dateien im Stammverzeichnis des USB-Sticks liegen, sonst startet der Stick nicht.


## Installation

Nach dem Neustart solltest du im BridgePatcher-Bootpicker eine neue Bootoption mit der Bezeichnung „EFI Boot“ oder „Windows“ sehen. Sie hat möglicherweise das Boot-Camp-Symbol.

:::warning Warnung

Wenn du nicht über BridgePatcher gebootet hast, siehst du eventuell **zwei** Bootoptionen namens „Windows“ und „EFI Boot“. Wähle keine davon, sondern boote BridgePatcher, um fortzufahren.

:::



### Installation: Microsoft-Methode

Sobald du in den Windows-Installer gebootet hast, gehst du wie auf jedem anderen Windows-Computer vor. Wenn eine Fehlermeldung wie „Windows konnte den Computer nicht für den Start in der nächsten Installationsphase vorbereiten“ erscheint, folge bitte dem nächsten Teil dieser Anleitung (DISM-Installation).

::: details Windows 11 installieren

Wenn du Windows 11 installierst, musst du [das Windows-Setup anpassen](https://www.bleepingcomputer.com/news/microsoft/how-to-bypass-the-windows-11-tpm-20-requirement/), damit die Installation auf nicht unterstützten Geräten möglich ist.

:::

### Installation: DISM-Methode

Sobald du in den Windows-Installer gebootet hast, gehst du wie gewohnt vor, bis du zum Abschnitt „Wo möchten Sie Windows installieren?“ zum Formatieren des Laufwerks kommst.

Wenn du ein Laufwerk auswählen sollst, markiere die gewünschte Partition und lösche sie mit „Löschen“. Wenn du Windows auf einem leeren Laufwerk installieren möchtest, lösche alle Partitionen auf diesem Laufwerk.
Nachdem das Laufwerk bzw. die Partition gelöscht ist, klicke auf „Neu“, um die Windows-Systempartitionen anzulegen.

![](../images/DISM-1.png)

Du wirst aufgefordert, das Anlegen der Systempartitionen zu bestätigen – klicke auf „OK“.

![](../images/DISM-2.png)

Sobald die Partitionen angelegt sind, wähle die Hauptpartition (die größte) und klicke auf „Formatieren“. Dadurch wird die Partition mit dem Dateisystem NTFS formatiert.

![](../images/DISM-3.png)

Nachdem der Installer die Partition formatiert hat, öffne mit UMSCHALT + F10 die Eingabeaufforderung. Führe dann den Befehl `diskpart` und anschließend `list vol` aus. Du erhältst eine Liste der Volumes in deinem System – merke dir die Laufwerksbuchstaben der Windows-Hauptpartition (die größte, NTFS), der EFI-Partition (100 MB, FAT32) und des Windows-Installers (meist Laufwerk D). Beende diskpart mit `exit`.

![](../images/DISM-4.png)

Lass dir nun mit `dism /Get-WimInfo /WimFile:D:\Sources\install.wim` die verfügbaren Windows-Editionen anzeigen (ersetze D durch den Laufwerksbuchstaben des Installers). In dieser Anleitung verwenden wir Option 6 für Windows 10 Pro.

![](../images/DISM-5.png)

Jetzt kannst du die Bereitstellung starten. Führe `dism /Apply-Image /ImageFile:D:\Sources\install.wim /index:6 /ApplyDir:E:` aus und ersetze dabei „D“ durch den Laufwerksbuchstaben des Installers, „6“ durch die Option der gewünschten Windows-Edition und „E“ durch den Laufwerksbuchstaben der Windows-Partition.

![](../images/DISM-6.png)

Wenn `dism` fertig ist, führe `bcdboot E:\Windows` aus und ersetze „E“ durch den Laufwerksbuchstaben der Windows-Hauptpartition, um die Bootdateien zu erstellen.

![](../images/DISM-7.png)

Windows ist jetzt installiert. Es sollte im BridgePatcher-Bootpicker als „EFI Boot“ oder „Windows“ mit Boot-Camp-Symbol erkannt werden.

:::warning Warnung

Starte nach dem Erstellen der Bootdateien auf einem MacPro4,1, MacPro5,1 oder Xserve3,1 **AUF KEINEN FALL** neu! Ein Fehler im Windows-Bootloader macht das System komplett unbrauchbar, wenn er über den Standard-Bootpicker geladen wird. Eine Lösung findest du im Abschnitt „Installation: Windows-Option aus dem Standard-Bootpicker entfernen“.

:::

### Installation: Windows-Option aus dem Standard-Bootpicker entfernen

Auf MacPro4,1, MacPro5,1 und Xserve3,1 wird **DRINGEND EMPFOHLEN**, die Windows-Bootoption aus dem Standard-Bootpicker zu entfernen, um eine Beschädigung des Secure-Boot-NVRAM und ein unbrauchbares System zu verhindern.

Öffne in der Windows-Setup-Umgebung mit `cmd` ein Eingabeaufforderungsfenster.

Wechsle dann mit `C:` in die EFI-Partition (ersetze „C“ durch den Laufwerksbuchstaben der EFI-Partition). Führe anschließend `cd EFI` aus, um in den EFI-Ordner zu wechseln. Führe dann `rmdir Boot /S /Q` aus, um die Bootdateien zu entfernen, die der Standard-Bootpicker erkennen kann. Der BridgePatcher-Bootpicker kann Windows weiterhin erkennen und starten.

![](../images/DISM-8.png)

Mit dem Befehl `dir` kannst du prüfen, ob der Ordner `Boot` entfernt wurde:

![](../images/DISM-9.png)

Falls du die Bootdateien aus irgendeinem Grund nicht im Windows-Setup entfernen kannst, fahre dein System herunter, boote macOS, hänge deine EFI-Partition mit [MountEFI](https://github.com/corpnewt/MountEFI) ein und entferne den Ordner `Boot` (er sollte ein aktuelles Änderungsdatum haben und `Bootx64.efi` enthalten).


## Nach der Installation

### Boot-Camp-Software installieren

Lade zunächst das Werkzeug Brigadier über den folgenden Link herunter:

* [Brigadier herunterladen](https://github.com/timsutton/brigadier/releases/download/0.2.4/brigadier.exe)

Verschiebe Brigadier nach dem Download auf deinen Desktop, damit du leicht darauf zugreifen kannst.

Öffne als normaler Benutzer ein Eingabeaufforderungsfenster und führe `cd desktop` aus.

![](../images/BOOTCAMP-1.png)

Führe dann `.\brigadier.exe --model=MODEL1,1` aus und ersetze „MODEL1,1“ durch das SMBIOS-Modell deines Geräts.

![](../images/BOOTCAMP-2.png)

Sobald die Boot-Camp-Software heruntergeladen ist, kannst du sie installieren, indem du `Setup.exe` oder `\Drivers\Apple\BootCamp.msi` (bzw. `BootCamp64.msi`, falls vorhanden) ausführst.

### Boot-Camp-6-Software auf nicht unterstützten Geräten installieren

Lade zunächst das Werkzeug Brigadier über den folgenden Link herunter:

* [Brigadier herunterladen](https://github.com/timsutton/brigadier/releases/download/0.2.4/brigadier.exe)

Verschiebe Brigadier nach dem Download auf deinen Desktop, damit du leicht darauf zugreifen kannst.

Öffne als normaler Benutzer ein Eingabeaufforderungsfenster und führe `cd desktop` aus.

![](../images/BOOTCAMP-1.png)

Führe dann `.\brigadier.exe --model=MacPro7,1` aus. Dadurch wird das neueste Boot-Camp-6-Paket heruntergeladen.

![](../images/BOOTCAMP-2.png)

Sobald die Boot-Camp-Software heruntergeladen ist, kannst du Boot Camp 6 installieren, indem du `\Drivers\Apple\BootCamp.msi` in einer Eingabeaufforderung mit Administratorrechten ausführst.

## Fehlerbehebung

### „Diese Version von Boot Camp ist nicht für dieses Computermodell vorgesehen.“

Wenn du OpenCore mit SMBIOS-Spoofing der Stufe „Moderate“ oder höher erstellt hast, erhältst du beim Installieren der Boot-Camp-Treiber eine Fehlermeldung. Du kannst das lösen, indem du OpenCore mit einer niedrigeren Spoofing-Stufe neu erstellst oder den Installer über `Drivers/Apple/BootCamp.msi` startest.

| Setup.exe | BootCamp.msi |
| :--- | :--- |
| ![](../images/windows-bootcamp-error.png) | ![](../images/windows-bootcamp-msi.png) |

::: details Besonderheiten von BootCamp.msi

Bei Bedarf kannst du es als Administrator über die Befehlszeile starten:

```
set __COMPAT_LAYER=WIN7RTM && start \path\to\BootCamp\Drivers\Apple\Bootcamp.msi'
```

Ersetze dabei `\path\to` durch den Speicherort des Boot-Camp-Ordners.

Wenn du Boot-Camp-4.0-Treiber hast, kannst du auch in den `Eigenschaften` der Datei die Kompatibilität auf `Vorherige Windows-Version` setzen (der obige Befehl erledigt das bereits).

:::

### Bluescreen auf iMac12,x nach der Treiberinstallation

Intels iGPU-Treiber für die HD-3000-Serie unterstützen das Booten von Windows im UEFI-Modus nicht. Die empfohlene Lösung ist, die iGPU einfach zu deaktivieren: [iMac 12,1 Windows 10 Boot Loop – Fix Intel Graphics issue](https://zzq.org/?p=39)

### Schwarzer Bildschirm mit NVIDIA Tesla nach der Treiberinstallation

Die NVIDIA-Tesla-GPUs in Macs von 2008 bis 2010 unterstützen das Booten von Windows im UEFI-Modus nicht. Ohne Low-Level-Patches kannst du UEFI-Windows auf diesen Geräten nicht nutzen.
