# FFXIV Free Company Financial Management System

A Streamlit-based financial management system for Final Fantasy XIV Free Companies, designed to streamline donation tracking and provide rich member insights with a gaming-inspired interface.

## Features

- 📊 Dashboard with financial overview
- 💰 Donation tracking and history
- 🏠 Housing bid management
- 📈 Expense tracking and categorization
- 👥 Member management with Lodestone integration
- 🎨 FFXIV-themed UI
- 💾 Automatic data persistence between deployments

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   streamlit run main.py
   ```

## Data Persistence

The application uses Replit's persistent storage system to maintain data between deployments. All data is stored in the `data/` directory.

- Member data
- Donation records
- Expense tracking
- Housing bids

## Configuration

The application is configured to run on port 5000 with the following settings:
```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues related to the application functionality, please create an issue in the GitHub repository.
For Replit-specific deployment questions, please contact Replit support.