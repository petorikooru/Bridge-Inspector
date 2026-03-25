# Dashboard KAI

Selamat datang di Dashboard KAI!

Di dalam aplikasi ini, anda dapat melihat data berupa akselometer dan inclinometer
yang telah terhubung dengan protokol MQTT!

## Running the Application

```sh
cd ./src/
pyuic6 dashboard.ui -o dashboard.py
```

## Flow

`NodeRED [MQTT] -> Python`

Probably will use gzip compression for the csv data

## References

[GZIP compression](https://medium.com/@shahrullo/data-compression-in-csv-up-to-85-116e68d87d7a)
[LZMA compression](https://medium.com/data-folks-indonesia/optimizing-data-i-o-analyzing-joblibs-compression-techniques-1fa019d411b7)
[Polars processing](https://medium.com/@mariusz_kujawski/converting-csv-files-to-parquet-with-polars-pandas-dask-and-dackdb-52a77378349d)
