Store SQL scripts and queries in this directory. SQLFluff checks every `.sql` file on push and when its workflow is run manually.

[`incremental_load_scd2.sql`](./incremental_load_scd2.sql) is a SQL Server/Azure SQL example. It uses `MERGE` to expire changed current records, then inserts a new current version for changed or new keys. Adapt its staging/target table names and columns, and set `@LoadBatchId` for each run. The stage batch should contain the delta to apply; absent keys are not treated as deletes. The sample keeps one staged row per key by choosing the latest `SourceUpdatedAt` and then the greatest `StageRowId`.

The SQL validation workflow defaults to the `tsql` dialect for this example. Set the `SQL_DIALECT` repository variable to another SQLFluff-supported dialect if your project uses a different engine.
