# engine/interfaces.py
# Copyright (C) 2005-2022 the SQLAlchemy authors and contributors
# <see AUTHORS file>
#
# This module is part of SQLAlchemy and is released under
# the MIT License: https://www.opensource.org/licenses/mit-license.php

"""Define core interfaces used by the engine system."""

from enum import Enum
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import Union

from ..pool import PoolProxiedConnection
from ..sql.compiler import Compiled  # noqa
from ..sql.compiler import TypeCompiler  # noqa
from ..util.concurrency import await_only
from ..util.typing import _TypeToInstance
from ..util.typing import NotRequired
from ..util.typing import Protocol
from ..util.typing import TypedDict

if TYPE_CHECKING:
    from .base import Connection
    from .base import Engine
    from .url import URL
    from ..sql.compiler import DDLCompiler
    from ..sql.compiler import IdentifierPreparer
    from ..sql.compiler import SQLCompiler
    from ..sql.type_api import TypeEngine


class DBAPIConnection(Protocol):
    """protocol representing a :pep:`249` database connection.

    .. versionadded:: 2.0

    .. seealso::

        `Connection Objects <https://www.python.org/dev/peps/pep-0249/#connection-objects>`_
        - in :pep:`249`

    """  # noqa: E501

    def close(self) -> None:
        ...

    def commit(self) -> None:
        ...

    def cursor(self) -> "DBAPICursor":
        ...

    def rollback(self) -> None:
        ...


class DBAPIType(Protocol):
    """protocol representing a :pep:`249` database type.

    .. versionadded:: 2.0

    .. seealso::

        `Type Objects <https://www.python.org/dev/peps/pep-0249/#type-objects>`_
        - in :pep:`249`

    """  # noqa: E501


class DBAPICursor(Protocol):
    """protocol representing a :pep:`249` database cursor.

    .. versionadded:: 2.0

    .. seealso::

        `Cursor Objects <https://www.python.org/dev/peps/pep-0249/#cursor-objects>`_
        - in :pep:`249`

    """  # noqa: E501

    @property
    def description(
        self,
    ) -> Sequence[
        Tuple[
            str,
            "DBAPIType",
            Optional[int],
            Optional[int],
            Optional[int],
            Optional[int],
            Optional[bool],
        ]
    ]:
        """The description attribute of the Cursor.

        .. seealso::

            `cursor.description <https://www.python.org/dev/peps/pep-0249/#description>`_
            - in :pep:`249`


        """  # noqa: E501
        ...

    @property
    def rowcount(self) -> int:
        ...

    arraysize: int

    def close(self) -> None:
        ...

    def execute(
        self,
        operation: Any,
        parameters: Optional[Union[Sequence[Any], Mapping[str, Any]]],
    ) -> Any:
        ...

    def executemany(
        self,
        operation: Any,
        parameters: Sequence[Union[Sequence[Any], Mapping[str, Any]]],
    ) -> Any:
        ...

    def fetchone(self) -> Optional[Any]:
        ...

    def fetchmany(self, size: int = ...) -> Sequence[Any]:
        ...

    def fetchall(self) -> Sequence[Any]:
        ...

    def setinputsizes(self, sizes: Sequence[Any]) -> None:
        ...

    def setoutputsize(self, size: Any, column: Any) -> None:
        ...

    def callproc(self, procname: str, parameters: Sequence[Any] = ...) -> Any:
        ...

    def nextset(self) -> Optional[bool]:
        ...


class ReflectedIdentity(TypedDict):
    """represent the reflected IDENTITY structure of a column, corresponding
    to the :class:`_schema.Identity` construct.

    The :class:`.ReflectedIdentity` structure is part of the
    :class:`.ReflectedColumn` structure, which is returned by the
    :meth:`.Inspector.get_columns` method.

    """

    always: bool
    """type of identity column"""

    on_null: bool
    """indicates ON NULL"""

    start: int
    """starting index of the sequence"""

    increment: int
    """increment value of the sequence"""

    minvalue: int
    """the minimum value of the sequence."""

    maxvalue: int
    """the maximum value of the sequence."""

    nominvalue: bool
    """no minimum value of the sequence."""

    nomaxvalue: bool
    """no maximum value of the sequence."""

    cycle: bool
    """allows the sequence to wrap around when the maxvalue
    or minvalue has been reached."""

    cache: Optional[int]
    """number of future values in the
    sequence which are calculated in advance."""

    order: bool
    """if true, renders the ORDER keyword."""


class ReflectedComputed(TypedDict):
    """Represent the reflected elements of a computed column, corresponding
    to the :class:`_schema.Computed` construct.

    The :class:`.ReflectedComputed` structure is part of the
    :class:`.ReflectedColumn` structure, which is returned by the
    :meth:`.Inspector.get_columns` method.

    """

    sqltext: str
    """the expression used to generate this column returned
    as a string SQL expression"""

    persisted: bool
    """indicates if the value is stored or computed on demand"""


class ReflectedColumn(TypedDict):
    """Dictionary representing the reflected elements corresponding to
    a :class:`_schema.Column` object.

    The :class:`.ReflectedColumn` structure is returned by the
    :class:`.Inspector.get_columns` method.

    """

    name: str
    """column name"""

    type: "TypeEngine"
    """column type represented as a :class:`.TypeEngine` instance."""

    nullable: bool
    """column nullability"""

    default: str
    """column default expression as a SQL string"""

    autoincrement: NotRequired[bool]
    """database-dependent autoincrement flag.

    This flag indicates if the column has a database-side "autoincrement"
    flag of some kind.   Within SQLAlchemy, other kinds of columns may
    also act as an "autoincrement" column without necessarily having
    such a flag on them.

    See :paramref:`_schema.Column.autoincrement` for more background on
    "autoincrement".

    """

    comment: NotRequired[Optional[str]]
    """comment for the column, if present"""

    computed: NotRequired[Optional[ReflectedComputed]]
    """indicates this column is computed at insert (possibly update) time by
    the database."""

    identity: NotRequired[Optional[ReflectedIdentity]]
    """indicates this column is an IDENTITY column"""

    dialect_options: NotRequired[Dict[str, Any]]
    """Additional dialect-specific options detected for this reflected
    object"""


class ReflectedCheckConstraint(TypedDict):
    """Dictionary representing the reflected elements corresponding to
    :class:`.CheckConstraint`.

    The :class:`.ReflectedCheckConstraint` structure is returned by the
    :meth:`.Inspector.get_check_constraints` method.

    """

    name: Optional[str]
    """constraint name"""

    sqltext: str
    """the check constraint's SQL expression"""

    dialect_options: NotRequired[Dict[str, Any]]
    """Additional dialect-specific options detected for this reflected
    object"""


class ReflectedUniqueConstraint(TypedDict):
    """Dictionary representing the reflected elements corresponding to
    :class:`.UniqueConstraint`.

    The :class:`.ReflectedUniqueConstraint` structure is returned by the
    :meth:`.Inspector.get_unique_constraints` method.

    """

    name: Optional[str]
    """constraint name"""

    column_names: List[str]
    """column names which comprise the constraint"""

    dialect_options: NotRequired[Dict[str, Any]]
    """Additional dialect-specific options detected for this reflected
    object"""


class ReflectedPrimaryKeyConstraint(TypedDict):
    """Dictionary representing the reflected elements corresponding to
    :class:`.PrimaryKeyConstraint`.

    The :class:`.ReflectedPrimaryKeyConstraint` structure is returned by the
    :meth:`.Inspector.get_pk_constraint` method.

    """

    name: Optional[str]
    """constraint name"""

    constrained_columns: List[str]
    """column names which comprise the constraint"""

    dialect_options: NotRequired[Dict[str, Any]]
    """Additional dialect-specific options detected for this reflected
    object"""


class ReflectedForeignKeyConstraint(TypedDict):
    """Dictionary representing the reflected elements corresponding to
    :class:`.ForeignKeyConstraint`.

    The :class:`.ReflectedForeignKeyConstraint` structure is returned by
    the :meth:`.Inspector.get_foreign_keys` method.

    """

    name: Optional[str]
    """constraint name"""

    constrained_columns: List[str]
    """local column names which comprise the constraint"""

    referred_schema: Optional[str]
    """schema name of the table being referenced"""

    referred_table: str
    """name of the table being referenced"""

    referred_columns: List[str]
    """referenced column names"""

    dialect_options: NotRequired[Dict[str, Any]]
    """Additional dialect-specific options detected for this reflected
    object"""


