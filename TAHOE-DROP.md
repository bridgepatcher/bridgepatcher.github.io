# macOS Tahoe

<img width="1064" height="370" alt="macOS Tahoe" src="./images/macos-tahoe.png" />

*Here we are, the last for intel Macs*

macOS 26 Tahoe is the last major macOS release that Apple ships for Intel Macs. It drops a large number of Intel Macs, most of them with a T2 security chip, which makes it the main focus of BridgePatcher.

Support for macOS Tahoe in BridgePatcher is currently in **alpha**. Expect bugs, and please report them on [GitHub Discussions](https://github.com/bridgepatcher/BridgePatcher/discussions).


## Newly dropped hardware

* MacBookAir9,1 :       MacBook Air (Retina, 13-inch, 2020)
* MacBookPro15,1 :      MacBook Pro (15-inch, 2018 and 2019)
* MacBookPro15,2 :      MacBook Pro (13-inch, 2018 and 2019, 4 Thunderbolt 3 ports)
* MacBookPro15,3 :      MacBook Pro (15-inch, 2018 and 2019, Vega graphics)
* MacBookPro15,4 :      MacBook Pro (13-inch, 2019, 2 Thunderbolt 3 ports)
* MacBookPro16,3 :      MacBook Pro (13-inch, 2020, 2 Thunderbolt 3 ports)
* Macmini8,1 :          Mac mini (Late 2018)
* iMac19,1 :            iMac (Retina 5K, 27-inch, 2019)
* iMac19,2 :            iMac (Retina 4K, 21.5-inch, 2019)
* iMacPro1,1 :          iMac Pro (2017)

All of these models except the iMac (2019) have a T2 security chip.

The only Intel Macs that still run Tahoe natively are the MacBook Pro (16-inch, 2019), MacBook Pro (13-inch, 2020, 4 Thunderbolt 3 ports), iMac (Retina 5K, 27-inch, 2020) and Mac Pro (2019).

## Current status
BridgePatcher supports Tahoe for the models below, however some challenges remain. You can find information about them further down this page
<img width="625" alt="" src="./images/OCLPT2-Tahoe-Support.png">

For Macs **without** a T2 chip, BridgePatcher can install macOS Tahoe and apply root patches, however some challenges remain. You can find information about them further down this page.

For **T2 Macs**, Tahoe does not work yet. See [T2 security chip](#t2-security-chip) below and [T2 Macs and macOS Tahoe](MODELS.md#t2-macs-and-macos-tahoe) for the current status.

## Non-functional features

On majority of patched Macs, iPhone Mirroring and Apple Intelligence won't be functional.

iPhone Mirroring requires T2 for attestation and Apple Intelligence requires an NPU only found in Apple Silicon, the patcher is unable to provide a fix for these as they're hardware requirements.

## Issues

* [T2 Security chip](#t2-security-chip)
* [Audio support](#audio-support)
* [Dual socket CPUs with Mac Pros and Xserve](#dual-socket-cpus-with-mac-pro-2008-and-xserve-2008)
* [USB 1.1 (OHCI/UHCI) Support](#usb-1-1-ohci-uhci-support)
* [Graphics support and issues](#graphics-support-and-issues)


### T2 security chip

Booting unsupported T2 Macs through OpenCorePkg used to end in a kernel panic, because AppleKeyStore.kext ran into timeouts while communicating with the T2 chip:

```
"AppleKeyStore":3212:0: sks timeout strike 18
"AppleKeyStore":3212:0: sks timeout strike 19
"AppleKeyStore":3212:0: sks timeout strike 20
panic(cpu 0 caller 0xffffff801cd12509): "AppleSEPManager panic for "AppleKeyStore": sks request timeout" @AppleSEPManagerIntel.cpp:809
```

**This panic no longer occurs.** BridgePatcher now gets past the AppleKeyStore timeouts on unsupported T2 Macs, so the machines boot into the Tahoe installer.

The remaining issue is that the macOS installation currently ends with "Failed to install a software update" before it finishes. We cannot provide an estimate on when T2 installations will fully work yet.

If you want to help test or share results, please use [GitHub Discussions](https://github.com/bridgepatcher/BridgePatcher/discussions).

### Audio support

macOS Tahoe no longer includes AppleHDA.kext, the driver used for built-in audio on Intel Macs. On affected Macs, BridgePatcher restores audio through the "Modern Audio" root patch, so make sure to run root patching after installing Tahoe. The iMac (2019) is the exception, see below.

#### iMac (2019): audio without root patching

Starting with BridgePatcher **4.0.0.2000003.3**, and in the current release 4.0.0.2000003.4, audio on the iMac (Retina 5K, 27-inch, 2019) and the iMac (Retina 4K, 21.5-inch, 2019) (`iMac19,1` and `iMac19,2`) is restored by OpenCore instead of the "Modern Audio" root patch. On these Macs the root patch could fail to install, or leave the Mac stuck at the "no entry" symbol after a restart.

When you build OpenCore for one of these iMacs, BridgePatcher adds [SimpleHDA](https://github.com/laobamac/SimpleHDA) by laobamac together with AppleALC (layout `alcid=7`), the method a community member [found and tested on an iMac19,2](https://github.com/orgs/bridgepatcher/discussions/315). Nothing on the system volume changes, so no root patching, Kernel Debug Kit or SIP change is needed for audio.

1. Update BridgePatcher to 4.0.0.2000003.3 or newer.
2. If the "Modern Audio" root patch is installed, revert root patches first. BridgePatcher keeps a working root patch and doesn't add SimpleHDA while it's installed, so that AppleHDA isn't loaded twice.
3. Make sure the Mac is connected to the internet, then build and install OpenCore.
4. Restart. If there's no sound, reset NVRAM once from the OpenCore boot picker.

::: tip Good to know

* SimpleHDA isn't bundled with BridgePatcher, because its license doesn't allow redistribution. It is downloaded from laobamac's GitHub releases while OpenCore is built, and only used if its checksum matches. Without an internet connection OpenCore is built without it, and the "Modern Audio" root patch stays available.
* AppleALC and SimpleHDA only load on macOS Tahoe, so older macOS versions you dual boot keep their native audio.
* It's on by default and can be turned off in Settings -> Extras -> "SimpleHDA Tahoe Audio". The setting is only shown when building for one of these iMacs.
* It has been reported working on the iMac19,2. The iMac19,1 is untested so far, so please share your results in the [discussion](https://github.com/orgs/bridgepatcher/discussions/315).

:::

### Dual socket CPUs with Mac Pro 2008 and Xserve 2008

As with macOS Sequoia, booting Tahoe on Mac Pro 2008 (MacPro3,1) or Xserve 2008 (Xserve2,1) with more than 4 cores will cause a kernel panic. BridgePatcher will automatically disable additional cores.

**If building OpenCore for older OS, this limitation can be disabled in Settings -> Build -> "MacPro3,1/Xserve2,1 Workaround".**

::: warning Note

Dual booting Tahoe and older will not be possible with all cores enabled due to reasons described before. In these cases you will be limited to 4 cores.

:::

### USB 1.1 (OHCI/UHCI) Support

For Penryn systems, pre-2013 Mac Pros and Xserve, USB 1.1 support was outright removed in macOS Ventura, therefore this applies all the way to Tahoe.
While USB 1.1 may seem unimportant, it handles many important devices on your system. These include:

* Keyboard and Trackpad for laptops
* IR Receivers
* Bluetooth

Refer to [the troubleshooting page](TROUBLESHOOT-HARDWARE.md#keyboard-mouse-and-trackpad-not-working-in-installer-or-after-update) on how to workaround this issue.


### Graphics support and issues

This build includes both Legacy Metal and non-Metal patches for macOS Tahoe, based on the upstream Dortania patches. Refer to the following links for more information about Legacy Metal and non-Metal support and their respective issues.

* [Legacy Metal](https://github.com/dortania/OpenCore-Legacy-Patcher/issues/1008)
* [Non-Metal](https://github.com/dortania/OpenCore-Legacy-Patcher/issues/108)

::: warning AMD Vega on T2 Macs

Graphics acceleration for the AMD Vega GPUs in the iMac Pro (2017) and the Vega-equipped MacBook Pro (15-inch, 2018 and 2019) is currently not provided on Tahoe.

:::
