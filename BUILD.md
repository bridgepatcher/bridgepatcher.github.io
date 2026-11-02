# Building and installing OpenCore

Now that we have a macOS installer, let's now build our OpenCore configuration!

If you haven't downloaded BridgePatcher yet, do so now:

* [BridgePatcher Releases](https://github.com/bridgepatcher/BridgePatcher/releases)

Next, run the `BridgePatcher.app`

Here we'll select `OpenCore` and click `Install OpenCore`:


<div align="left">
             <img src="./images/OCLP-GUI-Main-Menu.png" alt="BridgePatcher GUI Main Menu" width="700" />
</div>

::: warning
OpenCore configurations are hardware specific.
If you're building OpenCore for a different model than you're currently running, it is absolutely necessary to select the proper model from Settings.
:::


<img src="./images/OCLP-GUI-Build-Start.png" alt="Build start" width="600" />


Once it finishes building, you'll want to select the disk to install to:

* If you created a macOS USB manually and don't see it listed, make sure it's either formatted as GUID/GPT or has a FAT32 partition for OpenCore to reside on.


| Select Drive | Select Partition |
| :--- | :--- |
| <img src="./images/OCLP-GUI-EFI-Select-Disk.png" alt="Select disk" width="600" /> | <img src="./images/OCLP-GUI-EFI-Select-Partition.png" alt="Select partition" width="600" /> |



::: tip T2 Macs
On a T2 Mac, Secure Boot and SIP have to be disabled before OpenCore can boot. Once you reach the *Reboot to apply* screen, follow the [Instructions for T2 Macs](./T2.md).
:::

# Once finished, head to [Booting OpenCore and macOS](./BOOT.md)