class ReflectedIndex(TypedDict):
    """Dictionary representing the reflected elements corresponding to
    :class:`.Index`.

    The :class:`.ReflectedIndex` structure is returned by the
    :meth:`.Inspector.get_indexes` method.

    """

    name: Optional[str]
    """constraint name"""

    column_names: List[str]
    """column names which the index refers towards"""

    unique: bool
    """whether or not the index has a unique flag"""

    duplicates_constraint: NotRequired[bool]
    """boolean indicating this index mirrors a unique constraint of the same
    name"""

    include_columns: NotRequired[List[str]]
    """columns to include in the INCLUDE clause for supporting databases.

    .. deprecated:: 2.0

        Legacy value, will be replaced with
        ``d["dialect_options"][<dialect name>]["include"]``

    """

    column_sorting: NotRequired[Dict[str, Tuple[str]]]
    """optional dict mapping column names to tuple of sort keywords,
    which may include ``asc``, ``desc``, ``nulls_first``, ``nulls_last``."""

    dialect_options: NotRequired[Dict[str, Any]]
    """Additional dialect-specific options detected for this reflected
    object"""


class ReflectedTableComment(TypedDict):
    """Dictionary representing the reflected comment corresponding to
    the :attr:`_schema.Table.comment` attribute.

    The :class:`.ReflectedTableComment` structure is returned by the
    :meth:`.Inspector.get_table_comment` method.

    """

    text: str
    """text of the comment"""


class BindTyping(Enum):
    """Define different methods of passing typing information for
    bound parameters in a statement to the database driver.

    .. versionadded:: 2.0

    """

    NONE = 1
    """No steps are taken to pass typing information to the database driver.

    This is the default behavior for databases such as SQLite, MySQL / MariaDB,
    SQL Server.

    """

    SETINPUTSIZES = 2
    """Use the pep-249 setinputsizes method.

    This is only implemented for DBAPIs that support this method and for which
    the SQLAlchemy dialect has the appropriate infrastructure for that
    dialect set up.   Current dialects include cx_Oracle as well as
    optional support for SQL Server using pyodbc.

    When using setinputsizes, dialects also have a means of only using the
    method for certain datatypes using include/exclude lists.

    When SETINPUTSIZES is used, the :meth:`.Dialect.do_set_input_sizes` method
    is called for each statement executed which has bound parameters.

    """

    RENDER_CASTS = 3
    """Render casts or other directives in the SQL string.

    This method is used for all PostgreSQL dialects, including asyncpg,
    pg8000, psycopg, psycopg2.   Dialects which implement this can choose
    which kinds of datatypes are explicitly cast in SQL statements and which
    aren't.

    When RENDER_CASTS is used, the compiler will invoke the
    :meth:`.SQLCompiler.render_bind_cast` method for each
    :class:`.BindParameter` object whose dialect-level type sets the
    :attr:`.TypeEngine.render_bind_cast` attribute.

    """


