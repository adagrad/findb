# Financial Research Data Base

The purpose of this database is to **enable research**. 

There is not much free available financial data for a research only purpose. On the other hand a lot of APIs exist to
obtain information on a dedicated asset. What is clearly missing is a broader access to the data in contrast to very
specific API calls. 

This project should help individuals and stop their need to build their own yet individual database. This is not only 
tedious but also hits the same servers unnecessarily often for the same data. Save the planet! So this is an attempt to 
introduce an open and crowed maintained database which can be used to do research accross different assets classes, 
countries and sectors.


## Project State
At the moment the data is focussed around static data to answer 
questions like:
* how are different asset classes distributed across different countries
* which assets should be part of a model (and are supported by my broker)

Later it may be useful to add price data as well such that questions like these can be answered:
* how did certain asset classes or sectors behave in periods like crashes
* how did those assets covariance behave
* which factors can be used to building a factor model
* ...


## Data Frequency
The purpose of this database is explicitly not to provide most recent up-to-date information. However, with the help of
GitHub actions the database will be updated on a regular basis with a rather low frequency like every month.


## ETL
Every database starts with an Extract Transform and Load process. This repository is used for the extraction part. 
As of now every data source will be extracted as csv files. The next step is to load these csv files into a community
shared database. This is currently done by using a sqlite database and share it via GitHub release assets. 
Eventually one could load these files into a shared database hosted via [Dolthub](https://www.dolthub.com/). As of now
dolthub has too many issues with performance, indices and data loading (can only load specific formated csv files).


## Usage
The sqlite can be used from basically any programing language. For those using MS Excel there are integrations for Excel
as well like [SQLiteForExcel](https://github.com/govert/SQLiteForExcel) for example.

## Asking for Help 
Help with extending and maintenance is highly appreciated :-)
<br/>Just fork and PR (and remember the limits)

There are also possible improvements on the database side as well, i.e. one could create views to match assets between 
different brokers or data sources.

## Contribution
Contribute like you do with any other GitHub project by forking, and the submission of pull requests. Make sure you 
follow the ETL pattern. Use a github action to generate a data extraction preferable in csv format. Every action itself
commits the extracted data and pushes the changes back to the repository (and the full history remains).


Whenever a commit is maid on the main branch (i.e an action comples with a push or a PR is merged), the new csv data 
will be loaded into the database automatically via github actions.

Until dolt has not fixed its various performance and loading issues remember the limits:
* GitHub only supports a maximum of 100MB per file and a maximum of 1GB per repository. 
* Eeach file under release assets can have a maximum of 2GB, where the number of files is unlimited. 

