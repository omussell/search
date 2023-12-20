import json
import os
import pytest


def load_test_data(filename):
    file_path = os.path.join(os.path.dirname(
        __file__), 'test_data', filename)
    with open(file_path, 'r') as file:
        data = file.read()
    return data
