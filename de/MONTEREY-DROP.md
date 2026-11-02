# macOS Monterey

![](../images/macos-monterey.png)

*Banner: Dokumentation von Dortanias OpenCore Legacy Patcher.*

Mit Dortanias OpenCore Legacy Patcher v0.1.7 und neuer hat Dortania eine Beta-Unterstützung für macOS Monterey implementiert. Beachte bitte, dass Apple mit diesem Release viel Hardware fallen gelassen und zudem viele von Dortanias bisherigen Patch-Sets unbrauchbar gemacht hat. Diese Seite informiert über aktuelle Probleme und wird aktualisiert, sobald neue Patch-Sets entwickelt und in den Patcher aufgenommen werden.

## Neu fallen gelassene Hardware

Mit Monterey setzt Apple seinen recht rücksichtslosen Kurs fort, Intel-Hardware fallen zu lassen. Mit diesem Release wurden folgende Modelle entfernt und damit in BridgePatcher aufgenommen:

* iMac14,4
* iMac15,1
* MacBook8,1
* MacBookAir6,1
* MacBookAir6,2
* MacBookPro11,1
* MacBookPro11,2
* MacBookPro11,3

::: details Modellnamen

* iMac (21,5 Zoll, Mitte 2014)
* iMac (Retina 5K, 27 Zoll, Ende 2014)
* MacBook (Retina, 12 Zoll, Anfang 2015)
* MacBook Air (11 Zoll, Mitte 2013)
* MacBook Air (13 Zoll, Mitte 2013)
* MacBook Air (11 Zoll, Anfang 2014)
* MacBook Air (13 Zoll, Anfang 2014)
* MacBook Pro (Retina, 13 Zoll, Ende 2013)
* MacBook Pro (Retina, 15 Zoll, Ende 2013)
* MacBook Pro (Retina, 13 Zoll, Mitte 2014)
* MacBook Pro (Retina, 15 Zoll, Mitte 2014)

:::

Alle diese Modelle werden jetzt von BridgePatcher unterstützt.

## Aktuelle Probleme unter Monterey

### Startproblem beim MacBookPro11,3 ohne Kepler-Beschleunigung

