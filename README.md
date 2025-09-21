# 🔥 Teleforge

**Your automation toolkit for Telegram.**

Teleforge is a modular Python framework, built with Telethon and Rich, that provides a powerful command-line interface (CLI) to run a suite of on-demand tasks on Telegram. Analyze chats, manage contacts, export data, apply watermarks, and much more, all from a clean, organized, and easily expandable codebase.

---

## ⚠️ Responsible Use Warning

This project includes powerful features, such as bulk messaging, which can be easily interpreted as spam by Telegram. Improper use **can lead to the limitation or permanent banning of your account**.

-   **Use at your own risk.** The author is not responsible for any damage or blocks to your account.
-   **"Warm up" your account:** New accounts or those with low activity are more likely to be limited. Use them manually for a while before automating tasks.
-   **Do not spam:** Use this tool ethically and consciously.

---

## ✨ Features

Teleforge is a Swiss Army knife for Telegram power users, providing a collection of independent, on-demand tools:

#### Data & Analytics
-   **Chat Analyzer:** Get statistics on any chat, including the most active users and a breakdown of shared media types over a custom number of messages.
-   **Member Exporter:** Export the full member list of any group to a `.csv` file, including user IDs, names, and last seen status.
-   **Global Search:** Search for a keyword across *all* your chats (groups, channels, DMs) and save the results to a detailed text file.
-   **Chat History Archiver:** Create a full backup of a chat's text history to a `.txt` or `.json` file, with flexible date filters (all-time, today, yesterday, or a custom range).

#### Content & Media Management
-   **Advanced Media Downloader:** Download media from any chat with powerful filters for media type (photos, videos, docs) and/or a specific user.
-   **Image Watermarker:** Automatically apply a custom watermark to a batch of images from a local folder and upload them directly to a chat, with options for position, scale, and opacity.

#### Account & Chat Management
-   **Contact Manager:** Clean up your address book by finding and bulk-deleting deleted accounts or long-inactive contacts.
-   **Bulk Archiver:** Organize your chat list by archiving hundreds of chats at once based on rules like mute status or inactivity.
-   **Bulk Messenger:** Send direct messages to a random subset of group members, with built-in safety delays to mitigate spam detection.

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
-   **Navigate the Menu:** Use the numbers to choose the desired feature from the main menu.

---

## 📄 License

This project is under the MIT License. See the `LICENSE` file for more details.