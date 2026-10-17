ATTENTION : L'APP EST DÉSORMAIS PUBLIQUE MAIS LES INFORMATIONS INDIVIDUELLES NE SONT PAS TOUTES À JOUR - NOUS FERONS LA MISE À JOUR PROCHAINEMENT

# Tour de France CNU

L'application pour afficher les universités et les candidats sur la carte de France est disponible sur : https://tinyurl.com/TourDeFrancePEA

## Photos

Vous pouvez ajouter votre photo dans le dossier `photos/`.

Attention, il faut bien mettre le nom de la photo sous cette forme sinon vous ne serez pas reconnu :

`Prenom_Nom.jpg`
`Prenom-Composé_Nom.jpg`

Exemple :

`Blaise_Pascal.jpg`
`Blaise-Robert_Pascal.jpg`

(Les accents et espaces sont gérés partiellement, mais il est préférable d’utiliser ce format simple)


Disponible sur : https://tinyurl.com/TourDeFrancePEA

(Ou par le lien complet : https://tour-france-cnu-rcs7zanlfmax3jymteuhos.streamlit.app/)

## Présentation et données

Les données proviennent de l’onglet `gid=0` du [tableau Google Sheets](https://docs.google.com/spreadsheets/d/17u0RMvtud4-uERfHmyb5N_FGqZSLlIQloUTxPtUg2e0/edit?gid=0).
Le bandeau affiche les corps dans l’ordre PU-PH, MCU-PH, PHU, PA, MCA, PA-T, MCA-T ; les catégories temporaires sont comptées séparément.

Le logo `assets/cnu.png` provient du [site officiel du CNU](https://conseil-national-des-universites.fr/cnu/assets/images/cnu.png) et est conservé dans le dépôt pour garantir son affichage.
Les liens « CNU PEA » et « Guide » renvoient actuellement à la même page, conformément aux adresses fournies. Le lien du guide peut être modifié via `GUIDE_URL` dans `app.py`.
