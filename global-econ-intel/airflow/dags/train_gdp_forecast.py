"""Day 2, Step 5 - nightly GDP forecast training. Logic lives in _training_dag_factory.py."""
from _training_dag_factory import build_training_dag

dag = build_training_dag("gdp")
