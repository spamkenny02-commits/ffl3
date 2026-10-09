# Final Fantasy Legend III USA — tentative française, ROM de 512 Ko

Cette version traduit les dialogues identifiés du scénario, jusqu'au dénouement, ainsi que de nombreux objets, équipements, ennemis, talents, menus et messages de combat. Elle est expérimentale : elle ne constitue pas une traduction intégrale validée sur un parcours complet.

## Reprise du 8 octobre 2026

202 entrées ont reçu des corrections d’accents. Les tests inclus dans l’archive utilisent maintenant le nom correct du rapport. Le relais reconnaît une commande d’accent `4C 8A` suivie d’un code de tuile 80–87 ; `é` utilise la tuile AB. Les neuf emplacements étaient vides dans la ROM source. Les icônes et les tuiles graphiques F9/FA restent intactes. La taille reste 512 Ko, avec le même MBC1.

La validation des accents en émulation utilise une ROM temporaire contenant une ligne de contrôle ; cette ROM de test n’est pas la ROM livrée. La version livrée contient uniquement les textes du projet. L’interface Tkinter n’a pas pu être testée interactivement dans cet environnement sans affichage.

## Combat, scénario et sauvegarde — nouvelle reprise

Le premier combat a été gagné, ses gains d’expérience et d’argent affichés, puis le scénario a été traversé jusqu’aux explications dans le Talon. L’audit n’a détecté aucune lecture de glyphes à l’intérieur des anciens emplacements déplacés sur ce parcours. Il vérifie les chemins réellement exécutés ; il ne prouve pas l’exhaustivité des autres événements.

Le paramètre `16` de la commande `13` à l’adresse ROM `261F0` était inclus dans une chaîne candidate. Sa réinsertion interrompait le dialogue sur la machine temporelle. Il reste désormais intact ; le texte commence à `261F2`. Le constructeur refuse tout projet qui empiète à nouveau sur ce paramètre connu.

Deux fragments anglais de l’introduction qui échappaient à l’extraction ont été ajoutés, et une chaîne de combat tronquée a été complétée. Les verbes « utilise » ont été rétablis au présent. Les positions fixes du menu principal et les deux lignes du message de sauvegarde ont été vérifiées en émulation.

La sauvegarde dans un emplacement du jeu, la fermeture de l’émulateur et le chargement par « Reprendre » ont réussi. Le fichier RAM fait 8 192 octets et les noms/valeurs du groupe affichés après chargement correspondent à ceux d’avant la sauvegarde. Les tests utilisent une partie et des fichiers temporaires, distincts d’une éventuelle sauvegarde personnelle.

## Fichiers

- `FFL3_FR_512K.gb` : ROM modifiée de 524 288 octets.
- `FFL3_FR_512K.ips` : patch qui inclut l'extension de taille. Le logiciel d'application doit accepter les ROM agrandies.
- `project_fr.json` : 1 435 entrées extraites, avec anglais, français, octets sources et positions.
- `textes_EN_FR.txt` : export lisible du projet.
- `ffl3_editor.py` : éditeur Python avec recherche, aperçu de police, export ROM/IPS et lancement de l'émulateur.
- `runtime_audit.py` : trace des glyphes affichés et détection des lectures à l’intérieur des anciens textes déplacés.
- `RECAP_FR.md` : compte rendu de la reprise et limites de validation.
- `reprise_changes.json` : détail des 13 entrées révisées lors de cette reprise.
- `font_fr.py` : installation des glyphes et encodage des accents.
- `smoke_game.py` : essai reproductible du début du jeu et captures.
- `expanded_builder.py` : réinsertion avec changements de banques MBC1.
- `translation_source.json` : propositions françaises longues avant adaptation des menus.
- `FFL3_FR_512K.report.json`, `validation.json`, `test_expansion.py` : détails de construction et vérifications.

## ROM source requise pour reconstruire

Final Fantasy Legend III (USA), 262 144 octets.
SHA-256 : `5ed87f65225b72a74c3c04a4e5d67683fb5cc33e5f1266157350828ab973fc1d`.
Le programme refuse une autre révision. Le fichier original n'est pas inclus dans l'atelier.

## Installation et utilisation

Python 3.10 ou ultérieur, Tkinter et :

