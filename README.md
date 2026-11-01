---
layout: home

hero:
  name: BridgePatcher
  tagline: Experience macOS just like before
  image:
    src: /homepage.png
    alt: BridgePatcher
  actions:
    - theme: brand
      text: Getting Started →
      link: /START
    - theme: alt
      text: Announcements
      link: /announcements/
    # Direct download of the newest release. /releases/latest/download/ always
    # resolves to the latest (non-pre-)release on the server side, so it also
    # works in old Safari versions that can't render github.com pages.
    # Falls back to OpenCore-Patcher-T2.pkg when the newest release has no
    # BridgePatcher.pkg (see DOWNLOAD_FALLBACK in .vitepress/config.mts).
    - theme: alt
      text: Download latest version
      link: https://github.com/bridgepatcher/BridgePatcher/releases/latest/download/BridgePatcher.pkg

features:
  - title: Near-native OTA updates
    details: "Install updates from System Settings, with just couple more additional steps compared to native."
  - title: Zero firmware patching
    details: "Using the capabilities of the OpenCore boot manager, our protocol upgrades are done in memory and are never permanent."
  - title: Supporting more hardware
    details: "New life is breathed into your decade-old graphics card, WiFi, and Bluetooth chipsets. Even your upgraded hardware receives benefits by unlocking exciting features like Hardware Acceleration, AirDrop, Apple Watch Unlock, Sidecar, and much more!"
  - title: Unlock newer features
    details: "Unlock some newer features such as Sidecar, AirPlay to Mac, Night Shift, and Universal Control, even on natively supported models!"
  - title: A helpful community
    details: "Whether it's getting started or learning the specifics, you can always find answers with our amazing community of tinkerers, developers, and dreamers."
footer: Copyright © Dortania 2020-2025 · BridgePatcher © 2026 Albert Müller and BridgePatcher contributors
---

<HomeAnnouncements />
