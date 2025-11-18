import json
from importlib.metadata import distributions

print(json.dumps({d.name: d.version for d in distributions()}))
