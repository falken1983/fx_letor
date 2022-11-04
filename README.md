# fx_letor
LEarning TO Rank Currency Investments

## Table of contents
1. [Introduction](#introduction)
2. [Installation & Reproducibility](#installation)
3. [Development roadmap](#development-roadmap)
4. [Jupyter Noteboks](#notebooks)
5. [Development](#development)
6. [Disclaimers](#disclaimers)

## Introduction

This repository analyses currency screening from G11 countries by means of learning-to-rank (LETOR) machine learning algorithms with the aim to improve cumulative gains of the equally weighted currency basket.

_Features construction and Selection_ is based on **PMs** (Financial Risk and Performance Measures).

Simple Trading Rules will be inferred from Rankers in order to outperform simple static strategies.

These rankers are directly based on supervised Learning-To-Rank (**LETOR** from now on) Algos.

**LETOR** were mainly developed for other Deep and Machine Learning archetypical scopes such as web search engines.

The repo will be structured along four tiers:

1. **Dataset Construction**.

2. **Regress-Then-Rank and LETOR methods**.

3. **Out-Of-Sample (Test) Portfolio Performance**.

4. **Frontend**

5. **Documentation**

## Installation

## Learning-To-Rank training

## Development roadmap

We are working on expanding the coverage of the repo. Areas under active development are:

  * Data: 
  * Implementation of the following Regress-Then-Rank and LETOR Algos:
      * LinearRegression (baseline)
      * ElasticNet (RtR)
      * XGBRegressor (RtR)
      * XGBClassifier (Pointwise LETOR)      
      * XGBRanker (Pairwise LETOR)
      * LambdaMART (LightGBM Pairwise LETOR)
      
  * Backtesting And Conclusions: Empirical evidence supporting Currency Screening methodologies based on LETOR Algos.
  * Frontend:
      * `streamlit`-based Financial KID (Key Information Dashboard)

## Notebooks

TBA

### Development dependencies

This library has the following dependencies:

TBA

### Commonly used commands

Clone the GitHub repository:

```sh
git clone https://github.com/falken1983/fx_letor.git
```

After you run

```sh
cd fx_letor

```

There's `environments.yml` and `requirements.txt` but they are still under changes. (`conda env`)

## Disclaimers

This repo is under active development, and notebooks may change at any time.
