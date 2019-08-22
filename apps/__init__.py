import importlib
import os

current_directory = os.path.dirname(os.path.realpath(__file__))

list_of_apps = [
    x for x in os.listdir(current_directory)
    if os.path.isdir(os.path.join(current_directory, x))
       and not x.startswith('.')
       and x != '__pycache__']

for app in list_of_apps:
    if 'builds' not in app:
        importlib.import_module('apps.{0}'.format(app))
