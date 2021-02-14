DROP TABLE IF EXISTS yahoo_symbol;

CREATE TABLE IF NOT EXISTS yf_symbol
(
    symbol        varchar(255) not null primary key,
    name          varchar(1024),
    exchange      varchar(255),
    exchange_name varchar(1024),
    type          varchar(1024),
    type_name     varchar(1024)
);

CREATE INDEX IF NOT EXISTS yf_symbol_ex_idx ON yf_symbol(exchange);
CREATE INDEX IF NOT EXISTS yf_symbol_type_idx ON yf_symbol(type);


-- ,IB Symbol,Product Description (click link for more details),Symbol,Currency,exchange,product,last_update
CREATE TABLE IF NOT EXISTS ib_symbol
(
    ib_symbol     varchar(255) not null,
    name          varchar(1024),
    symbol        varchar(255),
    currency      varchar(255),
    exchange      varchar(1024),
    product       varchar(1024),
    last_update   timestamp,
    primary key (ib_symbol, symbol, currency, exchange, product)
);

CREATE INDEX IF NOT EXISTS ib_symbol_ibs_idx ON ib_symbol(ib_symbol);
CREATE INDEX IF NOT EXISTS ib_symbol_s_idx ON ib_symbol(symbol);
CREATE INDEX IF NOT EXISTS ib_symbol_ex_idx ON ib_symbol(exchange);
CREATE INDEX IF NOT EXISTS ib_symbol_p_idx ON ib_symbol(product);

