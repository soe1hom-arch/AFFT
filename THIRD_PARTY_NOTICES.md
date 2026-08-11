# Third-Party Notices

This repository includes helper binaries under `bin/` that are subject to their
own upstream licenses and copyright terms.

## Bundled Binaries

| Binary | Fungsi | Sumber / Kredit |
|--------|--------|-----------------|
| `payload-dumper-go` | Extract payload.bin | [ssut](https://github.com/ssut/payload-dumper-go) |
| `lpunpack` | Unpack logical partitions | [AOSP](https://android.googlesource.com/platform/system/core/) |
| `lpmake` | Membangun super.img | [AOSP](https://android.googlesource.com/platform/system/core/) |
| `lucky-arch` | Extract partitions from sparse super.img on the fly | [GitHub](https://github.com/soe1hom-arch/lucky-arch) |
| `simg2img` | Konversi sparse Android image | [AOSP](https://android.googlesource.com/platform/system/core/) |
| `extract.erofs` | Extract filesystem EROFS | [erofs-utils](https://github.com/sekaiacg/erofs-utils) (NDK build by sekaiacg) |
| `mkfs.erofs` | Membuat filesystem EROFS | [erofs-utils](https://github.com/sekaiacg/erofs-utils) (NDK build by sekaiacg) |
| `debugfs` | Extract & debug ext4 | [e2fsprogs](https://git.kernel.org/pub/scm/fs/ext2/e2fsprogs.git/) (Static: Tsurugi Linux) |
| `make_ext4fs` | Membuat filesystem ext4 | [AOSP / rendiix](https://github.com/rendiix/make_ext4fs) |
| `magiskboot` | Unpack/repack boot image | [Magisk](https://github.com/topjohnwu/Magisk) — John Wu (topjohnwu) |

## License

The original project files in this repository are licensed under the MIT License.
See `LICENSE` for details.

Each binary tool remains subject to its own upstream license. Before
redistributing this package, verify the redistribution terms for each tool.
