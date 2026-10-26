"""Guard against missing or untranslated built-in English text."""

import re
import unittest
from string import Formatter

from src.i18n import TRANSLATIONS, get_language, set_language
from src.views.calendar_view import localized_badge


class TestEnglishTranslation(unittest.TestCase):
    def test_catalogs_and_format_fields_match(self):
        ru, en = TRANSLATIONS["ru"], TRANSLATIONS["en"]
        self.assertEqual(set(ru), set(en))
        for key in ru:
            self.assertFalse(re.search(r"[А-Яа-яЁё]", en[key]), key)
            fields = lambda value: {name for _, name, _, _ in Formatter().parse(value) if name}
            self.assertEqual(fields(ru[key]), fields(en[key]), key)

    def test_saved_badge_names_follow_selected_language(self):
        previous = get_language()
        try:
            set_language("en")
            self.assertEqual(localized_badge("Урок"), "Class")
            set_language("ru")
            self.assertEqual(localized_badge("Class"), "Урок")
        finally:
            set_language(previous)


if __name__ == "__main__":
    unittest.main()
