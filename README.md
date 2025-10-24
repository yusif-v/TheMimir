# Mimir v0.3

Mimir is a terminal-based DFIR arsenal for digital forensics, threat intelligence, and incident response. It offers a fast, interactive interface and is easily extensible for efficient analyst workflows.

## Features

	•	Command-driven forensic and intelligence operations
	•	Case and evidence management
	•	Integration with external analysis tools
	•	Modular, extensible command framework

## Installation
```sh
git clone https://github.com/yusif-v/TheMimir.git
cd TheMimir
python3 -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```
## Usage

```sh
python main.py
```
Type help inside the terminal for available commands.

## Structure

```sh
Mimir/
├── cli/             # Command handlers
├── history/         # History and session management
├── integrations/    # External forensic integrations
├── main.py          # Entry point
└── requirements.txt
```