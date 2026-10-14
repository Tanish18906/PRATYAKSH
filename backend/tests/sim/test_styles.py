import unittest

from app.sim.styles import format_profile, render_csv, render_value


class StyleTests(unittest.TestCase):
    def test_profiles_only_include_present_columns(self):
        columns = ["phone", "full_name", "created_at"]
        etl = format_profile("ETL", columns)
        self.assertEqual(etl["columns"], {
            "phone": {"style": "e164_dash"},
            "full_name": {"case": "title"},
            "created_at": {"style": "iso"},
        })
        self.assertEqual(etl["delimiter"], ",")
        self.assertEqual(etl["line_ending"], "LF")
        self.assertEqual(format_profile("MARKETING", ["email"])["columns"],
                         {"email": {"case": "lower"}})

    def test_render_vectors(self):
        phone = "9876543221"
        self.assertEqual(render_value("phone", phone, "ETL"), "+91-9876543221")
        self.assertEqual(render_value("phone", phone, "CONTRACTOR"), phone)
        self.assertEqual(render_value("phone", phone, "MARKETING"), "+91 98765 43221")
        self.assertEqual(render_value("signup_date", "2026-10-08", "ETL"), "2026-10-08")
        self.assertEqual(render_value("signup_date", "2026-10-08", "CONTRACTOR"), "08/10/2026")
        self.assertEqual(render_value("dob", "2026-10-08", "MARKETING"), "10-08-26")
        self.assertEqual(render_value("created_at", "2026-10-08T17:42:09Z", "CONTRACTOR"),
                         "2026-10-08T17:42:09Z")
        self.assertEqual(render_value("full_name", "Arohan Vey", "CONTRACTOR"), "AROHAN VEY")
        self.assertEqual(render_value("full_name", "Arohan Vey", "NOTEBOOK"), "arohan vey")

    def test_mixed_email_is_stable_and_varies_by_row(self):
        values = [render_value("email", "name@example.com", "CONTRACTOR", i)
                  for i in range(40)]
        self.assertIn("name@example.com", values)
        self.assertIn("Name@example.com", values)
        self.assertEqual(values,
                         [render_value("email", "name@example.com", "CONTRACTOR", i)
                          for i in range(40)])

    def test_csv_style_and_nulls(self):
        rows = [{"full_name": "Arohan, Vey", "phone": "9876543221", "city": None}]
        columns = ["full_name", "phone", "city"]
        etl = render_csv(rows, columns, "ETL")
        self.assertEqual(etl, b'full_name,phone,city\n"Arohan, Vey",+91-9876543221,\n')
        contractor = render_csv(rows, columns, "CONTRACTOR")
        self.assertTrue(contractor.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(contractor.decode("utf-8-sig"),
                         '"Full Name","Phone","City"\r\n"AROHAN, VEY","9876543221","NULL"\r\n')
        marketing = render_csv([{"phone": "9876543221", "city": "Raipur"}],
                               ["phone", "city"], "MARKETING")
        self.assertEqual(marketing, b"Phone;City\n+91 98765 43221;Raipur\n")
        notebook = render_csv([], ["full_name"], "NOTEBOOK")
        self.assertEqual(notebook, b"fullName\n")


if __name__ == "__main__":
    unittest.main()
