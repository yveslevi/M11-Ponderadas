CREATE TABLE IF NOT EXISTS working_data (
    data_ingestao DateTime,
    dado_linha String,
    tag String
) ENGINE = MergeTree()
ORDER BY data_ingestao;

-- CREATE VIEW IF NOT EXISTS working_data_view AS
-- SELECT
--     data_ingestao,
--     JSONExtractInt(dado_linha, 'date') AS date_unix,
--     JSONExtractInt(dado_linha, 'dados') AS dados,
--     toDateTime(JSONExtractInt(dado_linha, 'data_ingestao') / 1000) AS data_ingestao_datetime
-- FROM working_data;