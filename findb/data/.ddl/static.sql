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


CREATE TABLE IF NOT EXISTS yf_info
(
    symbol                       varchar(255) not null primary key,
    exchange                     varchar(255),
    short_name                   varchar(1024),
    exchange_timezone            varchar(1024),
    exchange_timezone_short      varchar(5),
    is_esg_populated             boolean,
    gmt_offset_ms                bigint,
    message_board                varchar(255),
    market                       varchar(255),
    company_officers             varchar(1024),
    twitter                      varchar(1024),
    name                         varchar(1024),
    start_date                   datetime,
    description                  varchar(1024),
    max_age                      bigint,
    zip                          varchar(255),
    sector                       varchar(255),
    fullTimeEmployees            double,
    long_summary                 varchar(1024),
    city                         varchar(255),
    phone                        varchar(255),
    state                        varchar(255),
    country                      varchar(255),
    website                      text,
    address1                     varchar(1024),
    address2                     varchar(1024),
    address3                     varchar(1024),
    industry_init_investment     double,
    family                       varchar(1024),
    categoryName                 varchar(1024),
    init_aip_investment          double,
    subseq_ira_investment        double,
    brokerages                   varchar(1024),
    management_info              text,
    subseq_investment            double,
    legal_type                   varchar(1024),
    style_box_url                text,
    fees_expenses_investment     double,
    fees_expenses_investment_cat text,
    init_ira_investment          double,
    subseq_aip_investment        double
);



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

CREATE TABLE IF NOT EXISTS ib_fractional
(
    symbol         varchar(255) not null,
    main_exchange  varchar(255) not null,
    description    IB_CONTRACT_ID varchar(1024),
    ib_contract_id varchar(255),
    last_update    timestamp,
    primary key (symbol, main_exchange)
);

CREATE TABLE IF NOT EXISTS optionable
(
    symbol         varchar(255) not null,
    company_name   varchar(1024),
    details        varchar(2048),
    quick_find     varchar(2048),
    option_chain   varchar(2048),
    asset_type     varchar(255),
    last_update    timestamp
);

CREATE INDEX IF NOT EXISTS optionable_symbol_is_idx ON optionable(symbol);


