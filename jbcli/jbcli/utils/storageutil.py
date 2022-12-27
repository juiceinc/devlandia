import toml
import os


__all__ = ["Stash", "stash"]


class Stash(object):
    """A wrapper for storing config in a toml file."""

    def __init__(self, stash_filename="~/.config/juicebox/devlandia.toml"):
        self.local_filename = os.path.abspath(os.path.expanduser(stash_filename))
        stash_dir = os.path.dirname(self.local_filename)
        if not os.path.exists(stash_dir):
            os.makedirs(stash_dir)

    @property
    def data(self):
        try:
            with open(self.local_filename) as f:
                return toml.loads(f.read())
        except IOError:
            return {}

    def get(self, name, default=None):
        """Get a secret directly from the local file."""
        try:
            return self.data.get(name, default)
        except IOError:
            pass

    def put(self, name, value):
        data = self.data
        data[name] = value
        with open(self.local_filename, "w") as f:
            f.write(toml.dumps(data))
        return data


stash = Stash()
