"""
Utility functions for the Blockstore API.
"""

from django.utils.datastructures import MultiValueDict


class ZippableMultiValueDict(MultiValueDict):
    """
    Enhances the MultiValueDict data structure to allow the grouping of multiple related values.

    For example, consider the following querystring which might add multiple people to a dataset:
        http://localhost?name=Abby&age=12&goal=astronaut&name=Bobby&age=14&name=Catherine&ambition=heiress

    When this request is parsed, the resulting MultiValueDict will look like this:
        {
            'name': ['Abby', 'Bobby', 'Catherine'],
            'age': [12, 14],
            'ambition': ['astronaut', 'heiress'],
        }

    But really, we want each of these fields to be associated with a single person.  This is achieved with the `zip`
    function added by this class.  The fields are collected in order, and missing values are not provided in the
    resulting dicts.  E.g.,
        [
            {
                'name': 'Abby',
                'age': 12,
                'ambition': 'astronaut',
            },
            {
                'name': 'Bobby',
                'age': 14,
                'ambition': 'heiress',
            },
            {
                'name': 'Catherine',
            },
        ]

    Note that to maintain the alignment implied by the original querystring, we need to use a placeholder:

        http://localhost?name=Abby&age=12&goal=astronaut&name=Bobby&age=14&ambition=&name=Catherine&ambition=heiress

    Resulting in this MultiValueDict.zip():
        [
            {
                'name': 'Abby',
                'age': 12,
                'ambition': 'astronaut',
            },
            {
                'name': 'Bobby',
                'age': 14,
            },
            {
                'name': 'Catherine',
                'ambition': 'heiress',
            },
        ]

    """
    def zip(self):
        """
        Returns a list of dicts created by collecting the keys and values lists in the order received.
        """
        zipped = []
        for key in self.keys():
            for idx, value in enumerate(self.getlist(key)):
                if len(zipped) <= idx:
                    zipped.append({})
                zipped[idx][key] = value
        return zipped