class Dialect:
    """Define the behavior of a specific database and DB-API combination.

    Any aspect of metadata definition, SQL query generation,
    execution, result-set handling, or anything else which varies
    between databases is defined under the general category of the
    Dialect.  The Dialect acts as a factory for other
    database-specific object implementations including
    ExecutionContext, Compiled, DefaultGenerator, and TypeEngine.

    .. note:: Third party dialects should not subclass :class:`.Dialect`
       directly.  Instead, subclass :class:`.default.DefaultDialect` or
       descendant class.

    """

    name: str
    """identifying name for the dialect from a DBAPI-neutral point of view
      (i.e. 'sqlite')
    """

    driver: str
    """identifying name for the dialect's DBAPI"""

    positional: bool
    """True if the paramstyle for this Dialect is positional."""

    paramstyle: str
    """the paramstyle to be used (some DB-APIs support multiple
      paramstyles).
    """

    statement_compiler: Type["SQLCompiler"]
    """a :class:`.Compiled` class used to compile SQL statements"""

    ddl_compiler: Type["DDLCompiler"]
    """a :class:`.Compiled` class used to compile DDL statements"""

    type_compiler: _TypeToInstance["TypeCompiler"]
    """a :class:`.Compiled` class used to compile SQL type objects"""

    preparer: Type["IdentifierPreparer"]
    """a :class:`.IdentifierPreparer` class used to
    quote identifiers.
    """

    identifier_preparer: "IdentifierPreparer"
    """This element will refer to an instance of :class:`.IdentifierPreparer`
    once a :class:`.DefaultDialect` has been constructed.

    """

    server_version_info: Optional[Tuple[Any, ...]]
    """a tuple containing a version number for the DB backend in use.

    This value is only available for supporting dialects, and is
    typically populated during the initial connection to the database.
    """

    default_schema_name: Optional[str]
    """the name of the default schema.  This value is only available for
    supporting dialects, and is typically populated during the
    initial connection to the database.

    """

    execution_ctx_cls: Type["ExecutionContext"]
    """a :class:`.ExecutionContext` class used to handle statement execution"""

    execute_sequence_format: Union[Type[Tuple[Any, ...]], Type[List[Any]]]
    """either the 'tuple' or 'list' type, depending on what cursor.execute()
    accepts for the second argument (they vary)."""

    supports_alter: bool
    """``True`` if the database supports ``ALTER TABLE`` - used only for
    generating foreign key constraints in certain circumstances
    """

    max_identifier_length: int
    """The maximum length of identifier names."""

    supports_sane_rowcount: bool
    """Indicate whether the dialect properly implements rowcount for
      ``UPDATE`` and ``DELETE`` statements.
    """

    supports_sane_multi_rowcount: bool
    """Indicate whether the dialect properly implements rowcount for
      ``UPDATE`` and ``DELETE`` statements when executed via
      executemany.
    """

    supports_default_values: bool
    """Indicates if the construct ``INSERT INTO tablename DEFAULT
      VALUES`` is supported
    """

    preexecute_autoincrement_sequences: bool
    """True if 'implicit' primary key functions must be executed separately
      in order to get their value.   This is currently oriented towards
      PostgreSQL.
    """

    implicit_returning: bool
    """For dialects that support RETURNING, indicate RETURNING may be used
    to fetch newly generated primary key values and other defaults from
    an INSERT statement automatically.

    .. seealso::

        :paramref:`_schema.Table.implicit_returning`

    """

    colspecs: Dict[Type["TypeEngine[Any]"], Type["TypeEngine[Any]"]]
    """A dictionary of TypeEngine classes from sqlalchemy.types mapped
      to subclasses that are specific to the dialect class.  This
      dictionary is class-level only and is not accessed from the
      dialect instance itself.
    """

    supports_sequences: bool
    """Indicates if the dialect supports CREATE SEQUENCE or similar."""

    sequences_optional: bool
    """If True, indicates if the :paramref:`_schema.Sequence.optional`
      parameter on the :class:`_schema.Sequence` construct
      should signal to not generate a CREATE SEQUENCE. Applies only to
      dialects that support sequences. Currently used only to allow PostgreSQL
      SERIAL to be used on a column that specifies Sequence() for usage on
      other backends.
    """

    supports_native_enum: bool
    """Indicates if the dialect supports a native ENUM construct.
      This will prevent :class:`_types.Enum` from generating a CHECK
      constraint when that type is used in "native" mode.
    """

    supports_native_boolean: bool
    """Indicates if the dialect supports a native boolean construct.
      This will prevent :class:`_types.Boolean` from generating a CHECK
      constraint when that type is used.
    """

    dbapi_exception_translation_map: Dict[str, str]
    """A dictionary of names that will contain as values the names of
       pep-249 exceptions ("IntegrityError", "OperationalError", etc)
       keyed to alternate class names, to support the case where a
       DBAPI has exception classes that aren't named as they are
       referred to (e.g. IntegrityError = MyException).   In the vast
       majority of cases this dictionary is empty.
    """

    supports_comments: bool
    """Indicates the dialect supports comment DDL on tables and columns."""

    inline_comments: bool
    """Indicates the dialect supports comment DDL that's inline with the
    definition of a Table or Column.  If False, this implies that ALTER must
    be used to set table and column comments."""

    _has_events = False

    supports_statement_cache: bool = True
    """indicates if this dialect supports caching.

    All dialects that are compatible with statement caching should set this
    flag to True directly on each dialect class and subclass that supports
    it.  SQLAlchemy tests that this flag is locally present on each dialect
    subclass before it will use statement caching.  This is to provide
    safety for legacy or new dialects that are not yet fully tested to be
    compliant with SQL statement caching.

    .. versionadded:: 1.4.5

    .. seealso::

        :ref:`engine_thirdparty_caching`

    """

    bind_typing = BindTyping.NONE
    """define a means of passing typing information to the database and/or
    driver for bound parameters.

    See :class:`.BindTyping` for values.

    .. versionadded:: 2.0

    """

    def create_connect_args(
        self, url: "URL"
    ) -> Tuple[Tuple[str], Mapping[str, Any]]:
        """Build DB-API compatible connection arguments.

        Given a :class:`.URL` object, returns a tuple
        consisting of a ``(*args, **kwargs)`` suitable to send directly
        to the dbapi's connect function.   The arguments are sent to the
        :meth:`.Dialect.connect` method which then runs the DBAPI-level
        ``connect()`` function.

        The method typically makes use of the
        :meth:`.URL.translate_connect_args`
        method in order to generate a dictionary of options.

        The default implementation is::

            def create_connect_args(self, url):
                opts = url.translate_connect_args()
                opts.update(url.query)
                return [[], opts]

        :param url: a :class:`.URL` object

        :return: a tuple of ``(*args, **kwargs)`` which will be passed to the
         :meth:`.Dialect.connect` method.

        .. seealso::

            :meth:`.URL.translate_connect_args`

        """

        raise NotImplementedError()

    @classmethod
    def type_descriptor(cls, typeobj: "TypeEngine") -> "TypeEngine":
        """Transform a generic type to a dialect-specific type.

        Dialect classes will usually use the
        :func:`_types.adapt_type` function in the types module to
        accomplish this.

        The returned result is cached *per dialect class* so can
        contain no dialect-instance state.

        """

        raise NotImplementedError()

    def initialize(self, connection: "Connection") -> None:
        """Called during strategized creation of the dialect with a
        connection.

        Allows dialects to configure options based on server version info or
        other properties.

        The connection passed here is a SQLAlchemy Connection object,
        with full capabilities.

        The initialize() method of the base dialect should be called via
        super().

        .. note:: as of SQLAlchemy 1.4, this method is called **before**
           any :meth:`_engine.Dialect.on_connect` hooks are called.

        """

        pass

    def get_columns(
        self,
        connection: "Connection",
        table_name: str,
        schema: Optional[str] = None,
        **kw,
    ) -> List[ReflectedColumn]:
        """Return information about columns in ``table_name``.

        Given a :class:`_engine.Connection`, a string
        ``table_name``, and an optional string ``schema``, return column
        information as a list of dictionaries
        corresponding to the :class:`.ReflectedColumn` dictionary.

        """

        raise NotImplementedError()

    def get_pk_constraint(
        self,
        connection: "Connection",
        table_name: str,
        schema: Optional[str] = None,
        **kw: Any,
    ) -> ReflectedPrimaryKeyConstraint:
        """Return information about the primary key constraint on
        table_name`.

        Given a :class:`_engine.Connection`, a string
        ``table_name``, and an optional string ``schema``, return primary
        key information as a dictionary corresponding to the
        :class:`.ReflectedPrimaryKeyConstraint` dictionary.


        """
        raise NotImplementedError()

    def get_foreign_keys(
        self,
        connection: "Connection",
        table_name: str,
        schema: Optional[str] = None,
        **kw: Any,
    ) -> List[ReflectedForeignKeyConstraint]:
        """Return information about foreign_keys in ``table_name``.

        Given a :class:`_engine.Connection`, a string
        ``table_name``, and an optional string ``schema``, return foreign
        key information as a list of dicts corresponding to the
        :class:`.ReflectedForeignKeyConstraint` dictionary.

        """

        raise NotImplementedError()

    def get_table_names(
        self, connection: "Connection", schema: Optional[str] = None, **kw: Any
    ) -> List[str]:
        """Return a list of table names for ``schema``."""

        raise NotImplementedError()

    def get_temp_table_names(
        self, connection: "Connection", schema: Optional[str] = None, **kw: Any
    ) -> List[str]:
        """Return a list of temporary table names on the given connection,
        if supported by the underlying backend.

        """

        raise NotImplementedError()

    def get_view_names(
        self, connection: "Connection", schema: Optional[str] = None, **kw: Any
    ) -> List[str]:
        """Return a list of all view names available in the database.

        :param schema: schema name to query, if not the default schema.
        """

        raise NotImplementedError()

    def get_sequence_names(
        self, connection: "Connection", schema: Optional[str] = None, **kw: Any
    ) -> List[str]:
        """Return a list of all sequence names available in the database.

        :param schema: schema name to query, if not the default schema.

        .. versionadded:: 1.4
        """

        raise NotImplementedError()

    def get_temp_view_names(
        self, connection: "Connection", schema: Optional[str] = None, **kw: Any
    ) -> List[str]:
        """Return a list of temporary view names on the given connection,
        if supported by the underlying backend.

        """

        raise NotImplementedError()

    def get_view_definition(
        self,
        connection: "Connection",
        view_name: str,
        schema: Optional[str] = None,
        **kw: Any,
    ) -> str:
        """Return view definition.

        Given a :class:`_engine.Connection`, a string
        `view_name`, and an optional string ``schema``, return the view
        definition.
        """

        raise NotImplementedError()

    def get_indexes(
        self,
        connection: "Connection",
        table_name: str,
        schema: Optional[str] = None,
        **kw: Any,
    ) -> List[ReflectedIndex]:
        """Return information about indexes in ``table_name``.

        Given a :class:`_engine.Connection`, a string
        ``table_name`` and an optional string ``schema``, return index
        information as a list of dictionaries corresponding to the
        :class:`.ReflectedIndex` dictionary.

        """

        raise NotImplementedError()

    def get_unique_constraints(
        self,
        connection: "Connection",
        table_name: str,
        schema: Optional[str] = None,
        **kw: Any,
    ) -> List[ReflectedUniqueConstraint]:
        r"""Return information about unique constraints in ``table_name``.

        Given a string ``table_name`` and an optional string ``schema``, return
        unique constraint information as a list of dicts corresponding
        to the :class:`.ReflectedUniqueConstraint` dictionary.

        """

        raise NotImplementedError()

    def get_check_constraints(
        self,
        connection: "Connection",
        table_name: str,
        schema: Optional[str] = None,
        **kw: Any,
    ) -> List[ReflectedCheckConstraint]:
        r"""Return information about check constraints in ``table_name``.

        Given a string ``table_name`` and an optional string ``schema``, return
        check constraint information as a list of dicts corresponding
        to the :class:`.ReflectedCheckConstraint` dictionary.

        """

        raise NotImplementedError()

    def get_table_options(
        self,
        connection: "Connection",
        table_name: str,
        schema: Optional[str] = None,
        **kw: Any,
    ) -> Dict[str, Any]:
        r"""Return the "options" for the table identified by ``table_name``
        as a dictionary.

        """

    def get_table_comment(
        self,
        connection: "Connection",
        table_name: str,
        schema: Optional[str] = None,
        **kw: Any,
    ) -> ReflectedTableComment:
        r"""Return the "comment" for the table identified by ``table_name``.

        Given a string ``table_name`` and an optional string ``schema``, return
        table comment information as a dictionary corresponding to the
        :class:`.ReflectedTableComment` dictionary.


        :raise: ``NotImplementedError`` for dialects that don't support
         comments.

        .. versionadded:: 1.2

        """

        raise NotImplementedError()

    def normalize_name(self, name: str) -> str:
        """convert the given name to lowercase if it is detected as
        case insensitive.

        This method is only used if the dialect defines
        requires_name_normalize=True.

        """
        raise NotImplementedError()

    def denormalize_name(self, name: str) -> str:
        """convert the given name to a case insensitive identifier
        for the backend if it is an all-lowercase name.

        This method is only used if the dialect defines
        requires_name_normalize=True.

        """
        raise NotImplementedError()

    def has_table(
        self,
        connection: "Connection",
        table_name: str,
        schema: Optional[str] = None,
        **kw: Any,
    ) -> bool:
        """For internal dialect use, check the existence of a particular table
        or view in the database.

        Given a :class:`_engine.Connection` object, a string table_name and
        optional schema name, return True if the given table exists in the
        database, False otherwise.

        This method serves as the underlying implementation of the
        public facing :meth:`.Inspector.has_table` method, and is also used
        internally to implement the "checkfirst" behavior for methods like
        :meth:`_schema.Table.create` and :meth:`_schema.MetaData.create_all`.

        .. note:: This method is used internally by SQLAlchemy, and is
           published so that third-party dialects may provide an
           implementation. It is **not** the public API for checking for table
           presence. Please use the :meth:`.Inspector.has_table` method.
           Alternatively, for legacy cross-compatibility, the
           :meth:`_engine.Engine.has_table` method may be used.

        .. versionchanged:: 2.0

            The :meth:`_engine.Dialect.has_table` method should also check
            for the presence of views.  In previous versions this
            behavior was dialect specific. New dialect suite tests were added
            to ensure that dialects conform with this behavior consistently.

        """

        raise NotImplementedError()

    def has_index(
        self,
        connection: "Connection",
        table_name: str,
        index_name: str,
        schema: Optional[str] = None,
    ) -> bool:
        """Check the existence of a particular index name in the database.

        Given a :class:`_engine.Connection` object, a string
        ``table_name`` and string index name, return True if an index of the
        given name on the given table exists, false otherwise.

        The :class:`.DefaultDialect` implements this in terms of the
        :meth:`.Dialect.has_table` and :meth:`.Dialect.get_indexes` methods,
        however dialects can implement a more performant version.


        .. versionadded:: 1.4

        """

        raise NotImplementedError()

    def has_sequence(
        self,
        connection: "Connection",
        sequence_name: str,
        schema: Optional[str] = None,
        **kw: Any,
    ) -> bool:
        """Check the existence of a particular sequence in the database.

        Given a :class:`_engine.Connection` object and a string
        `sequence_name`, return True if the given sequence exists in
        the database, False otherwise.
        """

        raise NotImplementedError()

    def _get_server_version_info(self, connection: "Connection") -> Any:
        """Retrieve the server version info from the given connection.

        This is used by the default implementation to populate the
        "server_version_info" attribute and is called exactly
        once upon first connect.

        """

        raise NotImplementedError()

    def _get_default_schema_name(self, connection: "Connection") -> str:
        """Return the string name of the currently selected schema from
        the given connection.

        This is used by the default implementation to populate the
        "default_schema_name" attribute and is called exactly
        once upon first connect.

        """

        raise NotImplementedError()

    def do_begin(self, dbapi_connection: PoolProxiedConnection) -> None:
        """Provide an implementation of ``connection.begin()``, given a
        DB-API connection.

        The DBAPI has no dedicated "begin" method and it is expected
        that transactions are implicit.  This hook is provided for those
        DBAPIs that might need additional help in this area.

        :param dbapi_connection: a DBAPI connection, typically
         proxied within a :class:`.ConnectionFairy`.

        """

        raise NotImplementedError()

    def do_rollback(self, dbapi_connection: PoolProxiedConnection) -> None:
        """Provide an implementation of ``connection.rollback()``, given
        a DB-API connection.

        :param dbapi_connection: a DBAPI connection, typically
         proxied within a :class:`.ConnectionFairy`.

        """

        raise NotImplementedError()

    def do_commit(self, dbapi_connection: PoolProxiedConnection) -> None:
        """Provide an implementation of ``connection.commit()``, given a
        DB-API connection.

        :param dbapi_connection: a DBAPI connection, typically
         proxied within a :class:`.ConnectionFairy`.

        """

        raise NotImplementedError()

    def do_close(self, dbapi_connection: PoolProxiedConnection) -> None:
        """Provide an implementation of ``connection.close()``, given a DBAPI
        connection.

        This hook is called by the :class:`_pool.Pool`
        when a connection has been
        detached from the pool, or is being returned beyond the normal
        capacity of the pool.

        """

        raise NotImplementedError()

    def do_set_input_sizes(
        self,
        cursor: DBAPICursor,
        list_of_tuples: List[Tuple[str, Any, "TypeEngine"]],
        context: "ExecutionContext",
    ) -> Any:
        """invoke the cursor.setinputsizes() method with appropriate arguments

        This hook is called if the :attr:`.Dialect.bind_typing` attribute is
        set to the
        :attr:`.BindTyping.SETINPUTSIZES` value.
        Parameter data is passed in a list of tuples (paramname, dbtype,
        sqltype), where ``paramname`` is the key of the parameter in the
        statement, ``dbtype`` is the DBAPI datatype and ``sqltype`` is the
        SQLAlchemy type. The order of tuples is in the correct parameter order.

        .. versionadded:: 1.4

        .. versionchanged:: 2.0  - setinputsizes mode is now enabled by
           setting :attr:`.Dialect.bind_typing` to
           :attr:`.BindTyping.SETINPUTSIZES`.  Dialects which accept
           a ``use_setinputsizes`` parameter should set this value
           appropriately.


        """
        raise NotImplementedError()

    def create_xid(self) -> Any:
        """Create a two-phase transaction ID.

        This id will be passed to do_begin_twophase(),
        do_rollback_twophase(), do_commit_twophase().  Its format is
        unspecified.
        """

        raise NotImplementedError()

    def do_savepoint(self, connection: "Connection", name: str) -> None:
        """Create a savepoint with the given name.

        :param connection: a :class:`_engine.Connection`.
        :param name: savepoint name.

        """

        raise NotImplementedError()

    def do_rollback_to_savepoint(
        self, connection: "Connection", name: str
    ) -> None:
        """Rollback a connection to the named savepoint.

        :param connection: a :class:`_engine.Connection`.
        :param name: savepoint name.

        """

        raise NotImplementedError()

    def do_release_savepoint(
        self, connection: "Connection", name: str
    ) -> None:
        """Release the named savepoint on a connection.

        :param connection: a :class:`_engine.Connection`.
        :param name: savepoint name.
        """

        raise NotImplementedError()

    def do_begin_twophase(self, connection: "Connection", xid: Any) -> None:
        """Begin a two phase transaction on the given connection.

        :param connection: a :class:`_engine.Connection`.
        :param xid: xid

        """

        raise NotImplementedError()

    def do_prepare_twophase(self, connection: "Connection", xid: Any) -> None:
        """Prepare a two phase transaction on the given connection.

        :param connection: a :class:`_engine.Connection`.
        :param xid: xid

        """

        raise NotImplementedError()

    def do_rollback_twophase(
        self,
        connection: "Connection",
        xid: Any,
        is_prepared: bool = True,
        recover: bool = False,
    ) -> None:
        """Rollback a two phase transaction on the given connection.

        :param connection: a :class:`_engine.Connection`.
        :param xid: xid
        :param is_prepared: whether or not
         :meth:`.TwoPhaseTransaction.prepare` was called.
        :param recover: if the recover flag was passed.

        """

        raise NotImplementedError()

    def do_commit_twophase(
        self,
        connection: "Connection",
        xid: Any,
        is_prepared: bool = True,
        recover: bool = False,
    ) -> None:
        """Commit a two phase transaction on the given connection.


        :param connection: a :class:`_engine.Connection`.
        :param xid: xid
        :param is_prepared: whether or not
         :meth:`.TwoPhaseTransaction.prepare` was called.
        :param recover: if the recover flag was passed.

        """

        raise NotImplementedError()

    def do_recover_twophase(self, connection: "Connection") -> None:
        """Recover list of uncommitted prepared two phase transaction
        identifiers on the given connection.

        :param connection: a :class:`_engine.Connection`.

        """

        raise NotImplementedError()

    def do_executemany(
        self,
        cursor: DBAPICursor,
        statement: str,
        parameters: List[Union[Dict[str, Any], Tuple[Any]]],
        context: Optional["ExecutionContext"] = None,
    ) -> None:
        """Provide an implementation of ``cursor.executemany(statement,
        parameters)``."""

        raise NotImplementedError()

    def do_execute(
        self,
        cursor: DBAPICursor,
        statement: str,
        parameters: Union[Mapping[str, Any], Tuple[Any]],
        context: Optional["ExecutionContext"] = None,
    ):
        """Provide an implementation of ``cursor.execute(statement,
        parameters)``."""

        raise NotImplementedError()

    def do_execute_no_params(
        self,
        cursor: DBAPICursor,
        statement: str,
        context: Optional["ExecutionContext"] = None,
    ):
        """Provide an implementation of ``cursor.execute(statement)``.

        The parameter collection should not be sent.

        """

        raise NotImplementedError()

    def is_disconnect(
        self,
        e: Exception,
        connection: Optional[PoolProxiedConnection],
        cursor: DBAPICursor,
    ) -> bool:
        """Return True if the given DB-API error indicates an invalid
        connection"""

        raise NotImplementedError()

    def connect(self, *cargs: Any, **cparams: Any) -> Any:
        r"""Establish a connection using this dialect's DBAPI.

        The default implementation of this method is::

            def connect(self, *cargs, **cparams):
                return self.dbapi.connect(*cargs, **cparams)

        The ``*cargs, **cparams`` parameters are generated directly
        from this dialect's :meth:`.Dialect.create_connect_args` method.

        This method may be used for dialects that need to perform programmatic
        per-connection steps when a new connection is procured from the
        DBAPI.


        :param \*cargs: positional parameters returned from the
         :meth:`.Dialect.create_connect_args` method

        :param \*\*cparams: keyword parameters returned from the
         :meth:`.Dialect.create_connect_args` method.

        :return: a DBAPI connection, typically from the :pep:`249` module
         level ``.connect()`` function.

        .. seealso::

            :meth:`.Dialect.create_connect_args`

            :meth:`.Dialect.on_connect`

        """

    def on_connect_url(self, url: "URL") -> Optional[Callable[[Any], Any]]:
        """return a callable which sets up a newly created DBAPI connection.

        This method is a new hook that supersedes the
        :meth:`_engine.Dialect.on_connect` method when implemented by a
        dialect.   When not implemented by a dialect, it invokes the
        :meth:`_engine.Dialect.on_connect` method directly to maintain
        compatibility with existing dialects.   There is no deprecation
        for :meth:`_engine.Dialect.on_connect` expected.

        The callable should accept a single argument "conn" which is the
        DBAPI connection itself.  The inner callable has no
        return value.

        E.g.::

            class MyDialect(default.DefaultDialect):
                # ...

                def on_connect_url(self, url):
                    def do_on_connect(connection):
                        connection.execute("SET SPECIAL FLAGS etc")

                    return do_on_connect

        This is used to set dialect-wide per-connection options such as
        isolation modes, Unicode modes, etc.

        This method differs from :meth:`_engine.Dialect.on_connect` in that
        it is passed the :class:`_engine.URL` object that's relevant to the
        connect args.  Normally the only way to get this is from the
        :meth:`_engine.Dialect.on_connect` hook is to look on the
        :class:`_engine.Engine` itself, however this URL object may have been
        replaced by plugins.

        .. note::

            The default implementation of
            :meth:`_engine.Dialect.on_connect_url` is to invoke the
            :meth:`_engine.Dialect.on_connect` method. Therefore if a dialect
            implements this method, the :meth:`_engine.Dialect.on_connect`
            method **will not be called** unless the overriding dialect calls
            it directly from here.

        .. versionadded:: 1.4.3 added :meth:`_engine.Dialect.on_connect_url`
           which normally calls into :meth:`_engine.Dialect.on_connect`.

        :param url: a :class:`_engine.URL` object representing the
         :class:`_engine.URL` that was passed to the
         :meth:`_engine.Dialect.create_connect_args` method.

        :return: a callable that accepts a single DBAPI connection as an
         argument, or None.

        .. seealso::

            :meth:`_engine.Dialect.on_connect`

        """
        return self.on_connect()

    def on_connect(self) -> Optional[Callable[[Any], Any]]:
        """return a callable which sets up a newly created DBAPI connection.

        The callable should accept a single argument "conn" which is the
        DBAPI connection itself.  The inner callable has no
        return value.

        E.g.::

            class MyDialect(default.DefaultDialect):
                # ...

                def on_connect(self):
                    def do_on_connect(connection):
                        connection.execute("SET SPECIAL FLAGS etc")

                    return do_on_connect

        This is used to set dialect-wide per-connection options such as
        isolation modes, Unicode modes, etc.

        The "do_on_connect" callable is invoked by using the
        :meth:`_events.PoolEvents.connect` event
        hook, then unwrapping the DBAPI connection and passing it into the
        callable.

        .. versionchanged:: 1.4 the on_connect hook is no longer called twice
           for the first connection of a dialect.  The on_connect hook is still
           called before the :meth:`_engine.Dialect.initialize` method however.

        .. versionchanged:: 1.4.3 the on_connect hook is invoked from a new
           method on_connect_url that passes the URL that was used to create
           the connect args.   Dialects can implement on_connect_url instead
           of on_connect if they need the URL object that was used for the
           connection in order to get additional context.

        If None is returned, no event listener is generated.

        :return: a callable that accepts a single DBAPI connection as an
         argument, or None.

        .. seealso::

            :meth:`.Dialect.connect` - allows the DBAPI ``connect()`` sequence
            itself to be controlled.

            :meth:`.Dialect.on_connect_url` - supersedes
            :meth:`.Dialect.on_connect` to also receive the
            :class:`_engine.URL` object in context.

        """
        return None

    def reset_isolation_level(self, dbapi_connection: DBAPIConnection) -> None:
        """Given a DBAPI connection, revert its isolation to the default.

        Note that this is a dialect-level method which is used as part
        of the implementation of the :class:`_engine.Connection` and
        :class:`_engine.Engine`
        isolation level facilities; these APIs should be preferred for
        most typical use cases.

        .. seealso::

            :meth:`_engine.Connection.get_isolation_level`
            - view current level

            :attr:`_engine.Connection.default_isolation_level`
            - view default level

            :paramref:`.Connection.execution_options.isolation_level` -
            set per :class:`_engine.Connection` isolation level

            :paramref:`_sa.create_engine.isolation_level` -
            set per :class:`_engine.Engine` isolation level

        """

        raise NotImplementedError()

    def set_isolation_level(
        self, dbapi_connection: DBAPIConnection, level: str
    ) -> None:
        """Given a DBAPI connection, set its isolation level.

        Note that this is a dialect-level method which is used as part
        of the implementation of the :class:`_engine.Connection` and
        :class:`_engine.Engine`
        isolation level facilities; these APIs should be preferred for
        most typical use cases.

        If the dialect also implements the
        :meth:`.Dialect.get_isolation_level_values` method, then the given
        level is guaranteed to be one of the string names within that sequence,
        and the method will not need to anticipate a lookup failure.

        .. seealso::

            :meth:`_engine.Connection.get_isolation_level`
            - view current level

            :attr:`_engine.Connection.default_isolation_level`
            - view default level

            :paramref:`.Connection.execution_options.isolation_level` -
            set per :class:`_engine.Connection` isolation level

            :paramref:`_sa.create_engine.isolation_level` -
            set per :class:`_engine.Engine` isolation level

        """

        raise NotImplementedError()

    def get_isolation_level(self, dbapi_connection: DBAPIConnection) -> str:
        """Given a DBAPI connection, return its isolation level.

        When working with a :class:`_engine.Connection` object,
        the corresponding
        DBAPI connection may be procured using the
        :attr:`_engine.Connection.connection` accessor.

        Note that this is a dialect-level method which is used as part
        of the implementation of the :class:`_engine.Connection` and
        :class:`_engine.Engine` isolation level facilities;
        these APIs should be preferred for most typical use cases.


        .. seealso::

            :meth:`_engine.Connection.get_isolation_level`
            - view current level

            :attr:`_engine.Connection.default_isolation_level`
            - view default level

            :paramref:`.Connection.execution_options.isolation_level` -
            set per :class:`_engine.Connection` isolation level

            :paramref:`_sa.create_engine.isolation_level` -
            set per :class:`_engine.Engine` isolation level


        """

        raise NotImplementedError()

    def get_default_isolation_level(self, dbapi_conn: Any) -> str:
        """Given a DBAPI connection, return its isolation level, or
        a default isolation level if one cannot be retrieved.

        This method may only raise NotImplementedError and
        **must not raise any other exception**, as it is used implicitly upon
        first connect.

        The method **must return a value** for a dialect that supports
        isolation level settings, as this level is what will be reverted
        towards when a per-connection isolation level change is made.

        The method defaults to using the :meth:`.Dialect.get_isolation_level`
        method unless overridden by a dialect.

        .. versionadded:: 1.3.22

        """
        raise NotImplementedError()

    def get_isolation_level_values(self, dbapi_conn: Any) -> List[str]:
        """return a sequence of string isolation level names that are accepted
        by this dialect.

        The available names should use the following conventions:

        * use UPPERCASE names.   isolation level methods will accept lowercase
          names but these are normalized into UPPERCASE before being passed
          along to the dialect.
        * separate words should be separated by spaces, not underscores, e.g.
          ``REPEATABLE READ``.  isolation level names will have underscores
          converted to spaces before being passed along to the dialect.
        * The names for the four standard isolation names to the extent that
          they are supported by the backend should be ``READ UNCOMMITTED``
          ``READ COMMITTED``, ``REPEATABLE READ``, ``SERIALIZABLE``
        * if the dialect supports an autocommit option it should be provided
          using the isolation level name ``AUTOCOMMIT``.
        * Other isolation modes may also be present, provided that they
          are named in UPPERCASE and use spaces not underscores.

        This function is used so that the default dialect can check that
        a given isolation level parameter is valid, else raises an
        :class:`_exc.ArgumentError`.

        A DBAPI connection is passed to the method, in the unlikely event that
        the dialect needs to interrogate the connection itself to determine
        this list, however it is expected that most backends will return
        a hardcoded list of values.  If the dialect supports "AUTOCOMMIT",
        that value should also be present in the sequence returned.

        The method raises ``NotImplementedError`` by default.  If a dialect
        does not implement this method, then the default dialect will not
        perform any checking on a given isolation level value before passing
        it onto the :meth:`.Dialect.set_isolation_level` method.  This is
        to allow backwards-compatibility with third party dialects that may
        not yet be implementing this method.

        .. versionadded:: 2.0

        """
        raise NotImplementedError()

    @classmethod
    def get_dialect_cls(cls, url: "URL") -> Type:
        """Given a URL, return the :class:`.Dialect` that will be used.

        This is a hook that allows an external plugin to provide functionality
        around an existing dialect, by allowing the plugin to be loaded
        from the url based on an entrypoint, and then the plugin returns
        the actual dialect to be used.

        By default this just returns the cls.

        .. versionadded:: 1.0.3

        """
        return cls

    @classmethod
    def get_async_dialect_cls(cls, url: "URL") -> None:
        """Given a URL, return the :class:`.Dialect` that will be used by
        an async engine.

        By default this is an alias of :meth:`.Dialect.get_dialect_cls` and
        just returns the cls. It may be used if a dialect provides
        both a sync and async version under the same name, like the
        ``psycopg`` driver.

        .. versionadded:: 2

        .. seealso::

            :meth:`.Dialect.get_dialect_cls`

        """
        return cls.get_dialect_cls(url)

    @classmethod
    def load_provisioning(cls) -> None:
        """set up the provision.py module for this dialect.

        For dialects that include a provision.py module that sets up
        provisioning followers, this method should initiate that process.

        A typical implementation would be::

            @classmethod
            def load_provisioning(cls):
                __import__("mydialect.provision")

        The default method assumes a module named ``provision.py`` inside
        the owning package of the current dialect, based on the ``__module__``
        attribute::

            @classmethod
            def load_provisioning(cls):
                package = ".".join(cls.__module__.split(".")[0:-1])
                try:
                    __import__(package + ".provision")
                except ImportError:
                    pass

        .. versionadded:: 1.3.14

        """

    @classmethod
    def engine_created(cls, engine: "Engine") -> None:
        """A convenience hook called before returning the final
        :class:`_engine.Engine`.

        If the dialect returned a different class from the
        :meth:`.get_dialect_cls`
        method, then the hook is called on both classes, first on
        the dialect class returned by the :meth:`.get_dialect_cls` method and
        then on the class on which the method was called.

        The hook should be used by dialects and/or wrappers to apply special
        events to the engine or its components.   In particular, it allows
        a dialect-wrapping class to apply dialect-level events.

        .. versionadded:: 1.0.3

        """

    def get_driver_connection(self, connection: PoolProxiedConnection) -> Any:
        """Returns the connection object as returned by the external driver
        package.

        For normal dialects that use a DBAPI compliant driver this call
        will just return the ``connection`` passed as argument.
        For dialects that instead adapt a non DBAPI compliant driver, like
        when adapting an asyncio driver, this call will return the
        connection-like object as returned by the driver.

        .. versionadded:: 1.4.24

        """
        raise NotImplementedError()


