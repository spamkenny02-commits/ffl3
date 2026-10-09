# Final Fantasy Legend III — français + patch couleur fourni

Cette version adapte la traduction existante au patch FFL3.ips fourni. Le patch couleur agrandit déjà la ROM USA de 256 à 512 Ko et change le mapper en MBC5 + RAM + batterie (1B). La traduction conserve ces 512 Ko : aucun agrandissement supplémentaire. Ce paquet ne contient pas une version couleur de 256 Ko.

## Utiliser les patchs

Choisir une seule méthode, sur une copie propre :

- ROM USA originale de 256 Ko : appliquer FFL3_FR_Color.ips. Ce patch contient à la fois la couleur et le français.
- ROM de 512 Ko obtenue en appliquant exactement le FFL3.ips fourni à cette ROM USA : appliquer FFL3_FR_Color_sur_couleur.ips. Ce patch ajoute la traduction et conserve la taille.
- FFL3_FR_Color.gb est le résultat prêt à tester dans un émulateur Game Boy Color.

Ne pas appliquer ces patchs à l’ancienne ROM française monochrome ni réappliquer le patch couleur sur le résultat. Le fichier FFL3_color_source.ips est une copie exacte du patch couleur fourni, utilisée pour reconstruire.

## Compatibilité et vérifications

Les 1 232 entrées traitées par le constructeur sont reprises du projet français existant. Aucun texte traduit n’a été raccourci pour cette adaptation. La routine de lecture a été réécrite : 43 octets dans une zone libre de la banque 0 à 3FD1, le reste dans la banque 31. Les textes utilisent les banques libres 18 et 19 ; le dictionnaire français et la table de références courtes sont en banque 31. Le code et les données couleur des banques 16 et 22 restent intacts.

Les tests comparent chaque octet réellement modifié par le patch couleur : tous restent identiques, à l’exception des trois octets de sommes de contrôle recalculés. Les pointeurs racines des événements sont conservés. Les deux chemins d’application IPS produisent exactement la même ROM.

Cinq tests passent : reconstruction, taille/mapper/sommes de contrôle ; reproduction par les deux patchs et conservation des changements couleur ; pointeurs et commandes ; affichage des neuf accents et restauration des banques ; scénario initial, sauvegarde et rechargement après fermeture de l’émulateur.

Le premier combat et le scénario jusqu’au Talon ont été parcourus sur 62 721 images émulées, avec zéro lecture détectée dans les anciens textes déplacés. Les captures montrent les couleurs, le texte français et les accents. Aucun parcours complet ni essai sur console physique n’a été effectué. Les limites de la traduction antérieure restent présentes : fragments anglais, extraction en partie heuristique, certains accents et graphismes manquants.

## Modifier et reconstruire

ROM source : Final Fantasy Legend III (USA), 262 144 octets.
SHA-256 : 5ed87f65225b72a74c3c04a4e5d67683fb5cc33e5f1266157350828ab973fc1d.
La ROM USA originale n’est pas incluse.

Python 3.10 ou ultérieur, Tkinter et dépendances :

```sh
python -m pip install -r requirements.txt
python ffl3_editor.py gui
```

Sous Windows, double-cliquer sur Ouvrir_editeur.bat et choisir la ROM USA originale. L’éditeur charge project_fr.json ; son bouton Exporter produit désormais la ROM couleur française et le patch combiné. L’aperçu de police reste une simulation, pas une émulation du cadre couleur. Le bouton Jouer ROM permet d’ouvrir le résultat exporté.

Pour reconstruire les deux patchs depuis le projet :

```sh
python color_builder.py original.gb FFL3_color_source.ips project_fr.json FFL3_FR_Color.gb
```

expanded_builder.py est une dépendance interne du constructeur couleur. Utiliser color_builder.py pour cette version.

Pour exécuter les tests, placer la ROM USA originale sous original.gb et lancer :

```sh
python -m unittest discover -s . -p test_color.py -v
```

Les tests de scénario utilisent color_audit.json et color_audit.state. Pour régénérer cet audit :

```sh
python runtime_audit.py FFL3_FR_Color.gb FFL3_FR_Color.report.json color_audit.json --cycles 1000
```
