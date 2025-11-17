# build
python -m pip install --upgrade pip setuptools wheel

# uploading
python -m pip install --upgrade twine build

# build
python -m build


# upload for testing
python -m twine upload --repository testpypi dist/* --verbose

# upload for real
python -m twine upload dist/*