Da das Display über die NVIDIA-Kepler-Karte angebunden ist, macOS aber auf der Intel-iGPU gerendert wird, haben Nutzer Probleme beim Booten ohne angewendete Post-Install-Patches ([weitere Informationen hier](https://github.com/dortania/OpenCore-Legacy-Patcher/issues/522)). Derzeit besteht die einzige Lösung darin, die Patches im abgesicherten Modus zu installieren, indem du `Shift+Enter` gedrückt hältst, wenn du macOS im BridgePatcher-Bootpicker auswählst.

## Früher nicht funktionierende Hardware

::: details Problem mit der 5K-Displayausgabe beim iMac15,1 (behoben in Dortanias OpenCore Legacy Patcher 0.3.2 und neuer)

* Dokumentation:
  * [5K iMac and UEFI: Fixing the dreaded output limitation](https://khronokernel.github.io/macos/2021/12/08/5K-UEFI.html)
* Zugehöriges GitHub-Issue:
  * [5k Output issues on iMac15,1 (27" 5k iMac - 2014) #359](https://github.com/dortania/OpenCore-Legacy-Patcher/issues/359)

:::

::: details Problem mit macOS 12.0 Beta 4 auf Geräten von 2012 bis Anfang 2013 (behoben in Dortanias OpenCore Legacy Patcher 0.2.5 und neuer)

Unter macOS 12.0 Beta 4 hatten viele Ivy-Bridge-Macs Bluetooth-Probleme im Zusammenhang mit ihrem BCM20702-Chipsatz. Die genaue Ursache ist derzeit unbekannt, vermutlich handelt es sich aber um einen Fehler auf Apples Seite. Bis zur Behebung empfehlen wir ein Downgrade auf macOS 12.0 Beta 3:

* [12.0 Beta 3 (21A5284e) InstallAssistant (direkt)](https://swcdn.apple.com/content/downloads/02/08/071-63739-A_G5RYVW5JHT/dfz5gp3s0jm9vl7m30oewq141zkpv8edr8/InstallAssistant.pkg)
* [12.0 Beta 3 (21A5284e) InstallAssistant (archive.org)](https://archive.org/details/12.0-21a5284e-beta-3)

Eine vorübergehende Lösung ist, die Prozesse BlueTool und bluetoothd bei jedem Start neu zu starten. Beachte, dass das nicht bei allen Nutzern funktioniert:

```sh
sudo killall -9 BlueTool bluetoothd
```

:::

::: details WLAN-Unterstützung entfernt (behoben in Dortanias OpenCore Legacy Patcher 0.2.5 und neuer)

* Die WLAN-Chipsätze Broadcom BCM94328, BCM94322 und Atheros werden nicht mehr unterstützt

Folgende Modelle haben in macOS Monterey wegen ihres älteren WLAN-Chipsatzes die WLAN-Unterstützung verloren:

* iMac12,x und älter
* Macmini3,1 und älter
* MacBook5,x und älter
* MacBookAir2,1 und älter
* MacBookPro7,1 und älter
  * MacBookPro6,x ist ausgenommen
* MacPro5,1 und älter

Hinweis: BCM943224, BCM94331, BCM94360 und BCM943602 werden von BridgePatcher weiterhin vollständig unterstützt.

:::

::: details Bluetooth-Unterstützung entfernt (behoben in Dortanias OpenCore Legacy Patcher 0.2.5 und neuer)

* Die Bluetooth-Chipsätze BRCM2046 und BRCM2070 werden nicht mehr unterstützt

Folgende Modelle haben in macOS Monterey wegen ihres älteren Bluetooth-Chipsatzes die Bluetooth-Unterstützung verloren:

* iMac12,x und älter
* Macmini5,1 und älter
* MacBook7,1 und älter
* MacBookAir4,1 und älter
* MacBookPro8,1 und älter
* MacPro5,1 und älter

Hinweis: Native BRCM20702 und BRCM20703 werden von BridgePatcher weiterhin vollständig unterstützt.

::: details Entfernte Firmwares

Folgende Firmwares hat macOS Monterey entfernt (früher in IOBluetoothUSBDFU.kext enthalten):

* 2046_820F.dfu
* 2046_8210.dfu
* 2046_8213.dfu
* 2046_8215.dfu
* 2046_8216.dfu
* 2046_8217.dfu
* 2070_821A.dfu
* 2070_821B.dfu
* 2070_8218.dfu
* 20702_821D.dfu
* 20702_821F.dfu
* 20702_828A.dfu
* 20702_828B.dfu
* 20702_828C.dfu
* 20702_8281.dfu
* 20702_8286.dfu

:::

::: details iGPU-Beschleunigung bei Ivy Bridge (behoben in Dortanias OpenCore Legacy Patcher 0.1.7 und neuer)

* Intel-HD4000-iGPUs werden nicht mehr unterstützt

Diese Geräte benötigen unter Monterey Root-Volume-Patches, um Grafikbeschleunigung zu erhalten. BridgePatcher kann die Unterstützung wiederherstellen, wegen des Root-Patchings kann SIP jedoch nicht mehr aktiviert werden:

* Macmini6,x
* MacBookAir5,x
* MacBookPro9,x
* MacBookPro10,x

:::

::: details dGPU-Beschleunigung bei NVIDIA Kepler (behoben in Dortanias OpenCore Legacy Patcher 0.2.5 und neuer)

* NVIDIA-Kepler-dGPUs werden nicht mehr unterstützt

Diese Geräte benötigen unter Monterey Root-Volume-Patches, um Grafikbeschleunigung zu erhalten. BridgePatcher kann die Unterstützung wiederherstellen, wegen des Root-Patchings kann SIP jedoch nicht mehr aktiviert werden:

* MacBookPro9,1
* MacBookPro10,1
* MacBookPro11,3
* iMac13,x
* iMac14,x

:::

::: details Non-Metal-Beschleunigung (behoben in Dortanias OpenCore Legacy Patcher 0.2.5 und neuer)

* Für Non-Metal-GPUs gibt es keine funktionierenden Beschleunigungs-Patches mehr:
  * Intel-iGPUs Ironlake und Sandy Bridge
  * NVIDIA-GPUs Tesla und Fermi
  * AMD-GPUs TeraScale 1 und 2

Folgende Geräte erhalten unter Monterey überhaupt keine Grafikbeschleunigung, sondern nur einen einfachen Framebuffer und Helligkeitssteuerung (ausgenommen iMac8,1/9,1 und MacBook5,2):

* iMac12,x und älter
* Macmini5,x und älter
* MacBook7,1 und älter
* MacBookAir4,x und älter
* MacBookPro8,x und älter

Hinweis: iMac10,1 bis iMac12,x können mit Metal-GPUs aufgerüstet werden, [weitere Informationen hier](https://forums.macrumors.com/threads/2011-imac-graphics-card-upgrade.1596614/).

:::
