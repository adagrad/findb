
CREATE TABLE IF NOT EXISTS yf_price
(
    symbol       TEXT,
    date         DATETIME,
    Open         DOUBLE,
    High         DOUBLE,
    Low          DOUBLE,
    Close        DOUBLE,
    adj_close    DOUBLE,
    Volume       BIGINT,
    Dividends    DOUBLE,
    stock_splits DOUBLE,
    PRIMARY KEY (symbol, date)
);

