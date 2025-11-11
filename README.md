# AmEx Java Upgrade CLI Tool

A comprehensive CLI application that simulates the process of upgrading Java versions across an enterprise environment like American Express.

## Features

- **Assessment Phase**: Scan inventory of Java applications and identify compatibility risks
- **Planning Phase**: Generate migration plans with risk scoring and prioritization
- **Migration Simulation**: Mock code refactoring and build processes
- **Testing Phase**: Run mock unit/integration tests with rollback capabilities
- **Reporting**: Generate detailed reports in console and PDF format

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Assessment Phase
```bash
python amex_java_upgrade.py --stage assessment
```

### Planning Phase
```bash
python amex_java_upgrade.py --stage planning
```

### Migration Simulation
```bash
python amex_java_upgrade.py --stage migration --apps CardAuthService,FraudDetectionService
```

### Testing Phase
```bash
python amex_java_upgrade.py --stage testing --apps CardAuthService
```

### Run All Phases
```bash
python amex_java_upgrade.py --stage all
```

## Project Structure

```
amex-java-upgrade-cli/
├── amex_java_upgrade.py       # Main CLI application
├── data/
│   └── app_inventory.csv      # Sample application inventory
├── output/                     # Generated reports and plans
├── tests/                      # Unit tests
├── requirements.txt
└── README.md
```

## Sample Data

The tool includes a sample inventory of 15 fictional AmEx applications running on Java 8, including:
- CardAuthService
- FraudDetectionService
- PaymentProcessingEngine
- RewardsCalculator
- And more...

## Testing

```bash
pytest tests/ -v --cov
```

## Success Criteria

- Runs end-to-end without errors
- Produces readable console and PDF reports
- Passes all unit tests with 95%+ coverage
- Handles errors gracefully with proper logging
