# Jinken Repo

Cydia / Sileo / Zebra repository for jailbreak tweaks.

**Credit: Jinken Nguyen - 1989**  
Cảm ơn bạn đã dùng tweak. Nếu thấy hữu ích, một chút ủng hộ giúp giữ repo miễn phí.

**Donate: MB Bank `0345140889` — Nguyễn Tiến Triều**

## Add source

```
https://tientrieu19892025.github.io
```

- Sileo: Sources → + → paste URL, or open `sileo://source/https://tientrieu19892025.github.io/`
- Zebra: `zbra://sources/add/https://tientrieu19892025.github.io/`
- Cydia: Sources → Edit → Add

Sileo / Zebra pick the right build automatically:

| Device | Architecture | Jailbreak |
| --- | --- | --- |
| Rootless | `iphoneos-arm64` | Dopamine, palera1n rootless |
| Rootful | `iphoneos-arm` | unc0ver, checkra1n, palera1n rootful |
| RootHide | `iphoneos-arm64e` | Dopamine-roothide / RootHide Bootstrap |

Do not install a `.deb` by hand unless you know your jailbreak type.

## Packages

| Name | Package | Version | Builds |
| --- | --- | --- | --- |
| CPU Boost | `com.jinkennguyen.cpuboost` | 1.0.0 | rootful, rootless, RootHide |
| DuoFrame | `com.jinkennguyen.duoframe` | 3.5.2 | rootful, rootless, RootHide |
| Lock Frame | `com.jinkennguyen.haloframe` | 1.2.1 | rootful, rootless, RootHide |
| LookGlass | `com.jinkennguyen.lookglass` | 4.0.0 | rootful, rootless, RootHide |
| SlapIos | `com.jinkennguyen.slapios` | 1.2.0 | rootful, rootless, RootHide |

## Credit

- Author / Maintainer: **Jinken Nguyen - 1989**
- Not affiliated with Apple.

## Donate

Cảm ơn bạn đã tin dùng tweak miễn phí. Nếu thấy hữu ích, một chút ủng hộ giúp mình giữ repo chạy và ra bản mới — không bắt buộc.

Thank you for using these free tweaks. A small donation keeps the repo online. No pressure.

| | |
| --- | --- |
| Ngân hàng | MB Bank |
| STK | `0345140889` |
| Chủ TK | Nguyễn Tiến Triều |
| Nội dung | `Donate Jinken Nguyen 1989` |

VietQR: scan the code on the [homepage](https://tientrieu19892025.github.io/#donate).

## Upload a new `.deb`

1. Drop files into `debs/` using `package_version_architecture.deb`
2. Run `python3 scripts/update-repo.py`
3. `git add -A && git commit -m "Add tweak" && git push`

Or rebuild from local Theos trees in `~/Documents/code/*/packages`.

## License

MIT — Jinken Nguyen - 1989
