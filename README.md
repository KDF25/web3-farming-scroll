# Scroll Farming Automation

---

## 🚀 Description

This project is an automated system for interacting with DeFi protocols on the Scroll network. The main features include:

- **Automated bridging between networks**
- **Token swaps across various DEXes**
- **Asset management via OKX**
- **Integration with Binance API**

---

### 📝 Main Scripts

- **main_action.py** – Performs various DeFi actions and orchestrates complex scenarios
- **main_bridge.py** – Handles asset bridging between networks
- **main_swap.py** – Executes token swaps across supported DEXes
- **main_okx_transfer.py** – Manages asset transfers to/from OKX exchange

### ⚙️ Configuration

- `config.py` – Main project settings
- `abi/` – Smart contract ABIs
- `data/` – Data and configuration files

### 🗄️ Database

- `database/` – Modules for database operations

---

## ⚙️ Config Constants

### Binance Configuration

| Name               | Description                      | Example/Default |
| ------------------ | -------------------------------- | --------------- |
| BINANCE_API_KEY    | Binance API key                  | `''`            |
| BINANCE_API_SECRET | Binance API secret               | `''`            |
| FULL_CONVERSION    | Full conversion flag             | `False`         |
| REMAINDER          | USDT Remainder on wallet         | `(50, 75)`      |
| max_tries          | Maximum number of retry attempts | `5`             |

### Database Configuration

| Name        | Description         | Example/Default |
| ----------- | ------------------- | --------------- |
| pg_host     | PostgreSQL host     | `""`            |
| pg_user     | PostgreSQL username | `""`            |
| pg_password | PostgreSQL password | `''`            |
| database    | Database name       | `""`            |

### OKX Configuration

| Name     | Description                                   | Example/Default                                                                                                                          |
| -------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| OKX_KEYS | Dictionary containing OKX account credentials | `{ 'Account_1': { 'api_key': '', 'api_secret': '', 'password': '' }, 'Account_2': { 'api_key': '', 'api_secret': '', 'password': '' } }` |

### Proxy Configuration

| Name        | Description                  | Example/Default |
| ----------- | ---------------------------- | --------------- |
| all_proxies | List of proxy servers to use | `[]`            |

---

## 🛠️ Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/KDF25/web3-farming-scroll.git
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚦 Usage

### Bridging Operations

```bash
python main_bridge.py
```

### Token Swaps

```bash
python main_swap.py
```

### OKX Operations

```bash
python main_okx_transfer.py
```

### Other Scripts

- Complex actions:  
  `python main_action.py`

---

## 📋 Requirements

- Python 3.8+
- starknet-py
- web3
- SQLAlchemy
- Other dependencies from `requirements.txt`

## 🔒 Security

- Store API keys securely
- Never commit configuration files with keys
- Use proxies to prevent IP blocks
- Double-check all transactions before sending
