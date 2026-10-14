import unittest, importlib, importlib.util, tempfile, zipfile, hashlib
from pathlib import Path


class SourceIdentityTests(unittest.TestCase):
    def core(self):
        self.assertIsNotNone(importlib.util.find_spec('source_identity'), 'CSV identity guard missing')
        return importlib.import_module('source_identity')

    def test_identical_csvs_survive_different_zip_containers(self):
        with tempfile.TemporaryDirectory() as temp:
            expected={'household.csv':hashlib.sha256(b'homes').hexdigest(),'project.csv':hashlib.sha256(b'jobs').hexdigest()}
            for compression in [zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED]:
                p=Path(temp)/f'{compression}.zip'
                with zipfile.ZipFile(p,'w',compression=compression) as z:
                    z.writestr('household.csv',b'homes');z.writestr('project.csv',b'jobs')
                self.assertEqual(self.core().verify_csv_archive(p,expected),expected)

    def test_valid_zip_with_changed_project_bytes_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'input.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('household.csv',b'homes');z.writestr('project.csv',b'changed')
            expected={'household.csv':hashlib.sha256(b'homes').hexdigest(),'project.csv':hashlib.sha256(b'jobs').hexdigest()}
            with self.assertRaises(ValueError):self.core().verify_csv_archive(p,expected)


if __name__=='__main__': unittest.main()
