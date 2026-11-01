# OpenCore erstellen und installieren

Jetzt, wo wir einen macOS-Installer haben, erstellen wir unsere OpenCore-Konfiguration!

Falls du BridgePatcher noch nicht heruntergeladen hast, hol das jetzt nach:

* [BridgePatcher Releases](https://github.com/oclp-t2/BridgePatcher/releases)

Starte als Nächstes die `BridgePatcher.app`.

Hier wählen wir `OpenCore` und klicken auf `Install OpenCore`:


<div align="left">
             <img src="../images/OCLP-GUI-Main-Menu.png" alt="BridgePatcher-GUI Hauptmenü" width="700" />
</div>

::: warning Warnung
OpenCore-Konfigurationen sind hardwarespezifisch.
Wenn du OpenCore für ein anderes Modell erstellst als das, auf dem du gerade arbeitest, musst du unbedingt das richtige Modell in den Einstellungen auswählen.
:::


<img src="../images/OCLP-GUI-Build-Start.png" alt="Erstellung starten" width="600" />


Sobald die Erstellung abgeschlossen ist, wählst du das Laufwerk aus, auf dem installiert werden soll:

* Wenn du einen macOS-USB-Stick manuell erstellt hast und er nicht aufgelistet wird, stelle sicher, dass er entweder als GUID/GPT formatiert ist oder eine FAT32-Partition für OpenCore besitzt.


| Laufwerk auswählen | Partition auswählen |
| :--- | :--- |
| <img src="../images/OCLP-GUI-EFI-Select-Disk.png" alt="Laufwerk auswählen" width="600" /> | <img src="../images/OCLP-GUI-EFI-Select-Partition.png" alt="Partition auswählen" width="600" /> |



::: tip T2-Macs
Auf einem T2-Mac müssen der sichere Start und SIP deaktiviert werden, bevor OpenCore booten kann. Sobald du den Bildschirm *Reboot to apply* erreichst, folge der [Anleitung für T2-Macs](./T2.md).
:::

# Wenn du fertig bist, geht es weiter mit [OpenCore und macOS booten](./BOOT.md)
