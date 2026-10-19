import unittest

from affiliations import (
    Affiliation, affiliations_html, build_affiliations, match_person,
    matches_search, name_index, practitioner_key, search_text,
)


class AffiliationTests(unittest.TestCase):
    def setUp(self):
        self.roster = [
            {"Prénom": "Carmen", "Nom": "Schröder"},
            {"Prénom": "Marie-Aude", "Nom": "Piot"},
            {"Prénom": "Charles Edouard", "Nom": "Notredame"},
            {"Prénom": "Lauriane", "Nom": "Vulliez Coady"},
            {"Prénom": "Angèle", "Nom": "Manesse-Consoli"},
            {"Prénom": "Gisèle", "Nom": "APTER"},
            {"Prénom": "Diane", "Nom": "Purper Ouakil"},
            {"Prénom": "Sylvie", "Nom": "Viaux-Savelon"},
        ]

    def test_initials_accents_and_checked_short_surnames(self):
        aliases = name_index(self.roster)
        for source, person in zip(
            ["C. Schroder", "M.A Piot", "C.E. Notredame", "L.Vulliez", "A. Consoli"],
            self.roster,
        ):
            with self.subTest(source=source):
                self.assertEqual(match_person(source, aliases)[0], practitioner_key(person["Prénom"], person["Nom"]))

    def test_ambiguous_initials_and_unconfirmed_spelling_are_not_assigned(self):
        aliases = name_index(self.roster + [{"Prénom": "Charlotte", "Nom": "Schröder"}])
        self.assertIsNone(match_person("C. Schroder", aliases)[0])
        self.assertEqual(match_person("Carmen Schröder", aliases)[0], "carmen:schroder")
        self.assertIsNone(match_person("S. Viaud", aliases)[0])
        self.assertIsNone(match_person("C. Schroder-Dupont", aliases)[0])

    def test_roles_parentheses_and_unmatched_name_do_not_cross_people(self):
        rows = [
            ["SOCIÉTÉS SAVANTES", "INTERNATIONALES", "WPA", "G Apter, International Distinguished Fellow"],
            ["", "", "ISSPD", "G Apter (EuropeanSSPD, Section Borderline PD and Parenthood)"],
            ["", "", "Eunethydis", "Diane Purper-Ouakil membre du bureau, vice présidente"],
            ["", "", "WAIMH", "S. Viaud, G Apter"],
        ]
        entries, unmatched = build_affiliations(rows, self.roster)
        self.assertEqual(entries["gisele:apter"][0].detail, "International Distinguished Fellow")
        self.assertEqual(entries["gisele:apter"][1].detail, "EuropeanSSPD, Section Borderline PD and Parenthood")
        self.assertEqual(entries["diane:purperouakil"][0].detail, "membre du bureau, vice présidente")
        self.assertEqual([(u.name, u.affiliation) for u in unmatched], [("S. Viaud", "WAIMH")])
        self.assertNotIn("sylvie:viauxsavelon", entries)

    def test_labels_scope_and_dates(self):
        rows = [
            ["INSTANCES", "INTERNATIONALES", "Instance A", "M.A Piot"],
            ["", "NATIONALES", "CNU", "M.A Piot"],
            ["ASSOCIATIONS - LABORATOIRES - RÉSEAUX", "INTERNATIONALES", "Qualab", "M.A Piot,"],
            ["RESPONSABILITÉS POUR L'UNIVERSITÉ", "NATIONALES", "Conseil", "M.A Piot"],
            ["REVUES (éditeurs)", "INTERNATIONALES", "Revue A", "M.A Piot"],
            ["ORGANISATION DE CONGRÈS - COLLOQUES - SEMINAIRES", "INTERNATIONAUX", "NOMS", "HU affiliés", "DATES HABITUELLES"],
            ["", "", "Congrès A", "M.A Piot", "Juillet"],
            ["", "", "Sans participant", "", "Mai"],
        ]
        entries, unmatched = build_affiliations(rows, self.roster)
        self.assertFalse(unmatched)
        self.assertEqual(len(entries["marieaude:piot"]), 6)
        self.assertEqual({e.label for e in entries["marieaude:piot"]}, {
            "Instance internationale", "Instance nationale", "Réseau", "Revue", "Organisation", "Responsabilité pour l’Université",
        })
        self.assertEqual(next(e.dates for e in entries["marieaude:piot"] if e.label == "Organisation"), "Juillet")

    def test_search_covers_roles_affiliations_and_literal_characters(self):
        person = {"Prénom": "Marie-Aude", "Nom": "Piot", "Université": "Paris Cité", "Corps": "MCU-PH"}
        text = search_text(person, [Affiliation("Société savante internationale", "EPA", "Présidente de section")])
        for query in ("EPA", "presidente", "PIOT cité", "internationale", "  "):
            self.assertTrue(matches_search(text, query))
        self.assertFalse(matches_search(text, "CNU"))
        self.assertFalse(matches_search(text, "["))

    def test_source_text_is_escaped_and_empty_state_does_not_claim_no_affiliations(self):
        html = affiliations_html([Affiliation("Revue", '<script>alert("x")</script>', "A & B")])
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("A &amp; B", html)
        self.assertIn("Affiliations non renseignées", affiliations_html([]))


if __name__ == "__main__":
    unittest.main()
