# modules/data_loader.py

import pandas as pd
import streamlit as st

from config import (
    COLUMNS_TO_HIDE,
    COLUMN_ALIASES,
    CACHE_TTL
)

@st.cache_data(ttl=CACHE_TTL)
def load_data(url):
    df = pd.read_csv(url)

    # Clean columns
    df.columns = df.columns.str.strip()

    # Standardize aliases
    df = df.rename(columns=COLUMN_ALIASES)

    # Hide restricted columns
    cols_to_drop = [c for c in COLUMNS_TO_HIDE if c in df.columns]
    df = df.drop(columns=cols_to_drop, errors="ignore")

    # Fill blanks
    df = df.fillna("")

    return df
