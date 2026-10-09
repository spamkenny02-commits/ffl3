# Final Fantasy Legend III — atelier de traduction française

Sauvegarde du travail au 9 octobre 2026 : outils Python, projet de traduction, patchs IPS, analyses et captures de validation. Version expérimentale, le jeu entier n’a pas encore été parcouru.

## Versions

| Dossier | Version | Mapper | Taille du résultat |
| --- | --- | --- | --- |
| `color/` | Français + patch couleur fourni | MBC5 + RAM + batterie, `1B` | 512 Ko, taille identique à la version couleur seule |
| `monochrome/` | Français sans colorisation | MBC1 + RAM + batterie, `03` | 512 Ko |
| `research/` | Scripts de recherche conservés | — | — |

Le patch couleur fourni agrandit lui-même la ROM de 256 à 512 Ko. La traduction couleur conserve cette taille. Les deux versions comportent 1 435 entrées dans le projet ; le constructeur traite 1 232 entrées. La version monochrome comporte 1 095 emplacements textuels réellement modifiés. Le projet français est repris dans la version couleur.

Les ROM complètes et les sauvegardes personnelles ne sont pas publiées dans ce dépôt. Les patchs et les constructeurs permettent de reproduire les résultats. Les fichiers `.state` sont des états d’émulation créés pour les validations, distincts des sauvegardes de jeu personnelles.

## Appliquer les patchs couleur

Choisir une seule méthode, sur une copie propre :

- Sur la ROM USA originale : `color/FFL3_FR_Color.ips`, patch combiné couleur + français.
- Sur une ROM déjà colorisée avec exactement le patch fourni : `color/FFL3_FR_Color_sur_couleur.ips`.

`color/FFL3_color_source.ips` conserve le patch couleur fourni pour la reconstruction. Ne pas appliquer les anciens patchs monochromes à la version couleur. Les fichiers README de chaque dossier donnent les détails.

## Source requise

Final Fantasy Legend III (USA), **262 144 octets**.

SHA-256 : `5ed87f65225b72a74c3c04a4e5d67683fb5cc33e5f1266157350828ab973fc1d`.

Le constructeur refuse une autre révision. Fournir votre copie originale pour reconstruire.

## Reconstruire

Python 3.10 ou ultérieur, Tkinter pour l’éditeur, Pillow pour l’aperçu et PyBoy pour l’émulation :

```sh
python -m pip install -r color/requirements.txt
python color/color_builder.py original.gb color/FFL3_color_source.ips color/project_fr.json color/FFL3_FR_Color.gb
python monochrome/expanded_builder.py original.gb monochrome/project_fr.json monochrome/FFL3_FR_512K.gb
```

Pour ouvrir l’éditeur couleur :

```sh
python color/ffl3_editor.py gui
```

Sous Windows, double-cliquer sur `Ouvrir_editeur.bat` dans le dossier choisi puis sélectionner la ROM USA originale de 256 Ko. L’éditeur couleur exporte la version couleur ; l’éditeur monochrome exporte la version monochrome. Le projet JSON placé dans chaque dossier reste éditable.

## Validation

- Monochrome : onze tests de ROM/émulation, plus cinq tests du lancement de l’éditeur.
- Couleur : cinq tests couvrent la taille et le mapper, la reconstruction, les deux routes IPS, la conservation des changements du patch couleur, les pointeurs/commandes, les neuf accents, le premier combat, le scénario jusqu’au Talon, la sauvegarde et le rechargement après fermeture de l’émulateur.
- L’audit couleur couvre 62 721 images émulées et ne relève aucune lecture dans les anciens textes déplacés sur ce parcours. Validation couleur avec PyBoy 2.8.1.

Pour refaire les tests, reconstruire les ROM à leurs emplacements ci-dessus. Placer une copie de la ROM USA originale sous `original.gb` dans chacun des dossiers, ou définir `FFL3_ORIGINAL_FILE` sur son chemin absolu. Puis :

```sh
python -m unittest discover -s monochrome -p test_launcher.py -v
python -m unittest discover -s monochrome -p test_expansion.py -v
python -m unittest discover -s color -p test_color.py -v
```

Les rapports JSON et les captures sont conservés dans les dossiers correspondants. Les fichiers d’audit permettent de reprendre les essais. Les scripts de `research/` sont des archives de travail, à adapter avant réutilisation.

## Limites

L’extraction des événements reste en partie heuristique ; tous les chemins de dialogue et paramètres ne sont pas identifiés. Les autres époques, boutiques, donjons, boss et la fin restent à valider. Des fragments anglais, des abréviations et des graphismes anglais subsistent. Les glyphes é è à ê â î ô ù ç sont installés ; û ë ï et les majuscules accentuées manquent. Aucun essai sur console physique ni transfert de sauvegarde USA n’a été réalisé. L’interface Tkinter n’a pas été testée interactivement sous Windows.

Les noms, graphismes et contenus du jeu appartiennent à leurs ayants droit. Aucune licence de redistribution de la ROM ou du patch couleur tiers n’est ajoutée par ce dépôt.
