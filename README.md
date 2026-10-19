# IND320 — Project work

Course project for IND320 (NMBU). Norwegian hydropower reservoir levels and
cross-border electricity flows, shown in a Streamlit app and documented in a
Jupyter Notebook.

- **Streamlit app:** https://ind320application-knut.streamlit.app/
- **Repository:** https://github.com/Knutis1/IND320_Application

## Data sources

| Source | What it gives | How it is used |
|---|---|---|
| [NVE Magasinstatistikk API](https://biapi.nve.no/magasinstatistikk/swagger) | Weekly reservoir filling levels per area, 1995 onwards | Read live by the app and the notebook |
| [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/) | Hourly physical cross-border flows, last two years | Downloaded in the notebook, stored in Cassandra, aggregated with Spark, written to MongoDB |

Physical flow is reported separately per direction, so each connection is
downloaded as two series (out of Norway and into Norway). Timestamps are
converted to UTC before being stored.

## Folder layout

```
App/
├── main.py                 Streamlit entry point (home page)
├── requirements.txt        packages for the deployed app
├── modules/
│   ├── nve_api.py          NVE Magasinstatistikk API
│   ├── entsoe_api.py       ENTSO-E cross-border flows
│   ├── Utils.py            Streamlit caching on top of nve_api
│   └── spark_env.py        finds Java/winutils and builds the SparkSession
├── notebooks/
│   ├── Task1.ipynb         Part 1: reservoir data from CSV
│   └── Task2.ipynb         Part 2: APIs, Cassandra, Spark, MongoDB
└── pages/
    ├── 2_Reservoirs.py     interval slider, EL/NO/VASS radio, table + plot
    ├── 3_Flows.py          MongoDB: pie chart and hourly line plot
    └── 4_About.py
```

## Running the app locally

```
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r App/requirements.txt
.\.venv\Scripts\python.exe -m streamlit run App/main.py
```

The Flows page reads from MongoDB, so it needs `App/.streamlit/secrets.toml`:

```toml
MONGO_URI = "mongodb+srv://<user>:<password>@<cluster>.mongodb.net/"
```

That file is not in the repository. On Streamlit Cloud the same value goes in
the app's Secrets settings.

## Running the notebook

Part 2 needs more than the app does:

1. **Cassandra** in Docker:

   ```
   docker run --name cassandra -p 9042:9042 -e MAX_HEAP_SIZE=2G -e HEAP_NEWSIZE=400M -d cassandra:5.0
   ```

   The keyspace and table are created with `cqlsh` inside the container (the
   Python `cassandra-driver` cannot be imported on Python 3.12, and Spark uses
   the connector jar rather than that driver):

   ```
   docker exec cassandra cqlsh -e "CREATE KEYSPACE IF NOT EXISTS ind320 WITH replication = {'class':'SimpleStrategy','replication_factor':1};"
   docker exec cassandra cqlsh -e "CREATE TABLE IF NOT EXISTS ind320.crossborder_flows (connection text, direction text, ts timestamp, flow_mw double, PRIMARY KEY ((connection, direction), ts));"
   ```

2. **Java 17** and, on Windows, `winutils.exe` + `hadoop.dll` in `C:\hadoop\bin`.
   `modules/spark_env.py` locates both and sets the environment itself.

3. **A `.env` file** in the project root (not in the repository):

   ```
   ENTSOE_TOKEN=<your token>
   MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
   ```

4. Extra packages used only by the notebook:

   ```
   pip install pyspark==3.5.3 entsoe-py python-dotenv matplotlib
   ```

The ENTSO-E download takes several minutes, so it is cached to
`App/notebooks/flows_cache.parquet`. That file is not in the repository; it is
recreated on the first run and reused afterwards.

## Data flow

```
NVE API ─────────────────────────────► Streamlit (Reservoirs page)

ENTSO-E API ──► Cassandra (local) ──► Spark ──► MongoDB ──► Streamlit (Flows page)
```

Cassandra runs locally and cannot be reached from Streamlit Cloud, so the
curated result is written to MongoDB, which the deployed app reads.
