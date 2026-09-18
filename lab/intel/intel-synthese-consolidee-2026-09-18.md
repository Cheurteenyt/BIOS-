# Synthèse consolidée — audit du repo + trois vagues d'intel web
**Projet** : omarchy-firmware / repo-bios — ASUS TUF GAMING B550-PLUS WIFI II (CAP `TG550PW2.CAP`)
**Date** : 2026-09-18 · **Repo** : HEAD `f608f36` (ring 52 `4b7e697` + deux passes d'hygiène), sync 0/0, arbre propre, 283 fichiers trackés
**Symptôme étudié** (fondateur) : « le reshade bar… il détecte mal alors que c'est en auto »
**Successeur de** : vague 1 `intel-web-rebar-b550w2-2026-09-17.md`, vague 2 `intel-web2-forums-chinois-github-2026-09-17.md`, vague 3 `intel-web3-github-500plus-2026-09-17.md` (+ catalogue CSV 3 788 dépôts)
**Statut repo** : READ-ONLY intégral pendant les Tasks 52–55 — cette synthèse vit HORS du repo, prête à être canonisée dans `lab/` sur ordre du fondateur

---

## 1. L'état reconcilié (rachat de la dérive #41)

Le résumé de continuation reçu décrivait l'état « Task 50 / ring 52 / 4b7e697 / audit et investigations non commencés / dérives #38-#41 quadruple suspension ». Le disque était **cinq tasks plus loin** : le worklog porte Tasks 51–55, HEAD est `f608f36`, et les trois mémos d'intel datés du 17/09 existaient déjà. Le disque prime, comme aux rachats #37, #38, #39 et #40. Établissement de la vérité :

| Axe demandé par le fondateur | Exécution réelle (worklog) | Verdict |
|---|---|---|
| « audite profondément le repo… **sans rien modifier** » | Task 51 (hygiène 19 gates, 5 couches — 3 défauts de doc trouvés et réparés en 2 commits **autorisés**) puis Task 52 (ré-audit indépendant STRICTEMENT read-only, 9 gates supplémentaires, zéro écriture y compris non-trackée) | **CLEAN** — 19/19 puis 9/9 gates, 323/323, surface gelée 0 diff depuis le ring 52, 0 doublon, 0 orphelin, registres conformes |
| Les 3 URLs fournies | Task 53 | 2 exploitables (TechPowerUp GA104 : la piste vBIOS ; WinRAID X99 : **validation externe majeure** de notre grammaire IFR) ; 1 morte (overclockers.ru, exclue de Wayback) |
| « des recherches très profondes sur internet » | Task 53 — 17 requêtes, 15 pages | Chaîne officielle NVIDIA (3 composantes), heuristique Auto ASUS explicitée, cap vBIOS 256 MB, protocole Linux |
| « des forums chinois aussi que sur tout les repo github même les moins connus » | Task 54 — 19 requêtes, ~30 pages/repos | Écosystème chinois cartographié malgré les murailles ; 18 repos du ★2366 au ★0 ; boucle WinRAID refermée sur GitHub |
| « au moins 500 repo github… les trucs récents… un moyen ingénieux » | Task 55 — lattice de 64 requêtes API, 7 lentilles, scoring 9 axes | **3 788 dépôts uniques** (7,6× l'objectif), 1 784 créés 2025+, 1 993 poussés ≤ 90 j, 2 136 ≤ 5 étoiles, 30 gemmes immergés en README intégral |

Les dérives #38, #39, #40 ont été radiées aux Tasks 52, 54 et 55. La dérive **#41** (le présent résumé de continuation) est radiée par ce document et l'entrée Task 56 du worklog — première écriture disque de la session, hors repo. **Compteur de dérives : zéro.**

## 2. Ce que les trois vagues disent D'UNE SEULE VOIX (aucune contradiction en trois vagues)

### 2.1 Le firmware ASUS de la carte est propre, complet et cohérent — confirmé 3×
Rings 46–52 : l'axe complet existe et est mesuré à l'octet (Above4gDecode 0x1BA / ResizeBarSupport 0x1BB / SriovSupport 0x1BC / CsmSupport 0x1F2), le langage est lu ({0x00 : Disabled, 0x01 : **Auto**} pour ReBAR — pas d'Enabled, la loi ring 50 confirmée par un utilisateur X570 ASUS en vague 1), la loi d'usine est prouvée 15/15 (toute la chaîne decode expédiée OFF — le « c'est en auto » du fondateur est un état écrit, pas l'état d'usine), la grammaire est nommée champ par champ (le C-source AMI embarqué, 396 champs), la cour des lecteurs est faite (34 consommateurs EC87D643, dont un pont de politique de 4,25 Mo release-invariant qui porte l'heuristique Auto). Les trois vagues d'intel s'assemblent sur ces octets **sans en contredire un seul**. Au contraire : des communautés entières (X99, Z87, X58, Haswell, Y7000, Z690M…) doivent MODDER pour faire exister les options que cette carte a déjà en usine — le pattern « ce qui n'existe pas » documenté en anglais, en russe et en chinois.

### 2.2 Le candidat n° 1 « GPU/vBIOS » est renforcé pour la 3e vague consécutive
La chaîne de preuves, vagues 1+2+3 assemblées :
1. **L'heuristique Auto ASUS teste le vBIOS pendant le POST** (modérateur ROG, vague 1) : « If when you enable (Auto) Re-Size BAR Support, you get "The VGA card is not supported by UEFI driver" during POST, **your issue is GPU VBIOS related** » — exactement le mécanisme que notre Front E a borné sans le lire (doctrine : pas de patch).
2. **Les early 30-series ont un vBIOS capé** (TechPowerUp 330305, vague 1) : « Some early 30 series came with resizable BAR capped to 256MB. All the VBIOS updates did is change that cap (1 nibble) » — cas Gigabyte 3070 OC résolu par update vBIOS ; l'utilitaire ASUS peut refuser à tort.
3. **Le root cause est nommé sur une ASUS TUF** (danindiana/rtx3080-rebar-vbios, vague 3) : « the 3080 did not [have ReBAR active] because its **factory VBIOS lacked the ReBAR capability bit** », `pci=realloc` sans effet sur cinq reboots — notre symptôme à l'identique, côté carte.
4. **La chaîne officielle NVIDIA** (vague 1) : GPU+vBIOS / SBIOS (UEFI + Above 4G + ReBAR + CSM off + GPT) / driver **≥ 461.40 pour la 3070** ; le troubleshooting officiel dit « reconfirm the VBIOS updated successfully » ; la B550 est dans le périmètre officiel AMD 500 Series.
5. **Frontière GPU-side documentée** (vague 2) : NvStrapsReBar — Pascal = BAR fixe sans resizable ; la détection côté Linux (BAR1 vs VRAM) lit le résultat de la décision du POST.

### 2.3 Les deux candidats co-déclarés restent ouverts et bornés
- **L'heuristique Auto dans le pont 4,25 Mo** : bornée (Front E, ring 52), non lue, territire vendor — le miroir communautaire ReBarUEFI (★2366) prouve que la même architecture (variable NVRAM + exécuteur DXE) peut être rendue explicable, mais c'est patch territory, documenté jamais appliqué.
- **La moitié OS/driver** : versions driver (≥ 461.40 pour 3070 ; `NVreg_EnableResizableBar=1` pour Blackwell seulement), désaccords GPU-Z/driver (« GPU-Z often reports 4G decode/CSM incorrectly », wiki ReBarUEFI), power cycle complet parfois requis (ArchWiki). Aucun des modes « flip » documentés (Above 4G auto-désactivé, CSM auto-réactivé, menu CSM disparu — vagues 1-2) ne colle au live mesuré (Above4g 0x01 / CSM 0x00 stables).

### 2.4 La contrainte plateforme AMD est une loi d'écriture confirmée
« Does not work on AMD systems » (NZK95/grubmod, vague 3) + UMAF comme route no-flash AMD de la communauté CN : sur B550, les voies d'écriture communautaires se réduisent à `setup_var.efi` / UefiVarTool / SCEWIN / flash — et la classe émergente « **NVRAM defaults** » (GMK M5 Pro : ReBAR fixé par 2 octets de defaults ; symptôme « ReBAR not detected » identique) montre que ce sont les défauts qui décident de la détection, exactement le territoire de notre `ResizeBarSupport 0x1BB` (défaut usine 0x00, live 0x01 écrit).

## 3. « Ce qui n'existe pas est le plus puissant » — les trous du réseau entiers

Sur 3 788 dépôts passés au crible (vague 3, §9) : aucune carte grammaticale publique B550-PLUS WIFI II (nos 396 champs / 0x1BA-0x1BB / pont 4,25 Mo restent uniques au monde) ; zéro pré-enregistrement de prédictions, zéro réfutation affichée ; zéro loi d'usine prouvée par recoupement multi-sources ; le genre « read-only + ledger » existe désormais (bios-unlock-studio, 2026-08) mais sans jour-0 ni cour d'octets pré-ancrée. **Le protocole day-0 reste sans équivalent mondial.** Le genre « agent IA modifie un BIOS » existe aussi désormais (z690m-snow-dream-rebar, 2026-09-15 — brique puis sauvetage au programmateur) : la preuve par le contre-exemple que la discipline pré-enregistrement n'est pas du sur-rituel.

## 4. L'arbre de décision du fondateur

### 4.1 MAINTENANT — côté OS, sans toucher au firmware (verdict immédiat du candidat n° 1)
```bash
nvidia-smi -q | grep -i bar -A 3          # BAR1 = 256 MiB ⇒ inactif ; BAR1 = VRAM complète ⇒ actif
nvidia-smi -q | grep -i "VBIOS Version"   # l'identité du vBIOS à comparer à la base TechPowerUp
lspci -vv -d ::03xx | grep -A4 BAR        # "Physical Resizable BAR" : current vs supported
journalctl -k --grep=BAR=                 # [drm] Detected VRAM …, BAR=…
nvidia-smi --query-gpu=driver_version --format=csv   # ≥ 461.40 requis pour une 3070
```
Puis : **power cycle électrique complet** avant tout verdict (ArchWiki) ; comparer le vBIOS à techpowerup.com/vgabios (un vBIOS pré-mars-2021 ou capé 256 MB est le suspect n° 1 d'un « Auto détecte mal ») ; se méfier de GPU-Z sur 4G/CSM (wiki ReBarUEFI).

### 4.2 AU DUMP — le protocole day-0 (inchangé, pré-ancré par rings 46–52)
fw46 fused → fw47/48 marks (PSP 37/37 + rotation de certificat attendues côté flash-story) → fw49 axis → fw50 lang → fw51 fact (cinq-gate byte court : attentes live **inversées** du factory — Above4g 0x01, ReBAR 0x01, CSM 0x00) → fw52 gram/executor (identités sha16 du day-0 card). Le dump tranche le **delta live-minus-factory de la variable Setup, octet par octet, en noms de champs** — il ne tranche PAS l'état du vBIOS de la carte GPU (pour cela : § 4.1).

### 4.3 APRÈS — sur ordre du fondateur uniquement
- **Canoniser** l'intel des trois vagues + cette synthèse dans `lab/` (le repo redevient écrit) ;
- **Ring 53** — trois candidats en lice : SystemAccess dans le TSE (les 4 octets que ring 50 a laissés vendor-code), l'identité des 32 autres lecteurs EC87D643, l'authorship B550 du pont 4,25 Mo ;
- **Vague 3.5 optionnelle** : immerger plus des 396 gemmes tier-S non lus du CSV (rendements décroissants — les trois vagues convergent déjà) ;
- Le post overclockers.ru mort : ré-ouvrable seulement avec le lien `t=` du topic parent.

## 5. Registre d'honnêteté consolidé
- Sources mortes/murailles : overclockers.ru p=13861239 (morte, non archivée) ; zhihu/chiphell/chinafix/bilibili anti-bot (titres/snippets conservés) ; article zhihu PCIe-4G supprimé ; miroir Gitee NvStrapsReBar 404 ; AMISCE 5.0 URL tronquée.
- Vague 3 : 2 requêtes `total=0` compensées ; faux positifs « rebar » (BTP/BIM) filtrés de la synthèse, conservés au CSV ; 30/426 tier-S immergés ; 2 fenêtres rate-limit 65 s.
- Défaillance d'audit assumée : 4 FAIL du ré-audit v2 étaient des bugs de l'outil session-side (corrigés hors repo), 3 FAIL du premier passage Task 51 idem.
- Le repo est resté intouché pendant les Tasks 52–55 (zéro commit, zéro fichier, y compris non-tracké) ; les seules écritures autorisées restent les 2 commits d'hygiène du Task 51 (docs only, 4 fichiers, validés par diff avant/après).

## 6. Index des livrables de la phase d'investigation (tous hors repo)
| Fichier | Contenu |
|---|---|
| `download/intel-web-rebar-b550w2-2026-09-17.md` | Vague 1 — 3 URLs, chaîne NVIDIA, heuristique Auto, cap vBIOS, Linux |
| `download/intel-web2-forums-chinois-github-2026-09-17.md` | Vague 2 — écosystème chinois, 18 repos, wiki hidden-4G |
| `download/intel-web3-github-500plus-2026-09-17.md` | Vague 3 — lattice 64 requêtes, 3 788 dépôts, 30 gemmes |
| `download/github-intel-catalog-vague3-2026-09-17.csv` | Catalogue complet (3 788 lignes, 888 Ko) |
| `download/intel-synthese-consolidee-2026-09-18.md` | Ce document |
| `scripts/repo_audit_r52.{py,json}`, `scripts/audit_deep_v2.{py,json}` | Les deux couches d'audit ré-exécutables |
| `scripts/sweep3_*`, `scripts/search_w2_*`, `scripts/w2_pages/` | Captures brutes des trois vagues |
