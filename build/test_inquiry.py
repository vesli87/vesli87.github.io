"""Public inquiry choices must remain valid, translated and script-safe."""
import copy
import json
import unittest
from unittest.mock import patch

import core as C
import render as R
import pages as PG
import build as B


class InquiryTests(unittest.TestCase):
    def test_context_is_embedded_without_search_or_analytics_dependency(self):
        for lang in C.LANGS:
            config = json.loads(R.boot_json(lang)[len("window.VT="):-1])
            catalog = config["inquiryCatalog"]
            self.assertEqual(set(catalog), {p["id"] for p in C.P})
            self.assertEqual(catalog["plasmafix-51"]["kind"], "unit")
            self.assertEqual(len(catalog["plasmafix-51"]["options"]), 3)
            self.assertEqual(config["inquiryServices"]["repair"]["u"], C.u_service(lang, "repair"))
            self.assertEqual(set(config["inquiryServices"]), {"repair", "calib", "auto", "overview"})

    def test_choice_validation_rejects_unknown_duplicate_and_partial_data(self):
        original = C.INQUIRY_OPTIONS
        variants = []
        invalid = copy.deepcopy(original)
        invalid["unknown-product"] = copy.deepcopy(invalid["mms"])
        variants.append(invalid)
        invalid = copy.deepcopy(original)
        invalid["mms"]["options"].append(copy.deepcopy(invalid["mms"]["options"][0]))
        variants.append(invalid)
        invalid = copy.deepcopy(original)
        del invalid["mms"]["options"][0]["label"]["fr"]
        variants.append(invalid)
        invalid = copy.deepcopy(original)
        invalid["plasmafix-51"]["availability"]["count"] = True
        variants.append(invalid)
        invalid = copy.deepcopy(original)
        invalid["plasmafix-51"]["availability"]["confirmed_on"] = "2026-02-31"
        variants.append(invalid)
        for invalid in variants:
            with patch.object(C, "INQUIRY_OPTIONS", invalid):
                with self.assertRaises(ValueError):
                    C.inquiry_options()

    def test_choice_text_cannot_close_script_or_create_markup(self):
        choices = copy.deepcopy(C.INQUIRY_OPTIONS)
        injected = '</script><img src=x onerror="alert(1)">'
        choices["mms"]["options"][0]["label"]["de"] = injected
        with patch.object(C, "INQUIRY_OPTIONS", choices):
            boot = R.boot_json("de")
            self.assertNotIn("</script>", boot)
            self.assertIn("\\u003c", boot)
            product = next(p for p in C.P if p["id"] == "mms")
            self.assertNotIn(injected, R.inquiry_product_choices("de", product))

    def test_services_are_searchable_in_each_language_and_have_context_cta(self):
        for lang in C.LANGS:
            services = B.search_index(lang)["services"]
            self.assertEqual({row["i"] for row in services}, {"repair", "calib", "auto", "overview"})
            for row in services:
                self.assertTrue(row["t1"])
                self.assertTrue(row["d"])
                key = None if row["i"] == "overview" else row["i"]
                url, html = PG.page_service(lang, key)
                self.assertEqual(row["u"], url)
                self.assertIn(C.u_page(lang, "contact") + "?service=" + row["i"], html)


if __name__ == "__main__":
    unittest.main()
