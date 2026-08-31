import os

# The application fails closed by default. Unit tests intentionally exercise
# the synthetic in-memory contract surface, so they opt in before app imports.
os.environ["ENABLE_DEMO_ROUTES"] = "true"
