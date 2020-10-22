"""
Classes for storing Link related information in our Draft and Snapshot repos.

TODO: store.py should probably be split into its own package with this as one of
the modules in that package.
"""
from typing import List
from uuid import UUID
import codecs

import attr


@attr.s(frozen=True)
class Dependency:
    """
    A Dependency is a pointer to exactly one Bundle + Version + Snapshot.
    """
    bundle_uuid = attr.ib(type=UUID)
    version = attr.ib(type=int)
    snapshot_digest = attr.ib(type=bytes)

    @bundle_uuid.validator
    def check_type(self, attrib, value):
        if not isinstance(value, UUID):
            raise ValueError(
                "{} {} must be a UUID (not str or bytes!)".format(attrib, value)
            )

    @classmethod
    def from_json_dict(cls, json_dict):
        """Parse Dependency from a dict."""
        return cls(
            bundle_uuid=UUID(json_dict["bundle_uuid"]),
            version=json_dict["version"],
            snapshot_digest=bytes_from_hex_str(json_dict["snapshot_digest"]),
        )


@attr.s(frozen=True)
class Link:
    """
    A Link is a named Dependency + all of its transitive dependencies.

    Links are named because it's totally fine to have Links that point to
    different versions of a Bundle (e.g Bundle Av1, Bundle Av2), but we want
    some stable way of identifying and differentiating between those references.

    The indirect dependencies are a flat list. We don't try to keep track of all
    the nested dependency relations. Instead, we want the Link to answer the
    question of "If I wanted to download this entire Bundle and all the things
    it links to, what is the complete list of other BundleVersions that I have
    to download to get all the dependencies?
    """
    name = attr.ib(type=str)
    direct_dependency = attr.ib(type=Dependency)
    indirect_dependencies = attr.ib(type=list)


class LinkCycleError(ValueError):
    """Raise when an action would create a cycle between two BundleVersions."""


class LinkCollection:
    """
    This data structure has to hold all dependencies for a Bundle.

    `LinkCollection` is immutable. Calling `with_updated_link()` and passing in
    a new `Link` will return a new `LinkCollection` rather than modifying the
    object in place.

    There are a few critical query patterns that we have to support here:

    1. Quickly return the entire set of things that needs to be downloaded. This
    is useful when we want to do an export of some sort.

    2. Determine if there is a Link cycle. Cycles break our assumptions and will
    lead us to endlessly prompt for updates, so we have to prevent them from
    happening.

    3. Add a new Link (and all of its transitive Dependencies).
    """
    def __init__(self, bundle_uuid: UUID, links: List[Link]):
        """
        Initialize with a `bundle_uuid` and list of Link objects.

        Will raise a ValueError if the data is malformed in some way (duplicate
        Link names or dependency cycles).
        """
        self._check_for_duplicates(links)
        self._check_for_cycles(bundle_uuid, links)

        self.bundle_uuid = bundle_uuid
        self.names_to_links = {link.name: link for link in links}

    def __eq__(self, other):
        return (
            self.bundle_uuid == other.bundle_uuid and
            self.names_to_links == other.names_to_links
        )

    def __getitem__(self, name):
        return self.names_to_links[name]

    def __iter__(self):
        return iter(self.names_to_links.values())

    def __bool__(self):
        return bool(self.names_to_links)

    @classmethod
    def from_json_dict(cls, bundle_uuid, json_dict):
        """Parse LinkCollection from a dict."""
        def _parse_dep(dep_info):
            return Dependency(
                bundle_uuid=UUID(dep_info['bundle_uuid']),
                version=dep_info['version'],
                snapshot_digest=bytes_from_hex_str(dep_info['snapshot_digest'])
            )

        links = []
        for link_name, link_info in json_dict.items():
            direct_dep = _parse_dep(link_info['direct'])
            indirect_deps = [_parse_dep(dep_info) for dep_info in link_info['indirect']]
            links.append(
                Link(link_name, direct_dep, indirect_deps)
            )

        return LinkCollection(bundle_uuid, links)

    def get_direct_dep(self, name):
        link = self.names_to_links.get(name)
        if link:
            return link.direct_dependency
        return None

    def _check_for_duplicates(self, links):
        seen_names = set()
        for link in links:
            if link.name in seen_names:
                raise ValueError(
                    "Duplicate link name not allowed: {}".format(link.name)
                )

    def _check_for_cycles(self, bundle_uuid, links):
        """
        Check for link cycles (when a bundle's links have links [that have
        links...] that point back to the bundle.)
        """
        for link in links:
            if link.direct_dependency == bundle_uuid:
                raise LinkCycleError(
                    "A Bundle cannot have any version of itself as a dependency (see Link {})."
                    .format(link.name)
                )
            for dep in link.indirect_dependencies:
                if dep.bundle_uuid == bundle_uuid:
                    raise LinkCycleError(
                        "Cycle detected: Link {} requires Bundle {}"
                        .format(link.name, bundle_uuid)
                    )

    def all_dependencies(self):
        dependencies = set(link.direct_dependency for link in self)
        for link in self:
            dependencies |= set(link.indirect_dependencies)
        return list(sorted(dependencies))

    def with_updated_link(self, link):
        return self.with_updated_links([link])

    def with_updated_links(self, links, deletes=None):
        """Return a new LinkCollection combining self with overrides from links."""
        deletion_set = set(deletes or [])
        names_to_links = {
            link.name: link for link in self if link.name not in deletion_set
        }
        for link in links:
            names_to_links[link.name] = link
        return LinkCollection(self.bundle_uuid, names_to_links.values())


class LinkChangeSet:
    """
    Changes we want to make to a given LinkCollection.
    """
    def __init__(self, puts, deletes):
        """
        `puts` is an iterable of Links. We're going to create these Links if
        they don't exist, and update them if they do.

        `deletes` is an iterable of the names of Links that we're going to
        delete.

        Putting the same key in both `puts` and `deletes` will raise a
        `ValueError`.
        """
        self.puts = puts
        self.deletes = deletes
        self.modified_set = set(p.name for p in puts) | set(deletes)

        overlap = set(p.name for p in puts) & set(deletes)
        if overlap:
            raise ValueError(
                "Keys marked for both PUT and DELETE: {}".format(
                    ", ".join(overlap)
                )
            )

    def __eq__(self, other):
        return (self.puts == other.puts) and (self.deletes == other.deletes)

    def apply_to(self, links):
        """Return new LinkCollection with our changes applied to `links`."""
        return links.with_updated_links(self.puts, self.deletes)

    @classmethod
    def from_json_dict(cls, json_dict):
        """Parse LinkChangeSet from a dict."""
        puts = []
        deletes = []
        for name, link_info in json_dict.items():
            if link_info is None:
                deletes.append(name)
            else:
                link = Link(
                    name=name,
                    direct_dependency=Dependency.from_json_dict(
                        link_info["direct"]
                    ),
                    indirect_dependencies=[
                        Dependency.from_json_dict(indirect_dep_info)
                        for indirect_dep_info in link_info["indirect"]
                    ]
                )
                puts.append(link)

        return cls(puts, deletes)


# TODO: Move this into common util after we refactor things into a store package
def bytes_from_hex_str(hex_str):
    """Return bytes given a hexidecimal string representation of binary data."""
    if hex_str is None:
        return None
    return codecs.decode(hex_str, 'hex')
