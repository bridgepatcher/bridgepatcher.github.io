# macOS Sequoia

![](../images/macos-sequoia.png)

*Banner: Dokumentation von Dortanias OpenCore Legacy Patcher.*

Ein neues Jahr, ein neues Release.

Diesmal hat Apple überraschend wenige Macs fallen gelassen. Mit der Veröffentlichung von Dortanias OpenCore Legacy Patcher 2.0.0 wurde erste Unterstützung für macOS Sequoia implementiert.

::: info
BridgePatcher basiert auf Dortanias OpenCore Legacy Patcher. Versionsnummern wie 2.0.0 auf dieser Seite sind Versionen von Dortanias OpenCore Legacy Patcher, keine BridgePatcher-Versionen. Die eigenen Versionen von BridgePatcher beginnen bei 3.0.0 Alpha 4.1.
:::


## Neu fallen gelassene Hardware

* MacBookAir8,1 :       MacBook Air (2018)
* MacBookAir8,2 :       MacBook Air (2019)

## Aktueller Stand

Dortanias OpenCore Legacy Patcher 2.0.0 unterstützt Sequoia auf den unten aufgeführten Modellen, einige Herausforderungen bleiben jedoch bestehen. Informationen dazu findest du weiter unten auf dieser Seite.

<img width="625" alt="" src="../images/OCLP-200-Initial-Support.png">

*Banner: basiert auf der Dokumentation von Dortanias OpenCore Legacy Patcher, Modelle, Version und Symbol durch die von BridgePatcher ersetzt.*

Die T2-bezogene AppleKeyStore-Panic, die die kürzlich fallen gelassenen MacBookAir8,x-Modelle (und andere nicht unterstützte T2-Macs) am Booten über OpenCorePkg gehindert hat, wurde in BridgePatcher behoben. Die T2-Unterstützung befindet sich aber noch im Alpha-Stadium: Die Installation wird noch nicht abgeschlossen. Den aktuellen Stand findest du unten unter [T2-Sicherheitschip](#t2-sicherheitschip).

## Nicht funktionierende Funktionen

Auf den meisten gepatchten Macs funktionieren iPhone-Synchronisierung (iPhone Mirroring) und Apple Intelligence nicht.

iPhone Mirroring benötigt den T2 zur Attestierung und Apple Intelligence eine NPU, die es nur bei Apple Silicon gibt. Da es sich um Hardwareanforderungen handelt, kann der Patcher dafür keine Lösung bieten.

## Probleme

* [Dual-Socket-CPUs bei Mac Pros und Xserve](#dual-socket-cpus-bei-mac-pro-2008-und-xserve-2008)
* [T2-Sicherheitschip](#t2-sicherheitschip)
* [Unterstützung für USB 1.1 (OHCI/UHCI)](#unterstutzung-fur-usb-1-1-ohci-uhci)
* [Grafikunterstützung und Probleme](#grafikunterstutzung-und-probleme)


### Dual-Socket-CPUs bei Mac Pro 2008 und Xserve 2008

Das Booten von Sequoia auf einem Mac Pro 2008 (MacPro3,1) oder Xserve 2008 (Xserve2,1) mit mehr als 4 Kernen führt zu einer Kernel Panic. BridgePatcher deaktiviert die zusätzlichen Kerne automatisch.

Das liegt an der Dual-Socket-Bauweise dieser Geräte und wahrscheinlich an einer Inkompatibilität in Firmware bzw. ACPI-Tabellen.

**Wenn du OpenCore für ein älteres Betriebssystem erstellst, kann diese Einschränkung unter Settings -> Build -> „MacPro3,1/Xserve2,1 Workaround“ deaktiviert werden.**

::: warning Hinweis

Dual-Boot von Sequoia und älteren Versionen ist aus den oben genannten Gründen nicht mit allen aktivierten Kernen möglich. In diesem Fall bist du auf 4 Kerne beschränkt.

:::

### T2-Sicherheitschip

Das Booten von T2-Macs wie der MacBookAir8,x-Reihe (2018/19) über OpenCorePkg endete früher in einer Kernel Panic, weil AppleKeyStore.kext bei der Kommunikation mit dem T2-Chip in Timeouts lief:

```
"AppleKeyStore":3212:0: sks timeout strike 18
"AppleKeyStore":3212:0: sks timeout strike 19
"AppleKeyStore":3212:0: sks timeout strike 20
panic(cpu 0 caller 0xffffff801cd12509): "AppleSEPManager panic for "AppleKeyStore": sks request timeout" @AppleSEPManagerIntel.cpp:809
```

**Diese Panic tritt nicht mehr auf.** BridgePatcher kommt auf nicht unterstützten T2-Macs inzwischen an den AppleKeyStore-Timeouts vorbei, sodass die Geräte in den Installer booten.

Die T2-Unterstützung befindet sich jedoch noch im **Alpha**-Stadium. Das verbleibende Problem: Die macOS-Installation endet derzeit vor dem Abschluss mit „Failed to install a software update“. Wir können noch nicht abschätzen, wann T2-Installationen vollständig funktionieren werden.

Wenn du beim Testen helfen oder Ergebnisse teilen möchtest, nutze bitte die [GitHub Discussions](https://github.com/bridgepatcher/BridgePatcher/discussions).

### Unterstützung für USB 1.1 (OHCI/UHCI)

Bei Penryn-Systemen, Mac Pros vor 2013 und Xserve wurde die Unterstützung für USB 1.1 in macOS Ventura komplett entfernt; das gilt daher bis einschließlich Sequoia.
Auch wenn USB 1.1 unwichtig erscheinen mag, hängen viele wichtige Geräte deines Systems daran, darunter:

* Tastatur und Trackpad bei Laptops
* IR-Empfänger
* Bluetooth

Auf [der Fehlerbehebungsseite](TROUBLESHOOT-HARDWARE.md#tastatur-maus-und-trackpad-funktionieren-im-installer-oder-nach-einem-update-nicht) erfährst du, wie du dieses Problem umgehen kannst.


### Grafikunterstützung und Probleme
Dieser Build enthält sowohl Legacy-Metal- als auch Non-Metal-Patches für macOS Sequoia. Unter den folgenden Links findest du weitere Informationen zur Unterstützung von Legacy Metal und Non-Metal sowie zu den jeweiligen Problemen.

* [Legacy Metal](https://github.com/dortania/OpenCore-Legacy-Patcher/issues/1008)
* [Non-Metal](https://github.com/dortania/OpenCore-Legacy-Patcher/issues/108)
