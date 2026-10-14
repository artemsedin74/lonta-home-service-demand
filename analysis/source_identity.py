"""Pin input CSV contents independently of download ZIP compression/timestamps."""
import hashlib
import zipfile

EXPECTED_CSV_HASHES={
    'household.csv':'ea2ee307fa14b2723aab9453f89fe4c0cf803a839214fb5b36a74e07c770b9db',
    'project.csv':'9efda82d10024a78f53018a2daaef46b58c6e22911f236587973c92b2c13ed49',
}


def verify_csv_archive(path, expected=EXPECTED_CSV_HASHES):
    observed={}
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            raise ValueError('Input ZIP CRC failed')
        for name,digest in expected.items():
            if z.namelist().count(name)!=1:
                raise ValueError('Missing or duplicate source CSV')
            with z.open(name) as stream:
                observed[name]=hashlib.file_digest(stream,'sha256').hexdigest()
            if observed[name]!=digest:
                raise ValueError(f'{name}: source bytes differ from the pinned archive; review source edition first')
    return observed
