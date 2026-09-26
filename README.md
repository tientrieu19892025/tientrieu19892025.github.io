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

Chọn **đúng thư mục** rồi tải. Cài nhầm loại thì tweak không chạy.

| Thư mục | File | Máy |
| --- | --- | --- |
| [rootless/](rootless/) | `_iphoneos-arm64.deb` | Dopamine, palera1n rootless (`/var/jb`) |
| [rootful/](rootful/) | `_iphoneos-arm.deb` | unc0ver, checkra1n, palera1n rootful |
| [roothide/](roothide/) | `_iphoneos-arm64e.deb` | Dopamine RootHide / RootHide Bootstrap |

Deb files: [`debs/rootless/`](debs/rootless/), [`debs/rootful/`](debs/rootful/), [`debs/roothide/`](debs/roothide/).

Sileo/Zebra vẫn tự chọn gói khi thêm source — không cần tải tay.

## Packages

| Name | Package | Version | Builds |
| --- | --- | --- | --- |
| AdShield | `com.jinkennguyen.adshield` | 1.0.4 | rootful, rootless, RootHide |
| AppSw | `com.jinkennguyen.appsw` | 1.0.5 | rootful, rootless, RootHide |
| CPU Boost | `com.jinkennguyen.cpuboost` | 1.0.3 | rootful, rootless, RootHide |
| dis-swipe | `com.jinken.disswipe` | 1.1.0 | rootful, rootless, RootHide |
| DuoFrame | `com.jinkennguyen.duoframe` | 3.5.3 | rootful, rootless, RootHide |
| ListApp | `com.jinken.listapp` | 1.2.1 | rootful, rootless, RootHide |
| Lock Frame | `com.jinkennguyen.haloframe` | 3.2.3 | rootful, rootless, RootHide |
| LookGlass | `com.jinkennguyen.lookglass` | 4.0.4 | rootful, rootless, RootHide |
| NoxFrame | `com.jinkennguyen.noxframe` | 1.1.1 | rootful, rootless, RootHide |
| PrankFrame | `com.jinkennguyen.prankframe` | 1.0.0 | rootful, rootless, RootHide |
| QuickPass | `com.jinken.quickpass` | 1.0.0 | rootful, rootless, RootHide |
| Repo | `com.jinkennguyen.jinken` | 1.0.0 | rootful, rootless, RootHide |
| SettingSZ | `com.jinkennguyen.settingsz` | 1.0.11 | rootful, rootless, RootHide |
| SlapIos | `com.jinkennguyen.slapios` | 1.2.0 | rootful, rootless, RootHide |
| StatusBarInfo | `com.jinkennguyen.statusbarinfo` | 1.3.0 | rootful, rootless, RootHide |

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

1. Drop files into `debs/rootless/`, `debs/rootful/` or `debs/roothide/`
2. Run `python3 scripts/update-repo.py`
3. `git add -A && git commit -m "Add tweak" && git push`

Or rebuild from local Theos trees in `~/Documents/code/*/packages`.

## License

MIT — Jinken Nguyen - 1989
