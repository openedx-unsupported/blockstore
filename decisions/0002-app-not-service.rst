============================================
Blockstore Deployment as an App, Not Service
============================================

------
Status
------

Pending

--------
Decision
--------

Blockstore will remain a separate application and repo, but be added as an installed app to Studio and will run in-process.

---------
Rationale
---------

Domain Driven Design
--------------------
Blockstore is a new peristence mechanism for Studio and is an implementation detail of the Content Authoring domain. Blockstore should continue to be strongly separated from a logic/code point of view, and maintain its place as something that is XBlock-agnostic.

Development and Deployment
--------------------------
Having one less service to run and configure simplifies configuration and development, and will simplify debugging (though much of the configuration overhead has been paid). It also simplifies listening for publish lifecycle signals in Studio, which will also be a common use case.

Another major change since Blockstore's initial creation is that edx-platform is now deployed to production in a truly conintuous fashion, with multiple deploys a day. This reduces the deployment advantage of having a separate service. In fact, the current state of things actually complicates some deployments where we have to make sure a certain thing is deployed first to Blockstore before it can be used by Studio.

Finally, the Arch Manifesto explicitly discourages synchronous blocking calls between services. Blockstore-as-a-service has to violate this because it is intended to be the backing store for Studio content.

Testing
-------
Keeping Blockstore as a separate app and repo means that it does not add to the runtime for edx-platform tests. At the same time, making it an installed application in the Studio process simplifies Studio-related tests that manipulate course content. We don't have to worry about maintaining a contract/mock layer that may drift out of sync, unexpected Blockstore regressions that are unaccounted for, or maintaining a separate service to be spun up for testing purposes. It also simplifies transactionality/cleanup of tests, since we can make use of Django's built-in database cleanup code and Blockstore unit tests already have a way to reset the file information stored.

Multi-Studio Support
--------------------
Early visions of Blockstore speculated a future where one Blockstore instance handled the data of multiple instances of Open edX, something that would support having Blockstore as a separate service. This vision was modified over time with the idea of content syndication where an instance of Blockstore is always tied to one particular Open edX instance as its primary, but might do replication of data in other instances. This approach simplifies both operations (those separate instances may be far away) and user permissions.

Reversibility
-------------
Blockstore is still separate app in a separate repo, with its own REST API. As long as it maintains its separation from the XBlock runtime (made easier by being in a different repo), we should be able to exract it back out into a service if makes sense to do so in the future.
