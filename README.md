# KODKAFA "nataly" Plugin

[![KODKAFA](https://img.shields.io/badge/KODKAFA-Plugin-000000)](https://github.com/kodkafa/kod)
[![License](https://img.shields.io/github/license/kodkafa/nataly)](https://github.com/kodkafa/nataly/blob/main/LICENSE.md)

This is a python "nataly" plugin for KODKAFA.
The plugin is a wrapper for the nataly library. 
And the KODKAFA remember the complex paramaters in the history. 

## Nataly Lib
nataly lib pip: https://pypi.org/project/nataly/ 

[![PyPI Downloads](https://img.shields.io/pypi/dm/nataly)](https://pypi.org/project/nataly/)

nataly lib source: https://github.com/gokerDEV/nataly

## KODKAFA CLI
source: https://github.com/kodkafa/kod

### macOS (Homebrew):

```bash
brew tap kodkafa/tap
brew install --cask kodkafa
```
[![Install with Homebrew](https://img.shields.io/badge/Homebrew-Install-2a7d2e?logo=homebrew&logoColor=white)](https://github.com/kodkafa/kod#macos-homebrew)

## Installation

Using KODKAFA:

- From Git URL:
  - `kod add https://github.com/kodkafa/nataly.git`
- From local folder (first download the source):
  - `kod add ./nataly`

Then install/load dependencies:
- `kod load nataly`

## Usage

Example:

`kod run nataly --person "Joe Doe" --birth "1990-02-27 09:15" --tz "+02:00" --lat 38.25 --lon 27.09 --house-system Placidus --format both`

## Ephemeris (optional)

Asteroid calculations may require ephemeris files.
- You can provide a directory with `--ephe-path`
- Or find `NATALY_EPHE_PATH` environment variable
- Or create an `ephe/` directory in the plugin folder and place files there
