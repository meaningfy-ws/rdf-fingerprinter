import unittest

from fingerprint.df_tex_utils import url_local_split


class MyTestCase(unittest.TestCase):
    def url_split(self):
        self.assertEqual(url_local_split("http://sdffffg.comamde+ddffg.cdep._erere?dfdf#asdf",
                                         ("http://sdffffg.comamde+ddffg.cdep._erere?dfdf#", "#asdf")))
        self.assertEqual(url_local_split("http://sdffffg.comamde+ddffg.cdep._erere?dfdf/asdf",
                                         ("http://sdffffg.comamde+ddffg.cdep._erere?dfdf/", "asdf")))
        self.assertEqual(url_local_split("http://sdffffg.comamde+ddffg.cdep._erere?dfdf/asdf/",
                                         ("http://sdffffg.comamde+ddffg.cdep._erere?dfdf/asdf/", "")))


if __name__ == '__main__':
    unittest.main()
