# Mémo d'intelligence web — vague 2 : forums chinois + repos GitHub (jusqu'aux plus obscurs)
**Projet** : omarchy-firmware / repo-bios — ASUS TUF GAMING B550-PLUS WIFI II (CAP `TG550PW2.CAP`)
**Date** : 2026-09-17 · **Repo au moment de la vague 2** : HEAD `f608f36` (ring 52 + 2 passes d'hygiène), sync 0/0, arbre propre — **repo READ-ONLY intégral pendant toute la vague**
**Successeur de** : `intel-web-rebar-b550w2-2026-09-17.md` (vague 1 : 3 URLs du fondateur + chaîne officielle NVIDIA + heuristique Auto ASUS + cap vBIOS 256 MB + chaîne Linux + ReBarUEFI)
**Mandat de la vague 2** (fondateur) : « des investigations sur des forums chinois aussi que sur tout les repo github même les moins connus le + possible »

---

## 1. L'écosystème chinois des options cachées — même grammaire, économie parallèle

### 1.1 Ce que la recherche a établi
La sphère chinoise du BIOS modding pratique **exactement la même grammaire IFR que nos rings 49–52 décodent à la machine** — AMIBCP, UEFITool, IFR extraction, `setup_var` — mais avec une couche commerciale parallèle (services payants, tutoriels vidéo) et des plateformes difficiles d'accès depuis l'extérieur. Faits captés :

- **L'outil chinois d'édition d'options cachées** (zhihu `p/2076426689756783006`, « BIOS隐藏选项查看修改工具发布新版：**修复部分 AMI BIOS 无法写入设置的问题** » — « outil de visualisation/modification des options BIOS cachées, nouvelle version : corrige l'impossibilité d'écrire sur certains BIOS AMI ») : un outil national avec un **fix d'écriture varstore AMI** — le même problème d'écriture Setup que notre pile mesure côté lecture. Une suite zhihu annonce le support de menus bilingues 中英一键 (bascule CN/EN). L'auteur maintient aussi un blog technique (blog.nkxingxh.top, « 老主板启用 Above 4G Decoding » — activer Above 4G sur vieilles cartes) et un unlock GitHub pour **Lenovo Y7000** (« y7000系列解除BIOS高级设置选项限制 »).
- **Les tutoriels équivalents** : CSDN « 老主板开启 Above 4GB Decoding » (original technique) ; bilibili « AMI bios修改隐藏项**解锁功耗墙** DIY » (unlock des power limits via options cachées) et « 「教程」AMI BIOS **替换菜单法** 解锁高级菜单显示隐藏菜单 » (la « méthode de remplacement de menu » — une technique d'unlock par échange de formulaires IFR, voisine de ce que UEFI-Editor fait) ; cnblogs « 利用 efi 功能更改 bios 主板被隐藏的设置 » (le `setup_var` à la chinoise).
- **La couche professionnelle** : ChinaFix (迅维网) « 解锁bios隐藏选项…方法 » (forum de réparateurs pros) ; **52pojie (吾爱破解)** partage AMIBCP **5.02.0036** ; taobao/douyin vendent des services d'unlock AMI/Insyde + LOGO rewrite — l'économie parallèle du BIOS modding.
- **Le cas « ce qui n'existe pas » côté chinois** : bilibili cv34561999 — Gigabyte Z87X-D3H, « 原生无 Above 4G Decoding 选项 » (l'option n'existe PAS nativement) → activation complète documentée. **Le même pattern que le fil WinRAID X99 du fondateur, en chinois** : des cartes dont l'option manque et que la communauté fait exister.
- **Les cousins « flip » (MSI forum traditionnel)** : « X570S ACE MAX 更新BIOS後**無法啟動 Above 4G 功能** » (l'update BIOS casse Above 4G) et « 3080 無法開啟 Resizable BAR » — les modes de défaillance voisins, aucun ne correspondant à notre live mesuré (Above4g 0x01 / CSM 0x00 stables).

### 1.2 Murailles et honnêteté
Zhihu, Chiphell, ChinaFix, Bilibili renvoient des coquilles JS/anti-bot au fetch serveur (titres + snippets sauvegardés dans `scripts/search_w2_*.json` — le contenu complet exige un navigateur avec session). Un article zhihu théorique (【PCIe】PCI Above 4G decoding) a été **supprimé** (« 你似乎来到了没有知识存在的荒原 »). Le miroir Gitee de NvStrapsReBar (gitee.com/jiangyunxing/NvStrapsReBar) répond 404 sur `master` et `main` (repo supprimé ou privé). Aucun de ces contenus manquants ne porte une prétention contradictoire à nos octets.

## 2. L'écosystème GitHub — du ★2366 au ★0, même les moins connus

Catalogue mesuré (étoiles au 2026-09-17, API GitHub/README bruts ; captures dans `scripts/w2_pages/`) :

| Repo | ★ | Rôle | Lien avec nos octets |
|---|---|---|---|
| xCuri0/ReBarUEFI | 2366 | Pilote DXE injecté qui remplace `PreprocessController` du PciHostBridgeResourceAllocationProtocol et force la taille ReBAR lue dans la variable `ReBarState` | L'architecture EXACTE du pont 4,25 Mo ASUS (Front E, ring 52), mais variable exposée |
| BoringBoredom/UEFI-Editor | 958 | « Aptio V UEFI Editor : an alternative to AMIBCP » ; workflow UEFITool NE + UEFITool 0.28.0 + IFRExtractor-RS | Le lecteur IFR manuel dont nos fw49–52 automatisent les trois quarts |
| datasone/grub-mod-setup_var | 473 | Patch GRUB (modGRUBShell) `setup_var`/`setup_var_3` ; lignée : patch froemel + setup_var2 (habr 190354 — origine russe) ; **déprécié** au profit de setup_var.efi | L'outil d'écriture du wiki « hidden 4G » |
| datasone/setup_var.efi | 441 | Réécriture standalone (aarch64, automatisable) ; « accessing wrong varstore or variable may completely brick your computer » | Le même varstore EC87D643 que nous lisons — la brique documentée |
| GeographicCone/UefiVarTool (UVT) | 77 | CLI EFI-shell, lecture/écriture de variables **au niveau de l'octet**, pensée pour les machines où Boot Guard interdit le flash custom | Le cousin byte-level de notre stack ; la voie « variable-write » quand flasher est impossible |
| xCuri0/X58Above4G | 6 | Above 4G + ReBAR sur **X58** (PCIe Gen2 !) via un .efi chargé avant l'OS (rEFInd) + override DSDT ; « Only works on Linux because Windows keeps the existing PCI allocation » | Le « ce qui n'existe pas est le plus puissant » poussé au registre matériel ; asymétrie OS pertinente pour notre candidat OS-half |
| stecklars/nvstraps-config | 5 | Configurateur **Linux** de NvStrapsReBar v0.3 via efivarfs (remplace le ReBarState Windows) | La chaîne Linux complète côté Turing |
| roncapat/W230SD-Unlocked-AMI-BIOS | 5 | Clevo W230SD : « the system setup panel is an EFI application embedded in the firmware image as a DXE driver ; menus described in IFR » — tous les formulaires cachés débloqués | La théorie Setup-DXE énoncée par un moddeur = notre lecture rings 49–52 |
| jackjusko/GA-X99-UD4P-QFlash-Above-4G-Decoding-ReBar-Cap-Removed-MMIO-High-Size-Raised-to-1tb… | 1 | **La résolution GitHub du fil WinRAID du fondateur** (LA même carte GA-X99-UD4P) : 40 h de travail, mod QFlash Above 4G + cap ReBAR retiré + MMIO High 1 To ; guide + BIOS archivés sur archive.org/details/x-99-ud-4-p.23c ; « Good luck, future hackers » | La boucle se referme : la demande du fil WinRAID a sa réponse communautaire — sur GitHub, pas chez Gigabyte |
| lolwheel/ifr-browser | 1 | « BIOS Hidden Options Editor **in browser** » : glisser l'image BIOS, basculer CFG Lock/undervolting/Above-4G…, génère un bundle USB prêt à boot ; 100 % local, version offline single-file (lolwheel.github.io/ifr-browser) | L'outil du post Reddit r/overclocking 1ufvzqz ; l'IFR lu dans le navigateur |
| Simmao/AMI-Setup-IFR-Extractor | 0 | Extracteur AMI Setup IFR (README absent — repo dormeur) | Recensé, non évalué |
| kriptosamu/am4-bios-optimization-guide | 0 | Guide de tuning UEFI/BIOS **AM4** (PBO, Curve Optimizer) | Notre famille de chipset, voix communautaire |
| topeterk/IfrViewer | — | Viewer de structures IFR | Famille des lecteurs IFR |
| XDleader555/grub_setup_var | — | Autre patch GRUB setup_var | Lignée setup_var |
| LongSoft/UEFITool + Universal-IFR-Extractor + IFRExtractor-RS | (triade canonique) | Le socle de TOUT l'écosystème ci-dessus | Nos instruments implémentent le même plan de lecture en stdlib pur |

Et côté WinRAID : **[Tool][Experimental][WIP] UniversalFormBrowser** (winraid 39825) — un navigateur de formulaires IFR universel encore expérimental.

**NvStrapsReBar (terminatorul — canonique)** : « copy of the rather popular ReBarUEFI DXE driver » spécialisé Turing (GTX 1600/RTX 2000) ; pour Pascal (GTX 1000) un grand BAR fixe est possible mais **pas resizable**, et le driver Windows BSOD si la taille change — la frontière GPU-side documentée. Fourches : Sid127/NvStrapsReBar (+ miroir Gitee mort), configurateur Linux stecklars/nvstraps-config.

## 3. Le wiki « Enabling hidden 4G decoding » — la procédure canonique, lue en entier (capture `w2_pages/wiki_hidden4g.md`)

La procédure communautaire de référence (maj 23/03/24, MrAnonymous7122) : UEFITool (chercher `4G Decod` en Unicode, sinon `Above 4G`/`MMIO`/« 64-Bit Resource Allocation ») → extraire le body → IFRExtractor-RS → lire le `VarStoreInfo (VarOffset/VarName)` → **modGRUBShell** `setup_var (offset) 0x1` (+ fallback `setup_var_3`). Ses avertissements valident nos disciplines :
- « **make sure that CSM is off** otherwise you might face issues such as black screen » — notre CsmSupport d'usine 0x00 est la précondition, déjà satisfaite.
- « If the file says the **VarStore is `PCI_COMMON`** check the other matches … usually doesn't enable 4G decoding » — le piège de varstore homonyme que notre census vsid 1–51 écarte par construction : notre Above4gDecode vit dans **Setup (EC87D643) @ 0x1BA**, jamais dans un varstore PCI commun.
- « If you get an error about **GUID mismatch** it is safe to ignore » — la communauté tolère ce que nous mesurons : nos instruments pinent le GUID exact, la divergence de GUID y est un signal, pas un bruit.
- « If your BIOS doesn't have the 4G decoding option (common on Haswell) you can try **asking motherboard vendor support** … they will sometimes send one » — la voie vendor, même conclusion que WinRAID (Koekieezz l'encourage, becca l'a attendue deux semaines en vain).

**Le fait structurel** : cette page décrit à la main, en 8 étapes, ce que notre pile fait en 15 instruments automatisés — et notre carte, elle, **possède déjà les deux options** (Above4gDecode 0x1BA, ResizeBarSupport 0x1BB) écrites à 0x01 par l'utilisateur. Nous sommes du côté « l'option existe » ; la communauté du wiki est du côté « l'option manque ».

## 4. Ce que la vague 2 change pour notre diagnostic

1. **Le firmware ASUS reste propre et complet** — la vague 2 renforce le verdict de la vague 1 : notre carte a les options que tant de communautés (X99, Z87, X58, Haswell, Y7000…) doivent faire exister par mod. Aucune des défaillances « flip » documentées (X570S ACE MAX, CSM auto-réactivé, Above 4G auto-désactivé) ne colle à notre live mesuré.
2. **Le candidat n° 1 reste GPU/vBIOS** — la vague 2 ne le contredit nulle part et ajoute la frontière Turing/Pascal (NvStrapsReBar) comme rappel que le vBIOS/carte est un maillon à part entière ; la voie OS (`nvidia-smi -q | grep -i bar`, `lspci -vv`, version driver) reste le verdict immédiat côté carte, le dump 16/09 reste le verdict firmware.
3. **L'outillage de la communauté valide notre grammaire** — UefiVarTool (byte-level), setup_var.efi, ifr-browser, UEFI-Editor, SlimIFR : cinq implémentations indépendantes de ce que fw49–52 lisent, avec les mêmes primitives (varstore, VarOffset, IFR). Notre différenciateur : pré-enregistrement, KATs, lois de paire, nulls générationnels — la communauté n'a ni registres ni refutations affichées.
4. **Patch territory, jamais appliqué** — tout ce catalogue (ReBarUEFI, setup_var.efi, UVT, mods QFlash) est documenté pour la préparation du day-0, conformément à la doctrine : rien de tout cela ne touchera la machine du fondateur sans le protocole complet.

## 5. Registre d'honnêteté de la vague 2
- Murs anti-bot : zhihu, chiphell, chinafix, bilibili, douyin (titres/snippets conservés, contenu non lu) ; article zhihu PCIe-Above-4G supprimé ; miroir Gitee NvStrapsReBar 404.
- API GitHub REST rate-limitée (IP partagée) → bascule sur raw.githubusercontent.com + recherches API avant quota : méthodologie conservée dans les captures.
- AMISCE 5.0 User Guide (Intel downloadmirror) : URL complète tronquée côté moteur — document identifié, non intégré (la voie AMI officielle scap/sceexport reste à lire si le fondateur le veut).
- Simmao/AMI-Setup-IFR-Extractor : ★0, README absent — recensé, non évalué.
- overclockers.ru p=13861239 : déjà classée morte en vague 1 (sans lien `t=` du topic parent, non résoluble).

## 6. Sources de la vague 2 (toutes consultées le 2026-09-17)
- **Repos GitHub** : github.com/xCuri0/ReBarUEFI (+ wiki Enabling-hidden-4G-decoding) ; github.com/terminatorul/NvStrapsReBar ; github.com/Sid127/NvStrapsReBar ; github.com/stecklars/nvstraps-config ; github.com/datasone/setup_var.efi ; github.com/datasone/grub-mod-setup_var ; github.com/XDleader555/grub_setup_var ; github.com/BoringBoredom/UEFI-Editor ; github.com/GeographicCone/UefiVarTool ; github.com/GeographicCone/SlimIFR ; github.com/lolwheel/ifr-browser ; github.com/xCuri0/X58Above4G ; github.com/roncapat/W230SD-Unlocked-AMI-BIOS ; github.com/topeterk/IfrViewer ; github.com/Simmao/AMI-Setup-IFR-Extractor ; github.com/kriptosamu/am4-bios-optimization-guide ; github.com/jackjusko/GA-X99-UD4P-QFlash-Above-4G-Decoding-ReBar-Cap-Removed-MMIO-High-Size-Raised-to-1tb-by-jack-jusko ; archive.org/details/x-99-ud-4-p.23c ; gitee.com/jiangyunxing/NvStrapsReBar (404).
- **Issues/ReBarUEFI** : #76 (ASUS Z87-A no 4G decode), #78 (P8Z77-V), #25 (B85-Plus), #220 (Maximus V Gene), discussion #135 (X79).
- **Communauté EN** : winraid.level1techs.com/t/release-resizable-bar-bios-efi-module/100235 (p. 8) ; winraid …/tool-experimental-wip-universalformbrowser/39825 ; winraid …/tool-guide-ami-setup-ifr-extractor-amisetupwriter/32801 ; winraid …/request-4g-decoding-re-bar-mod-asus-p8z77-v-pro-bios/90465 ; winraid …/request-unlock-above-4g-decoding-for-asus-sabertooth-z77/96021 ; bbs.archlinux.org (setup_var uefi-shell) ; reddit.com/r/overclocking/comments/1ufvzqz (ifr-browser) ; hardforum (ReBarUEFI) ; forums.guru3d (NvStrapsReBar) ; extremetech (Turing mod) ; superuser/linustechtips (Above 4G explainers) ; community.frame.work (unhide advanced BIOS).
- **Sphère chinoise** : zhuanlan.zhihu.com/p/2076426689756783006 (+ suite EN-menu) ; blog.nkxingxh.top ; blog.csdn.net (Above 4G 老主板 ; gitblog_00463) ; bilibili (BV1Uf4y1k7gg 功耗墙 ; cv34561999 Z87X-D3H ; 替换菜单法) ; cnblogs (efi 隐藏设置) ; chinafix.com thread-2303697 ; 52pojie.cn (AMIBCP 5.02.0036) ; chiphell.com (ReBAR impact) ; forum.gamer.com.tw (ASUS ReBAR) ; forum-tc.msi.com (X570S ACE MAX ; 3080) ; taobao/douyin (services).
- **Officiels** : downloadmirror.intel.com (Aptio AMISCE 5.0 User Guide) ; asus.com/support/faq/1046107 (+ .cn/.com.cn) ; nvidia.cn (ReBAR 30 系列) ; intel.com CN ; support.lenovo.com ht515548 (vBIOS ReBAR ThinkStation) ; gigabyte.com NVIDIA ReBAR ; support.hp.com ; device.report ; scribd (AFU NDA).