class CreateEnginePlugin:
    """A set of hooks intended to augment the construction of an
    :class:`_engine.Engine` object based on entrypoint names in a URL.

    The purpose of :class:`_engine.CreateEnginePlugin` is to allow third-party
    systems to apply engine, pool and dialect level event listeners without
    the need for the target application to be modified; instead, the plugin
    names can be added to the database URL.  Target applications for
    :class:`_engine.CreateEnginePlugin` include:

    * connection and SQL performance tools, e.g. which use events to track
      number of checkouts and/or time spent with statements

    * connectivity plugins such as proxies

    A rudimentary :class:`_engine.CreateEnginePlugin` that attaches a logger
    to an :class:`_engine.Engine` object might look like::


        import logging

        from sqlalchemy.engine import CreateEnginePlugin
        from sqlalchemy import event

        class LogCursorEventsPlugin(CreateEnginePlugin):
            def __init__(self, url, kwargs):
                # consume the parameter "log_cursor_logging_name" from the
                # URL query
                logging_name = url.query.get("log_cursor_logging_name", "log_cursor")

                self.log = logging.getLogger(logging_name)

            def update_url(self, url):
                "update the URL to one that no longer includes our parameters"
                return url.difference_update_query(["log_cursor_logging_name"])

            def engine_created(self, engine):
                "attach an event listener after the new Engine is constructed"
                event.listen(engine, "before_cursor_execute", self._log_event)


            def _log_event(
                self,
                conn,
                cursor,
                statement,
                parameters,
                context,
                executemany):

                self.log.info("Plugin logged cursor event: %s", statement)



    Plugins are registered using entry points in a similar way as that
    of dialects::

        entry_points={
            'sqlalchemy.plugins': [
                'log_cursor_plugin = myapp.plugins:LogCursorEventsPlugin'
            ]

    A plugin that uses the above names would be invoked from a database
    URL as in::

        from sqlalchemy import create_engine

        engine = create_engine(
            "mysql+pymysql://scott:tiger@localhost/test?"
            "plugin=log_cursor_plugin&log_cursor_logging_name=mylogger"
        )

    The ``plugin`` URL parameter supports multiple instances, so that a URL
    may specify multiple plugins; they are loaded in the order stated
    in the URL::

        engine = create_engine(
          "mysql+pymysql://scott:tiger@localhost/test?"
          "plugin=plugin_one&plugin=plugin_twp&plugin=plugin_three")

    The plugin names may also be passed directly to :func:`_sa.create_engine`
    using the :paramref:`_sa.create_engine.plugins` argument::

        engine = create_engine(
          "mysql+pymysql://scott:tiger@localhost/test",
          plugins=["myplugin"])

    .. versionadded:: 1.2.3  plugin names can also be specified
       to :func:`_sa.create_engine` as a list

    A plugin may consume plugin-specific arguments from the
    :class:`_engine.URL` object as well as the ``kwargs`` dictionary, which is
    the dictionary of arguments passed to the :func:`_sa.create_engine`
    call.  "Consuming" these arguments includes that they must be removed
    when the plugin initializes, so that the arguments are not passed along
    to the :class:`_engine.Dialect` constructor, where they will raise an
    :class:`_exc.ArgumentError` because they are not known by the dialect.

    As of version 1.4 of SQLAlchemy, arguments should continue to be consumed
    from the ``kwargs`` dictionary directly, by removing the values with a
    method such as ``dict.pop``. Arguments from the :class:`_engine.URL` object
    should be consumed by implementing the
    :meth:`_engine.CreateEnginePlugin.update_url` method, returning a new copy
    of the :class:`_engine.URL` with plugin-specific parameters removed::

        class MyPlugin(CreateEnginePlugin):
            def __init__(self, url, kwargs):
                self.my_argument_one = url.query['my_argument_one']
                self.my_argument_two = url.query['my_argument_two']
                self.my_argument_three = kwargs.pop('my_argument_three', None)

            def update_url(self, url):
                return url.difference_update_query(
                    ["my_argument_one", "my_argument_two"]
                )

    Arguments like those illustrated above would be consumed from a
    :func:`_sa.create_engine` call such as::

        from sqlalchemy import create_engine

        engine = create_engine(
          "mysql+pymysql://scott:tiger@localhost/test?"
          "plugin=myplugin&my_argument_one=foo&my_argument_two=bar",
          my_argument_three='bat'
        )

    .. versionchanged:: 1.4

        The :class:`_engine.URL` object is now immutable; a
        :class:`_engine.CreateEnginePlugin` that needs to alter the
        :class:`_engine.URL` should implement the newly added
        :meth:`_engine.CreateEnginePlugin.update_url` method, which
        is invoked after the plugin is constructed.

        For migration, construct the plugin in the following way, checking
        for the existence of the :meth:`_engine.CreateEnginePlugin.update_url`
        method to detect which version is running::

            class MyPlugin(CreateEnginePlugin):
                def __init__(self, url, kwargs):
                    if hasattr(CreateEnginePlugin, "update_url"):
                        # detect the 1.4 API
                        self.my_argument_one = url.query['my_argument_one']
                        self.my_argument_two = url.query['my_argument_two']
                    else:
                        # detect the 1.3 and earlier API - mutate the
                        # URL directly
                        self.my_argument_one = url.query.pop('my_argument_one')
                        self.my_argument_two = url.query.pop('my_argument_two')

                    self.my_argument_three = kwargs.pop('my_argument_three', None)

                def update_url(self, url):
                    # this method is only called in the 1.4 version
                    return url.difference_update_query(
                        ["my_argument_one", "my_argument_two"]
                    )

        .. seealso::

            :ref:`change_5526` - overview of the :class:`_engine.URL` change which
            also includes notes regarding :class:`_engine.CreateEnginePlugin`.


    When the engine creation process completes and produces the
    :class:`_engine.Engine` object, it is again passed to the plugin via the
    :meth:`_engine.CreateEnginePlugin.engine_created` hook.  In this hook, additional
    changes can be made to the engine, most typically involving setup of
    events (e.g. those defined in :ref:`core_event_toplevel`).

    .. versionadded:: 1.1

    """  # noqa: E501

    def __init__(self, url, kwargs):
        """Construct a new :class:`.CreateEnginePlugin`.

        The plugin object is instantiated individually for each call
        to :func:`_sa.create_engine`.  A single :class:`_engine.
        Engine` will be
        passed to the :meth:`.CreateEnginePlugin.engine_created` method
        corresponding to this URL.

        :param url: the :class:`_engine.URL` object.  The plugin may inspect
         the :class:`_engine.URL` for arguments.  Arguments used by the
         plugin should be removed, by returning an updated :class:`_engine.URL`
         from the :meth:`_engine.CreateEnginePlugin.update_url` method.

         .. versionchanged::  1.4

            The :class:`_engine.URL` object is now immutable, so a
            :class:`_engine.CreateEnginePlugin` that needs to alter the
            :class:`_engine.URL` object should implement the
            :meth:`_engine.CreateEnginePlugin.update_url` method.

        :param kwargs: The keyword arguments passed to
         :func:`_sa.create_engine`.

        """
        self.url = url

    def update_url(self, url):
        """Update the :class:`_engine.URL`.

        A new :class:`_engine.URL` should be returned.   This method is
        typically used to consume configuration arguments from the
        :class:`_engine.URL` which must be removed, as they will not be
        recognized by the dialect.  The
        :meth:`_engine.URL.difference_update_query` method is available
        to remove these arguments.   See the docstring at
        :class:`_engine.CreateEnginePlugin` for an example.


        .. versionadded:: 1.4

        """

    def handle_dialect_kwargs(self, dialect_cls, dialect_args):
        """parse and modify dialect kwargs"""

    def handle_pool_kwargs(self, pool_cls, pool_args):
        """parse and modify pool kwargs"""

    def engine_created(self, engine):
        """Receive the :class:`_engine.Engine`
        object when it is fully constructed.

        The plugin may make additional changes to the engine, such as
        registering engine or connection pool events.

        """


