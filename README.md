# 🔥 Teleforge

**Your automation toolkit for Telegram.**

Teleforge is a modular Python framework, built with Telethon and Rich, that provides a powerful command-line interface (CLI) to run automated tasks on Telegram. Extract media from any chat or send messages to group members, all from a clean, organized, and easily expandable codebase.

---

## ⚠️ Responsible Use Warning

This project includes powerful features, such as bulk messaging, which can be easily interpreted as spam by Telegram. Improper use **can lead to the limitation or permanent banning of your account**.

-   **Use at your own risk.** The author is not responsible for any damage or blocks to your account.
-   **"Warm up" your account:** New accounts or those with low activity are more likely to be limited. Use them manually for a while before automating tasks.
-   **Do not spam:** Use this tool ethically and consciously.

---

## ✨ Features

-   **Professional Command-Line Interface:** A beautiful and intuitive CLI built with the `rich` library.
-   **Modular Structure:** Features are organized into modules (`downloader`, `messaging`), making maintenance and the addition of new features easy.
-   **Media Downloader:** Download all photos, videos, and documents from any group or channel, including those with protected content.
-   **Member Messenger:** Send direct messages to a selected number of group members, with built-in safety delays to mitigate the risk of account limitation.
-   **Secure Configuration:** Credentials and session files are kept out of version control via `.gitignore`.

---

## 🚀 Setup and Installation

**Prerequisites:**
* Python 3.8+
* A Telegram Account

### Step 1: Clone the Repository

```bash
git clone [https://github.com/YOUR-USERNAME/Teleforge.git](https://github.com/YOUR-USERNAME/Teleforge.git)
cd Teleforge
```

### Step 2: Create a Virtual Environment

It is a recommended practice to use a virtual environment to isolate project dependencies.

```bash
# Create the environment
python -m venv venv

# Activate the environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Your Credentials

1.  **Get your API keys:** Go to [my.telegram.org](https://my.telegram.org), log in, and navigate to "API development tools" to get your `api_id` and `api_hash`.
2.  **Create the configuration file:** In the project's root directory, create a file named `config.ini` and fill it with your credentials, following the example below:

    ```ini
    [telegram_credentials]
    api_id = 1234567
    api_hash = abcdef1234567890abcdef1234567890

    [session_settings]
    session_name = teleforge_session
    ```

---

## ▶️ How to Run

With everything configured, run the main script:

```bash
python main.py
```

-   **First Login:** On the first run, the script will ask for your phone number, the login code sent to you by Telegram, and, if applicable, your two-factor authentication (2FA) password. A session file will be saved for future logins.
-   **Navigate the Menu:** Use the numbers to choose the desired feature.

---

## 🏗️ Project Structure

```
/Teleforge/
|-- main.py               # Main entry point, with the menu
|-- modules/              # Folder for each feature/module
|   |-- downloader.py
|   |-- messaging.py
|-- core/                 # Core functions (connection)
|   |-- client.py
|-- utils/                # Utility functions (chat selector)
|   |-- chat_selector.py
|-- config.ini            # Your credentials (IGNORED BY GIT)
|-- requirements.txt      # Project dependencies
|-- .gitignore            # Files to be ignored by Git
|-- README.md             # This file
```

---

## 📄 License

This project is under the MIT License. See the `LICENSE` file for more details.