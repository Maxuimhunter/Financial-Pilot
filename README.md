# Personal Budget Tracker

A comprehensive personal finance application built with Streamlit that helps you track your income, expenses, and savings across different months of the year.

## Features

- 📅 Monthly budget tracking for all 12 months
- 💰 Budget vs. Actual spending comparison
- 📊 Interactive charts and visualizations
- 💾 Local database storage (MySQL)
- 📈 Annual overview and trends
- 📥/📤 Data import/export capabilities

## Prerequisites

### For Docker Setup (Recommended)
- Docker
- Docker Compose

### For Local Setup
- Python 3.8 or higher
- MySQL Server
- pip (Python package manager)

## Installation

### Docker Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd budget-tracker
   ```

2. **Configure environment variables**
   ```bash
   cp .env.docker .env
   ```
   - Edit `.env` if you want to customize the database credentials

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd budget-tracker
   ```

2. **Create and activate a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MySQL**
   - Install MySQL Server if you haven't already
   - Create a new database named `budget_tracker`
   - Update the `.env` file with your MySQL credentials:
     ```
     DB_HOST=localhost
     DB_USER=your_username
     DB_PASSWORD=your_password
     DB_NAME=budget_tracker
     ```

## Usage

### Option 1: Running with Docker (Recommended)

1. **Copy the Docker environment file**
   ```bash
   cp .env.docker .env
   ```

2. **Start the application with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Access the web interface**
   - Open your browser and go to `http://localhost:8501` for the Budget Tracker app
   - Open your browser and go to `http://localhost:8080` for phpMyAdmin database admin

4. **Stop the application**
   ```bash
   docker-compose down
   ```

5. **View logs**
   ```bash
   docker-compose logs -f
   ```

6. **Reset the database**
   ```bash
   docker-compose down -v  # This removes the database volume
   docker-compose up -d
   ```

### Option 2: Running Locally

1. **Start the application**
   ```bash
   streamlit run app.py
   ```

2. **Access the web interface**
   - Open your browser and go to `http://localhost:8501`

**Using the application** (applies to both Docker and local setup):
- Select a month from the sidebar
- Enter your budgeted and actual amounts
- Click "Save Changes" to update the database
- View spending breakdowns in the charts section

## Features in Detail

### Monthly Budget
- Add/edit budget categories
- Track budgeted vs. actual spending
- Automatic calculation of totals and differences
- Visual spending breakdown by category

### Annual Overview
- View spending trends over the year
- Compare monthly budgets and actuals
- Track savings rate over time

### Data Management
- Export data to Excel or CSV
- Import data from existing spreadsheets
- Reset budget for any month

## Database Schema

The application uses the following database structure:

- **months**: Stores month names and IDs
- **budget**: Tracks budgeted and actual amounts for each category and month
- **expenses**: Stores individual expense records with descriptions and dates

## Docker Architecture

The Docker setup includes:
- **MySQL 8.0**: Database server with persistent volume for data storage
- **Streamlit App**: Python application running in a lightweight container
- **phpMyAdmin**: Web-based database administration interface at http://localhost:8080
- **Network**: Isolated bridge network for secure communication between services
- **Health Checks**: Automatic health monitoring for MySQL container

### phpMyAdmin Access

phpMyAdmin provides a web-based interface to manage your MySQL database:

- **URL**: http://localhost:8080
- **Username**: Use the `DB_USER` from your `.env` file (default: `budget_user`)
- **Password**: Use the `DB_PASSWORD` from your `.env` file (default: `budget_password`)
- **Server**: Automatically configured to connect to the MySQL container

You can use phpMyAdmin to:
- View and edit database tables
- Run SQL queries
- Import/export data
- Manage users and permissions
- Monitor database performance

## Troubleshooting

### Docker Issues
- **Container won't start**: Check logs with `docker-compose logs`
- **MySQL connection issues**: Ensure MySQL container is healthy: `docker-compose ps`
- **Port conflicts**: Change the port mapping in `docker-compose.yml` (e.g., `8502:8501` for app, `8081:80` for phpMyAdmin)
- **phpMyAdmin won't connect**: Ensure MySQL container is running and credentials in `.env` match
- **Database reset**: Run `docker-compose down -v` to remove the database volume and start fresh

### Local Setup Issues
- **MySQL Connection Issues**: Ensure MySQL server is running and the credentials in `.env` are correct
- **Missing Dependencies**: Run `pip install -r requirements.txt` to install all required packages
- **Port Already in Use**: Change the port in the Streamlit command: `streamlit run app.py --server.port 8502`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Happy Budgeting! 💰📊