class ExecutionContext:
    """A messenger object for a Dialect that corresponds to a single
    execution.

    ExecutionContext should have these data members:

    connection
      Connection object which can be freely used by default value
      generators to execute SQL.  This Connection should reference the
      same underlying connection/transactional resources of
      root_connection.

    root_connection
      Connection object which is the source of this ExecutionContext.

    dialect
      dialect which created this ExecutionContext.

    cursor
      DB-API cursor procured from the connection,

    compiled
      if passed to constructor, sqlalchemy.engine.base.Compiled object
      being executed,

    statement
      string version of the statement to be executed.  Is either
      passed to the constructor, or must be created from the
      sql.Compiled object by the time pre_exec() has completed.

    parameters
      bind parameters passed to the execute() method.  For compiled
      statements, this is a dictionary or list of dictionaries.  For
      textual statements, it should be in a format suitable for the
      dialect's paramstyle (i.e. dict or list of dicts for non
      positional, list or list of lists/tuples for positional).

    isinsert
      True if the statement is an INSERT.

    isupdate
      True if the statement is an UPDATE.

    prefetch_cols
      a list of Column objects for which a client-side default
      was fired off.  Applies to inserts and updates.

    postfetch_cols
      a list of Column objects for which a server-side default or
      inline SQL expression value was fired off.  Applies to inserts
      and updates.
    """

    def create_cursor(self):
        """Return a new cursor generated from this ExecutionContext's
        connection.

        Some dialects may wish to change the behavior of
        connection.cursor(), such as postgresql which may return a PG
        "server side" cursor.
        """

        raise NotImplementedError()

    def pre_exec(self):
        """Called before an execution of a compiled statement.

        If a compiled statement was passed to this ExecutionContext,
        the `statement` and `parameters` datamembers must be
        initialized after this statement is complete.
        """

        raise NotImplementedError()

    def get_out_parameter_values(self, out_param_names):
        """Return a sequence of OUT parameter values from a cursor.

        For dialects that support OUT parameters, this method will be called
        when there is a :class:`.SQLCompiler` object which has the
        :attr:`.SQLCompiler.has_out_parameters` flag set.  This flag in turn
        will be set to True if the statement itself has :class:`.BindParameter`
        objects that have the ``.isoutparam`` flag set which are consumed by
        the :meth:`.SQLCompiler.visit_bindparam` method.  If the dialect
        compiler produces :class:`.BindParameter` objects with ``.isoutparam``
        set which are not handled by :meth:`.SQLCompiler.visit_bindparam`, it
        should set this flag explicitly.

        The list of names that were rendered for each bound parameter
        is passed to the method.  The method should then return a sequence of
        values corresponding to the list of parameter objects. Unlike in
        previous SQLAlchemy versions, the values can be the **raw values** from
        the DBAPI; the execution context will apply the appropriate type
        handler based on what's present in self.compiled.binds and update the
        values.  The processed dictionary will then be made available via the
        ``.out_parameters`` collection on the result object.  Note that
        SQLAlchemy 1.4 has multiple kinds of result object as part of the 2.0
        transition.

        .. versionadded:: 1.4 - added
           :meth:`.ExecutionContext.get_out_parameter_values`, which is invoked
           automatically by the :class:`.DefaultExecutionContext` when there
           are :class:`.BindParameter` objects with the ``.isoutparam`` flag
           set.  This replaces the practice of setting out parameters within
           the now-removed ``get_result_proxy()`` method.

        .. seealso::

            :meth:`.ExecutionContext.get_result_cursor_strategy`

        """
        raise NotImplementedError()

    def post_exec(self):
        """Called after the execution of a compiled statement.

        If a compiled statement was passed to this ExecutionContext,
        the `last_insert_ids`, `last_inserted_params`, etc.
        datamembers should be available after this method completes.
        """

        raise NotImplementedError()

    def get_result_cursor_strategy(self, result):
        """Return a result cursor strategy for a given result object.

        This method is implemented by the :class:`.DefaultDialect` and is
        only needed by implementing dialects in the case where some special
        steps regarding the cursor must be taken, such as manufacturing
        fake results from some other element of the cursor, or pre-buffering
        the cursor's results.

        A simplified version of the default implementation is::

            from sqlalchemy.engine.result import DefaultCursorFetchStrategy

            class MyExecutionContext(DefaultExecutionContext):
                def get_result_cursor_strategy(self, result):
                    return DefaultCursorFetchStrategy.create(result)

        Above, the :class:`.DefaultCursorFetchStrategy` will be applied
        to the result object.   For results that are pre-buffered from a
        cursor that might be closed, an implementation might be::


            from sqlalchemy.engine.result import (
                FullyBufferedCursorFetchStrategy
            )

            class MyExecutionContext(DefaultExecutionContext):
                _pre_buffered_result = None

                def pre_exec(self):
                    if self.special_condition_prebuffer_cursor():
                        self._pre_buffered_result = (
                            self.cursor.description,
                            self.cursor.fetchall()
                        )

                def get_result_cursor_strategy(self, result):
                    if self._pre_buffered_result:
                        description, cursor_buffer = self._pre_buffered_result
                        return (
                            FullyBufferedCursorFetchStrategy.
                                create_from_buffer(
                                    result, description, cursor_buffer
                            )
                        )
                    else:
                        return DefaultCursorFetchStrategy.create(result)

        This method replaces the previous not-quite-documented
        ``get_result_proxy()`` method.

        .. versionadded:: 1.4  - result objects now interpret cursor results
           based on a pluggable "strategy" object, which is delivered
           by the :class:`.ExecutionContext` via the
           :meth:`.ExecutionContext.get_result_cursor_strategy` method.

        .. seealso::

            :meth:`.ExecutionContext.get_out_parameter_values`

        """
        raise NotImplementedError()

    def handle_dbapi_exception(self, e):
        """Receive a DBAPI exception which occurred upon execute, result
        fetch, etc."""

        raise NotImplementedError()

    def lastrow_has_defaults(self):
        """Return True if the last INSERT or UPDATE row contained
        inlined or database-side defaults.
        """

        raise NotImplementedError()

    def get_rowcount(self):
        """Return the DBAPI ``cursor.rowcount`` value, or in some
        cases an interpreted value.

        See :attr:`_engine.CursorResult.rowcount` for details on this.

        """

        raise NotImplementedError()


