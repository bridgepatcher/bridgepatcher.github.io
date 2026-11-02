# Eigene Symbole für OpenCore und den Mac-Bootpicker erstellen

Für alle, die ihr Setup persönlicher gestalten möchten, erlaubt OpenCore eigene Symbole und Bilder im Bootpicker.

* [Eigene OpenCore-Symbole](#eigene-opencore-symbole)
* [Eigene Symbole für den Mac-Bootpicker](#eigene-symbole-fur-den-mac-bootpicker)
* [Aktualisierte Symbole installieren](#aktualisierte-symbole-installieren)

# Eigene OpenCore-Symbole

Um eigene OpenCore-Symbole zu erzeugen, brauchst du Folgendes:

* Bilder im PNG-Format
* Jedes Bild in der folgenden Auflösung:
  * Cursor — Mauszeiger (Pflicht, bis 144x144).
  * Selected — Ausgewähltes Element (Pflicht, 144x144).
  * Selector — Auswahlrahmen (Pflicht, bis 144x40).
  * Left — Nach links scrollen (Pflicht, 40x40).
  * Right — Nach rechts scrollen (Pflicht, 40x40).
  * HardDrive — Allgemeines Betriebssystem (Pflicht, 128x128).
  * Background — Zentriertes Hintergrundbild (empfohlene Maximalgröße 1920x1080).
  * Apple — Apple-Betriebssystem (128x128).
  * AppleRecv — Apple-Wiederherstellung (128x128).
  * AppleTM — Apple Time Machine (128x128).
  * Windows — Windows (128x128).
  * Other — Eigener Eintrag (siehe [Entries](https://dortania.github.io/docs/latest/Configuration.html), 128x128).
  * ResetNVRAM — Systemaktion oder Werkzeug zum Zurücksetzen des NVRAM (128x128).
  * Shell — Eintrag mit UEFI-Shell-Namen, z. B. OpenShell (128x128).
  * Tool — Jedes andere Werkzeug (128x128).

Wir empfehlen, für jedes Bild zusätzlich eine Version in doppelter Größe bereitzuhalten. So werden die Symbole korrekt skaliert, da .icns eigene Bilder für HiDPI und Nicht-HiDPI unterstützt.

Sobald du ein eigenes Bild hast, das du verwenden möchtest (zum Beispiel als Hintergrund), lade das [neueste Release von OpenCorePkg](https://github.com/acidanthera/OpenCorePkg/releases) herunter und öffne den Ordner `Utilities/icnspack/`:

![](../images/icnspack-folder.png)

*Screenshot: Dokumentation von Dortanias OpenCore Legacy Patcher, Ordner- und Benutzernamen geändert.*

Wechsle nun im Terminal mit `cd` in diesen Ordner und führe Folgendes aus:

```sh
./icnspack Background.icns <insert_x1_image> <insert_x2_image>
```

Danach findest du dein erzeugtes Symbol im Ordner von `icnspack`:

![](../images/icnspack-done.png)

*Screenshot: Dokumentation von Dortanias OpenCore Legacy Patcher, Ordner- und Benutzernamen geändert.*

# Eigene Symbole für den Mac-Bootpicker

Eigene Bootpicker-Symbole sind auf älteren Macs deutlich komplizierter. Auf Macs ab Ende 2013 funktioniert die Methode unter [Eigene OpenCore-Symbole](#eigene-opencore-symbole) problemlos. Auf vielen Macs von 2012 und älter sind die so erzeugten Symbole jedoch nicht mit der Firmware kompatibel.

Um Symbole für ältere Macs zu erzeugen, brauchst du Folgendes:

* Einen Rechner mit macOS 10.4 bis 10.11
* Icon Composer.app (für den offiziellen Download ist ein Apple-Developer-Konto nötig)
* Das PNG-Bild, das du umwandeln möchtest

Öffne die Seite [More Downloads auf developer.apple.com](https://developer.apple.com/download/more/) und suche nach `Graphics Tools` in einer Version, die dein Betriebssystem unterstützt (bei 10.6 und älter steckt die App in den `Developer Tools`):

![](../images/graphics-download.png)

Öffne nach dem Download das Disk-Image, dort findest du Icon Composer.app:

![Graphics öffnen](../images/graphics-open.png)

Starte jetzt die App und ziehe die Bilder einfach in die jeweiligen Bereiche:

![](../images/icon-SL.png)

Speichere und exportiere anschließend die neue icns-Datei.

# Aktualisierte Symbole installieren

Stelle vor der Installation sicher, dass Vault beim Erstellen von OpenCore deaktiviert war. Wenn du unsicher bist, erstelle OpenCore einfach neu und setze dabei die Patcher-Einstellung „Vault“ auf „false“.

* <span style="color:red"> Warnung</span>: Fehlerhafte Änderungen an deinem OpenCore-EFI können die Installation unbrauchbar machen. Stelle sicher, dass eine nativ unterstützte macOS-Version installiert ist, in die du bei Problemen booten kannst.

Nachdem du sichergestellt hast, dass du OpenCore gefahrlos bearbeiten kannst, musst du das Laufwerk einhängen, auf dem OpenCore liegt. Lade dazu [MountEFI](https://github.com/corpnewt/MountEFI) herunter und starte es:

![](../images/mountefi.png)

Wähle das Laufwerk aus, auf dem du OpenCore installiert hast, und hänge es ein.

* [OpenCore-Symbole aktualisieren](#opencore-symbole-aktualisieren)
* [Mac-Bootpicker-Symbole aktualisieren](#mac-bootpicker-symbole-aktualisieren)

### OpenCore-Symbole aktualisieren

Öffne auf deinem Laufwerk `EFI/OC/Resources/Image/`, dort siehst du alle eigenen Symbole. Bei Background.icns müssen wir sicherstellen, dass die Datei zum in OpenCore eingestellten Theme passt, daher fügen wir das Präfix `Modern` hinzu:

![](../images/background-moved.png)

Starte jetzt neu, und du solltest deine aktualisierten Symbole sehen!

### Mac-Bootpicker-Symbole aktualisieren

Die Symbole des Mac-Bootpickers zu aktualisieren ist eigentlich ganz einfach. Lege das Symbol unter dem Namen `.VolumeIcon.icns` im Stammverzeichnis deines Laufwerks ab:

![](../images/mac-icns-drive.png)

*Screenshot: Dokumentation von Dortanias OpenCore Legacy Patcher, Ordner- und Benutzernamen geändert.*

Starte jetzt neu, und du siehst das neue Symbol!
