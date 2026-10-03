-- SQL Server / Azure SQL example.
-- Adapt the staging table, target table, batch filter, and business columns to your project.
-- The staged batch is treated as a delta: missing source keys are not interpreted as deletes.
-- Expected source columns: LoadBatchId, StageRowId, CustomerId, CustomerName, Email, City, SourceUpdatedAt.
-- Expected target columns: CustomerSK (identity), CustomerId, CustomerName, Email, City,
--                          EffectiveFrom, EffectiveTo, IsCurrent.

DECLARE @LoadBatchId bigint = 1; -- Set this to the batch to process.
DECLARE @LoadTimestamp datetime2(7) = SYSUTCDATETIME();

;WITH RankedSource AS
(
    SELECT
        CustomerId,
        CustomerName,
        Email,
        City,
        ROW_NUMBER() OVER
        (
            PARTITION BY CustomerId
            ORDER BY SourceUpdatedAt DESC, StageRowId DESC
        ) AS RowNumber
    FROM dbo.CustomerStage
    WHERE LoadBatchId = @LoadBatchId
)
SELECT
    CustomerId,
    CustomerName,
    Email,
    City
INTO #Source
FROM RankedSource
WHERE RowNumber = 1;

BEGIN TRY
    BEGIN TRANSACTION;

    -- Expire the current version when tracked attributes differ.
    MERGE dbo.DimCustomer WITH (HOLDLOCK) AS target
    USING #Source AS source
        ON target.CustomerId = source.CustomerId
        AND target.IsCurrent = 1
    WHEN MATCHED AND EXISTS
    (
        SELECT source.CustomerName, source.Email, source.City
        EXCEPT
        SELECT target.CustomerName, target.Email, target.City
    )
        THEN UPDATE SET
            target.EffectiveTo = @LoadTimestamp,
            target.IsCurrent = 0
    ;

    -- Insert brand-new keys and the new versions of changed keys.
    INSERT INTO dbo.DimCustomer
    (
        CustomerId,
        CustomerName,
        Email,
        City,
        EffectiveFrom,
        EffectiveTo,
        IsCurrent
    )
    SELECT
        source.CustomerId,
        source.CustomerName,
        source.Email,
        source.City,
        @LoadTimestamp,
        CONVERT(datetime2(7), '9999-12-31 23:59:59.9999999'),
        1
    FROM #Source AS source
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.DimCustomer AS target WITH (UPDLOCK, HOLDLOCK)
        WHERE target.CustomerId = source.CustomerId
          AND target.IsCurrent = 1
    );

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;

DROP TABLE #Source;
