from pathlib import Path
import shutil

test_folder = Path(__file__).parent


for f in test_folder.rglob('*'):
    if f.suffix not in  ('.py', ''):
        if f.name in (
            'shayesteh.EDB',
            'test.EDB',
            'pytest.ini',
            
        ):
            continue
        else:
            f.unlink()

shutil.rmtree(test_folder / 'etabs_api' / '.pytest_cache')