class ConnectionEventsTarget:
    """An object which can accept events from :class:`.ConnectionEvents`.

    Includes :class:`_engine.Connection` and :class:`_engine.Engine`.

    .. versionadded:: 2.0

    """


class ExceptionContext:
    """Encapsulate information about an error condition in progress.

    This object exists solely to be passed to the
    :meth:`_events.ConnectionEvents.handle_error` event,
    supporting an interface that
    can be extended without backwards-incompatibility.

    .. versionadded:: 0.9.7

    """

    connection = None
    """The :class:`_engine.Connection` in use during the exception.

    This member is present, except in the case of a failure when
    first connecting.

    .. seealso::

        :attr:`.ExceptionContext.engine`


    """

    engine = None
    """The :class:`_engine.Engine` in use during the exception.

    This member should always be present, even in the case of a failure
    when first connecting.

    .. versionadded:: 1.0.0

    """

    cursor = None
    """The DBAPI cursor object.

    May be None.

    """

    statement = None
    """String SQL statement that was emitted directly to the DBAPI.

    May be None.

    """

    parameters = None
    """Parameter collection that was emitted directly to the DBAPI.

    May be None.

    """

    original_exception = None
    """The exception object which was caught.

    This member is always present.

    """

    sqlalchemy_exception = None
    """The :class:`sqlalchemy.exc.StatementError` which wraps the original,
    and will be raised if exception handling is not circumvented by the event.

    May be None, as not all exception types are wrapped by SQLAlchemy.
    For DBAPI-level exceptions that subclass the dbapi's Error class, this
    field will always be present.

    """

    chained_exception = None
    """The exception that was returned by the previous handler in the
    exception chain, if any.

    If present, this exception will be the one ultimately raised by
    SQLAlchemy unless a subsequent handler replaces it.

    May be None.

    """

    execution_context = None
    """The :class:`.ExecutionContext` corresponding to the execution
    operation in progress.

    This is present for statement execution operations, but not for
    operations such as transaction begin/end.  It also is not present when
    the exception was raised before the :class:`.ExecutionContext`
    could be constructed.

    Note that the :attr:`.ExceptionContext.statement` and
    :attr:`.ExceptionContext.parameters` members may represent a
    different value than that of the :class:`.ExecutionContext`,
    potentially in the case where a
    :meth:`_events.ConnectionEvents.before_cursor_execute` event or similar
    modified the statement/parameters to be sent.

    May be None.

    """

    is_disconnect = None
    """Represent whether the exception as occurred represents a "disconnect"
    condition.

    This flag will always be True or False within the scope of the
    :meth:`_events.ConnectionEvents.handle_error` handler.

    SQLAlchemy will defer to this flag in order to determine whether or not
    the connection should be invalidated subsequently.    That is, by
    assigning to this flag, a "disconnect" event which then results in
    a connection and pool invalidation can be invoked or prevented by
    changing this flag.


    .. note:: The pool "pre_ping" handler enabled using the
        :paramref:`_sa.create_engine.pool_pre_ping` parameter does **not**
        consult this event before deciding if the "ping" returned false,
        as opposed to receiving an unhandled error.   For this use case, the
        :ref:`legacy recipe based on engine_connect() may be used
        <pool_disconnects_pessimistic_custom>`.  A future API allow more
        comprehensive customization of the "disconnect" detection mechanism
        across all functions.

    """

    invalidate_pool_on_disconnect = True
    """Represent whether all connections in the pool should be invalidated
    when a "disconnect" condition is in effect.

    Setting this flag to False within the scope of the
    :meth:`_events.ConnectionEvents.handle_error`
    event will have the effect such
    that the full collection of connections in the pool will not be
    invalidated during a disconnect; only the current connection that is the
    subject of the error will actually be invalidated.

    The purpose of this flag is for custom disconnect-handling schemes where
    the invalidation of other connections in the pool is to be performed
    based on other conditions, or even on a per-connection basis.

    .. versionadded:: 1.0.3

    """


class AdaptedConnection:
    """Interface of an adapted connection object to support the DBAPI protocol.

    Used by asyncio dialects to provide a sync-style pep-249 facade on top
    of the asyncio connection/cursor API provided by the driver.

    .. versionadded:: 1.4.24

    """

    __slots__ = ("_connection",)

    @property
    def driver_connection(self):
        """The connection object as returned by the driver after a connect."""
        return self._connection

    def run_async(self, fn):
        """Run the awaitable returned by the given function, which is passed
        the raw asyncio driver connection.

        This is used to invoke awaitable-only methods on the driver connection
        within the context of a "synchronous" method, like a connection
        pool event handler.

        E.g.::

            engine = create_async_engine(...)

            @event.listens_for(engine.sync_engine, "connect")
            def register_custom_types(dbapi_connection, ...):
                dbapi_connection.run_async(
                    lambda connection: connection.set_type_codec(
                        'MyCustomType', encoder, decoder, ...
                    )
                )

        .. versionadded:: 1.4.30

        .. seealso::

            :ref:`asyncio_events_run_async`

        """
        return await_only(fn(self._connection))

    def __repr__(self):
        return "<AdaptedConnection %s>" % self._connection
