Adapt.py API Reference
======================

Client and Events
-----------------

Client
~~~~~~

.. autoclass:: adapt.Client
    :members:
    :inherited-members:

Server
~~~~~~

.. autoclass:: adapt.AdaptServer
    :members:

Events
~~~~~~

.. autoclass:: adapt.client.EventDispatcher
    :members:

Event Utilities
~~~~~~~~~~~~~~~

.. autofunction:: adapt.once

.. autoclass:: adapt.ReadyEvent
    :members:

Models
------

Object
~~~~~~

.. autoclass:: adapt.Object
    :members:
    :inherited-members:

User
~~~~

.. autoclass:: adapt.User
    :members:
    :inherited-members:

ClientUser
~~~~~~~~~~

.. autoclass:: adapt.ClientUser
    :members:
    :inherited-members:

Relationship
~~~~~~~~~~~~

.. autoclass:: adapt.Relationship
    :members:
    :inherited-members:

Asset
~~~~~

.. autoclass:: adapt.Asset
    :members:
    :inherited-members:

Enums
-----

Standard Enums
~~~~~~~~~~~~~~

.. autoclass:: adapt.ModelType()
    :members:

.. autoclass:: adapt.Status()
    :members:

.. autoclass:: adapt.RelationshipType()
    :members:

.. autoclass:: adapt.ChannelType()
    :members:

Bitflag Enums
~~~~~~~~~~~~~

.. autoclass:: adapt.Bitflags
    :members:

.. autoclass:: adapt.UserFlags
    :members:

.. autoclass:: adapt.PrivacyConfiguration
    :members:

.. autoclass:: adapt.GuildFlags
    :members:

.. autoclass:: adapt.MessageFlags
    :members:

.. autoclass:: adapt.RoleFlags
    :members:

Utility Functions
-----------------

.. automodule:: adapt.util
    :members:
