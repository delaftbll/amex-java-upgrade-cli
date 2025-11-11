# AmEx Java Upgrade CLI - Usage Examples

This document provides detailed usage examples for the AmEx Java Upgrade CLI tool.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Phase-by-Phase Examples](#phase-by-phase-examples)
3. [Advanced Usage](#advanced-usage)
4. [Output Files](#output-files)
5. [Interpreting Results](#interpreting-results)

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd amex-java-upgrade-cli

# Install dependencies
pip install -r requirements.txt
```

### Run Complete Workflow

```bash
# Run all phases in sequence
python amex_java_upgrade.py --stage all
```

This will execute all four phases (assessment, planning, migration, testing) and generate a comprehensive PDF report.

## Phase-by-Phase Examples

### 1. Assessment Phase

The assessment phase analyzes your application inventory and identifies compatibility risks for Java 17 migration.

```bash
python amex_java_upgrade.py --stage assessment
```

**What it does:**
- Loads application inventory from `data/app_inventory.csv`
- Analyzes each application for Java 17 compatibility issues
- Identifies risks like javax namespace changes, deprecated APIs, Spring Boot incompatibilities
- Calculates risk scores and effort estimates
- Generates a detailed assessment report

**Output:**
- Console report with detailed risk analysis
- `output/assessment_report.txt` - Text report with all findings
- Risk levels: HIGH, MEDIUM, LOW
- Estimated effort in days for each application

**Example Output:**
```
================================================================================
JAVA UPGRADE ASSESSMENT REPORT
Generated: 2025-11-11 23:39:56
================================================================================

Total Applications Analyzed: 15
High Risk Applications: 5
Medium Risk Applications: 10
Low Risk Applications: 0

Total Estimated Effort: 263.3 days
```

### 2. Planning Phase

The planning phase generates a prioritized migration plan with recommended tools and strategies.

```bash
python amex_java_upgrade.py --stage planning
```

**What it does:**
- Takes assessment results and creates migration waves
- Prioritizes applications by risk level and criticality
- Groups applications into manageable migration waves
- Generates detailed migration steps for each application
- Includes rollback strategies

**Output:**
- Console summary of migration plan
- `output/migration_plan.json` - Detailed JSON migration plan
- Migration waves with effort estimates
- Recommended tools (OpenRewrite, jdeps, etc.)

**Example Output:**
```
================================================================================
MIGRATION PLAN SUMMARY
================================================================================

Total Applications: 15
Migration Waves: 11

Wave 1:
  Applications: 1
  Estimated Effort: 18.9 days
  Apps: CardAuthService
```

**JSON Structure:**
```json
{
  "plan_version": "1.0",
  "total_applications": 15,
  "migration_waves": [...],
  "recommended_tools": [...],
  "applications": [
    {
      "name": "CardAuthService",
      "risk_level": "high",
      "migration_steps": [...],
      "rollback_strategy": {...}
    }
  ]
}
```

### 3. Migration Simulation Phase

The migration phase simulates the actual migration process for selected applications.

```bash
# Migrate specific applications
python amex_java_upgrade.py --stage migration --apps CardAuthService,FraudDetectionService

# Or migrate first 3 applications from plan (default when using --stage all)
python amex_java_upgrade.py --stage migration
```

**What it does:**
- Simulates code refactoring (javax → jakarta, Date API updates, etc.)
- Updates build configurations
- Runs mock build processes
- Reports success/failure for each application

**Output:**
- Console output showing migration progress
- Build scripts in `output/` directory
- Success/failure status for each application

**Example Output:**
```
============================================================
Migrating: CardAuthService
============================================================
  ✓ Create feature branch for Java 17 migration
  ✓ Update build configuration (pom.xml/build.gradle) to Java 17
  ✓ Run dependency analysis with jdeps
  ✓ Apply OpenRewrite recipes for javax to jakarta migration
  ✓ Upgrade Spring Boot to 2.7.x or 3.x
  ✓ Refactored: javax.servlet → jakarta.servlet (45 files)
  ✓ Refactored: javax.persistence → jakarta.persistence (32 files)
  ✓ Build: SUCCESS
```

### 4. Testing Phase

The testing phase runs mock unit and integration tests with automatic rollback on failure.

```bash
# Test specific applications
python amex_java_upgrade.py --stage testing --apps CardAuthService,FraudDetectionService

# Or test applications from previous migration
python amex_java_upgrade.py --stage testing
```

**What it does:**
- Runs mock unit tests (150-300 tests per app)
- Runs mock integration tests (30-60 tests per app)
- Calculates pass rates
- Triggers automatic rollback if pass rate < 95%
- Reports detailed test results

**Output:**
- Console output with test results
- Pass/fail rates for unit and integration tests
- Rollback notifications if triggered

**Example Output:**
```
============================================================
Testing: CardAuthService
============================================================

  Unit Tests:
    Total: 253
    Passed: 244
    Failed: 9
    Pass Rate: 96.4%

  Integration Tests:
    Total: 42
    Passed: 40
    Failed: 2
    Pass Rate: 95.2%

  Overall Pass Rate: 96.3%

  ✓ All tests passed - Migration successful
```

**Rollback Example:**
```
  Overall Pass Rate: 93.5%

  ⚠ ROLLBACK TRIGGERED - Pass rate below 95% threshold

  Rollback Procedure:
    → Reverting to Java 8 deployment...
    → Restoring previous build artifacts...
    → Verifying service health checks...
    → Notifying stakeholders...
    ✓ Rollback completed successfully
```

## Advanced Usage

### Custom Application Selection

You can specify which applications to migrate/test using the `--apps` flag:

```bash
# Single application
python amex_java_upgrade.py --stage migration --apps CardAuthService

# Multiple applications (comma-separated, no spaces)
python amex_java_upgrade.py --stage migration --apps CardAuthService,FraudDetectionService,PaymentProcessingEngine

# Test specific applications
python amex_java_upgrade.py --stage testing --apps APIGateway,BillingService
```

### Running Individual Phases

You can run phases independently for iterative development:

```bash
# 1. First, run assessment
python amex_java_upgrade.py --stage assessment

# 2. Review the assessment report, then generate plan
python amex_java_upgrade.py --stage planning

# 3. Review the plan, then migrate selected apps
python amex_java_upgrade.py --stage migration --apps CardAuthService

# 4. Test the migrated applications
python amex_java_upgrade.py --stage testing --apps CardAuthService
```

### Complete End-to-End Workflow

For a complete simulation of the entire upgrade process:

```bash
python amex_java_upgrade.py --stage all
```

This will:
1. Run assessment on all 15 applications
2. Generate migration plan
3. Migrate first 3 applications (by priority)
4. Test the migrated applications
5. Generate comprehensive PDF report

## Output Files

After running the tool, you'll find the following files in the `output/` directory:

| File | Description |
|------|-------------|
| `assessment_report.txt` | Detailed text report of compatibility assessment |
| `migration_plan.json` | Complete migration plan in JSON format |
| `java_upgrade_report_YYYYMMDD_HHMMSS.pdf` | Comprehensive PDF report (when using --stage all) |
| `amex_upgrade.log` | Detailed log file of all operations |
| `build_<AppName>.sh` | Mock build scripts for each migrated application |

## Interpreting Results

### Risk Levels

- **HIGH**: Applications with risk score ≥ 10
  - Multiple compatibility issues
  - Requires significant refactoring
  - High effort estimate
  
- **MEDIUM**: Applications with risk score 5-9
  - Some compatibility issues
  - Moderate refactoring needed
  - Medium effort estimate
  
- **LOW**: Applications with risk score < 5
  - Minimal compatibility issues
  - Minor refactoring needed
  - Low effort estimate

### Risk Score Components

Risk scores are calculated based on:
- javax namespace usage (+3 points)
- Deprecated Date API (+2 points)
- sun.misc.Unsafe usage (+4 points)
- Deprecated Thread methods (+2 points)
- SecurityManager usage (+3 points)
- JAXB removal (+3 points)
- Incompatible Spring Boot version (+4 points)
- Application criticality (high: +2, medium: +1, low: 0)

### Test Pass Rate Thresholds

- **≥ 95%**: Migration successful, no rollback
- **< 95%**: Automatic rollback triggered

### Migration Waves

Applications are grouped into waves based on:
1. Risk level (high-risk apps first)
2. Criticality (high-criticality apps prioritized)
3. Effort estimates (waves capped at ~30 days effort)

## Running Unit Tests

To run the comprehensive test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=amex_java_upgrade --cov-report=term-missing

# Run specific test class
pytest tests/test_amex_java_upgrade.py::TestJavaUpgradeAssessment -v

# Run specific test
pytest tests/test_amex_java_upgrade.py::TestJavaUpgradeAssessment::test_load_inventory_success -v
```

## Customizing the Inventory

To use your own application inventory:

1. Create a CSV file with the following columns:
   - `app_name`: Name of the application
   - `current_java_version`: Current Java version (e.g., "8")
   - `dependencies`: Semicolon-separated list of dependencies
   - `known_issues`: Known compatibility issues
   - `lines_of_code`: Approximate lines of code
   - `criticality`: high, medium, or low

2. Place the file at `data/app_inventory.csv`

3. Run the tool as normal

**Example CSV:**
```csv
app_name,current_java_version,dependencies,known_issues,lines_of_code,criticality
MyApp,8,Spring Boot 2.3.0;Hibernate 5.4.0,javax namespace,50000,high
```

## Troubleshooting

### Issue: "Inventory file not found"
**Solution**: Ensure `data/app_inventory.csv` exists in the project directory.

### Issue: "No matching applications found for migration"
**Solution**: Check that the application names in `--apps` match exactly with names in the inventory CSV.

### Issue: Tests failing
**Solution**: Run `pytest tests/ -v` to see detailed test output and identify the issue.

## Best Practices

1. **Start with Assessment**: Always run assessment first to understand the scope
2. **Review the Plan**: Examine the migration plan JSON before starting migrations
3. **Migrate in Waves**: Follow the recommended wave structure for manageable migrations
4. **Test Thoroughly**: Always run the testing phase after migration
5. **Keep Logs**: Review `output/amex_upgrade.log` for detailed operation logs
6. **Backup First**: In a real scenario, ensure backups before migration
7. **Monitor Rollbacks**: If rollbacks occur frequently, review and address underlying issues

## Support

For issues or questions, refer to the main README.md or check the log files in the `output/` directory.
