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

## Data flow

```
NVE API ─────────────────────────────► Streamlit (Reservoirs page)

ENTSO-E API ──► Cassandra (local) ──► Spark ──► MongoDB ──► Streamlit (Flows page)
```

Cassandra runs locally and cannot be reached from Streamlit Cloud, so the
curated result is written to MongoDB, which the deployed app reads.