```sh
python -m pip install -r requirements.txt
python ffl3_editor.py gui "chemin/jeu_original.gb" project_fr.json
```

Sous Windows, double-cliquer sur `Ouvrir_editeur.bat`, puis sélectionner la ROM USA originale de 256 Ko dans la fenêtre de sélection. Le glisser-déposer de cette ROM sur le lanceur fonctionne aussi. Annuler la sélection ferme proprement le programme. Une ROM ou un projet inaccessible affiche un message d’erreur.

La commande `python ffl3_editor.py gui` ouvre également le sélecteur et charge le projet placé à côté de l’éditeur.
L'aperçu montre la police réelle de la ROM ; il ne simule pas les pauses, noms variables, menus ou événements. Le bouton **Jouer ROM** ouvre une ROM exportée dans PyBoy. Touches : flèches, A=`a`, B=`s`, Start=Entrée, Select=Retour arrière.

Pour reconstruire en ligne de commande :

```sh
python expanded_builder.py "chemin/jeu_original.gb" project_fr.json FFL3_FR_512K.gb
```

Les modifications effectuées dans le projet sont utilisées directement. Les commandes `[HH]` doivent rester dans le même ordre. Les champs à largeur fixe doivent conserver leur capacité ; les textes du moteur de dialogue peuvent être déplacés si leur emplacement dispose d'au moins trois octets. Les candidats sans relecture ni validation restent bloqués. En cas d'erreur, consulter le rapport avant d'utiliser une ROM précédemment exportée.

## Extension et mapper

Le mapper reste **0x03, MBC1 + RAM + batterie** ; la RAM reste **0x02**. L'indicateur ROM passe de 0x03 à **0x04**. Les sommes de contrôle sont recalculées.

573 fragments utilisent des pointeurs avec banque dans les banques 16 et 17. Le dictionnaire de compression, avec quatre entrées adaptées en français, est dans la banque 31. Un relais dans une zone libre de la banque 0 utilise les routines de changement/restauration de banque du jeu. Les pointeurs racines du scénario et les adresses des événements restent inchangés. Les libellés de menus consultés à positions fixes restent en place.

Référence technique du MBC1 : https://gbdev.io/pandocs/MBC1.html

## Audit reproductible

```sh
python runtime_audit.py FFL3_FR_512K.gb FFL3_FR_512K.report.json audit.json --cycles 1000
```

Le projet `project_fr.json` doit être dans le dossier du rapport. Le programme crée une trace JSON, une capture PNG et un état PyBoy de test. La séquence saisit volontairement un nom « AAAAAA », utilise les choix de combat par défaut et avance les dialogues. Cet essai couvre le début du jeu, pas un parcours complet.

## Vérification et limites

Onze tests passent : en-tête/sommes de contrôle, application exacte du patch IPS, conservation des pointeurs/commandes et contenu des chaînes déplacées, reconstruction identique depuis le projet, dictionnaire et son chargeur. PyBoy 2.7 a permis de vérifier le titre, l'introduction, la saisie des noms et le début du combat. Un essai avec substitution temporaire en mémoire a aussi exercé les banques 17 et 31 ; la ROM livrée n'a pas cette substitution.

1 095 emplacements textuels ont réellement changé ; 1 232 entrées sont traitées par le constructeur, certaines étant des noms conservés ou des changements de remplissage sans différence binaire. Aucun texte sélectionné n'est bloqué lors de cette construction.

Il reste des fragments anglais, des abréviations contraintes par les menus et des graphismes anglais, dont le logo. Les minuscules é, è, à, ê, â, î, ô, ù et ç sont installées. Il reste û, ë, ï et les majuscules accentuées. Les champs à largeur fixe acceptent é ; les huit autres nécessitent le moteur de dialogue et ne sont pas permis dans ces champs. L'extraction des événements contient des candidats heuristiques : l'exhaustivité et tous les chemins de dialogue ne sont pas prouvés. Aucun parcours complet, transfert de sauvegarde ou test sur console physique n'a été effectué. Cette version est une base de traduction étendue et testable, pas une version finale.

Pour exécuter les tests, placer la ROM source sous le nom `original.gb` dans ce dossier, puis :

```sh
python -m unittest discover -s . -p test_expansion.py -v
```
