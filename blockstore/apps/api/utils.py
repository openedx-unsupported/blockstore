"""
Utility functions for the Blockstore API.
"""

from django.utils.datastructures import MultiValueDict


class ZippableMultiValueDict(MultiValueDict):

    def zip(self):
        """
        Returns a list of dicts using the keys and values lists.
        """
        zipped = []
        for key in self.keys():
            for idx, value in enumerate(self.getlist(key)):
                if len(zipped) <= idx:
                    zipped.append({})
                zipped[idx][key] = value
        return zipped
