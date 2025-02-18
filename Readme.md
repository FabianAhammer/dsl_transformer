 ______   _______  _        _______ ______  _       
(  __  \ (  ____ \( \      (  ____ \(  ____ \( (    /|
| (  \  )| (    \/| (      | (    \/| (    \/|  \  ( |
| |   ) || (_____ | |      | |      | (__    |   \ | |
| |   | |(_____  )| |      | | ____ |  __)   | (\ \) |
| |   ) |      ) || |      | | \_  )| (      | | \   |
| (__/  )/\____) || (____/\| (___) || (____/\| )  \  |
(______/ \_______)(_______/(_______)(_______/|/    )_)
                                                      


## DSL Generator from JIRA Tempo Entries

This program generates a Dienststundenliste (DSL) from your JIRA Tempo Entries. It also creates a diff .xlsx file for any conflicts found, allowing you to easily copy in the necessary changes.

### 🚀 Installation

Make sure you have Python installed, then install the required dependencies:

pip install -r requirements.txt

### 🔧 Configuration

You must set the filename and JIRA API Key inside main.py before running the script.

### ▶️ Usage

Run the program with:

python main.py

### 📂 Output

Dienststundenliste: Generated from your JIRA Tempo entries.

Conflict Diff (.xlsx): Highlights any discrepancies found.