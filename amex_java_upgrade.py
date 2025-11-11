#!/usr/bin/env python3
"""
AmEx Java Upgrade CLI Tool
Simulates the process of upgrading Java versions across an enterprise environment
"""

import click
import pandas as pd
import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
logger.add(OUTPUT_DIR / "amex_upgrade.log", rotation="10 MB")


class JavaUpgradeAssessment:
    """Handles assessment phase of Java upgrade"""
    
    def __init__(self, inventory_path):
        self.inventory_path = inventory_path
        self.df = None
        self.assessment_results = []
        
    def load_inventory(self):
        """Load application inventory from CSV"""
        try:
            self.df = pd.read_csv(self.inventory_path)
            logger.info(f"Loaded {len(self.df)} applications from inventory")
            return True
        except Exception as e:
            logger.error(f"Failed to load inventory: {e}")
            return False
    
    def analyze_compatibility_risks(self):
        """Analyze each application for Java 17 compatibility risks"""
        logger.info("Starting compatibility risk analysis...")
        
        risk_patterns = {
            'javax_namespace': r'javax\.',
            'deprecated_date_api': r'Date API',
            'unsafe_usage': r'sun\.misc\.Unsafe',
            'deprecated_thread': r'Thread\.stop\(\)',
            'security_manager': r'SecurityManager',
            'jaxb_removal': r'JAXB',
            'removed_modules': r'(javax\.xml\.bind|javax\.activation)',
        }
        
        for idx, row in self.df.iterrows():
            app_name = row['app_name']
            dependencies = row['dependencies']
            known_issues = row['known_issues']
            criticality = row['criticality']
            
            risks = []
            risk_score = 0
            
            combined_text = f"{dependencies} {known_issues}"
            
            if re.search(risk_patterns['javax_namespace'], combined_text):
                risks.append("javax to jakarta namespace migration required")
                risk_score += 3
            
            if re.search(risk_patterns['deprecated_date_api'], combined_text):
                risks.append("Deprecated Date API usage detected")
                risk_score += 2
            
            if re.search(risk_patterns['unsafe_usage'], combined_text):
                risks.append("sun.misc.Unsafe usage - requires refactoring")
                risk_score += 4
            
            if re.search(risk_patterns['deprecated_thread'], combined_text):
                risks.append("Deprecated Thread.stop() usage")
                risk_score += 2
            
            if re.search(risk_patterns['security_manager'], combined_text):
                risks.append("SecurityManager deprecated in Java 17")
                risk_score += 3
            
            if re.search(risk_patterns['jaxb_removal'], combined_text):
                risks.append("JAXB removed from JDK - external dependency needed")
                risk_score += 3
            
            spring_boot_version = self._extract_spring_boot_version(dependencies)
            if spring_boot_version and self._is_spring_boot_incompatible(spring_boot_version):
                risks.append(f"Spring Boot {spring_boot_version} incompatible with Java 17")
                risk_score += 4
            
            if criticality == 'high':
                risk_score += 2
            elif criticality == 'medium':
                risk_score += 1
            
            risk_level = self._calculate_risk_level(risk_score)
            
            self.assessment_results.append({
                'app_name': app_name,
                'current_java': row['current_java_version'],
                'target_java': '17',
                'risk_level': risk_level,
                'risk_score': risk_score,
                'identified_risks': risks,
                'criticality': criticality,
                'lines_of_code': row['lines_of_code'],
                'estimated_effort_days': self._estimate_effort(risk_score, row['lines_of_code'])
            })
            
            logger.info(f"Analyzed {app_name}: Risk Level = {risk_level}, Score = {risk_score}")
        
        return self.assessment_results
    
    def _extract_spring_boot_version(self, dependencies):
        """Extract Spring Boot version from dependencies string"""
        match = re.search(r'Spring Boot ([\d.]+)', dependencies)
        return match.group(1) if match else None
    
    def _is_spring_boot_incompatible(self, version):
        """Check if Spring Boot version is incompatible with Java 17"""
        try:
            major, minor = map(int, version.split('.')[:2])
            return major < 2 or (major == 2 and minor < 5)
        except:
            return False
    
    def _calculate_risk_level(self, risk_score):
        """Calculate risk level based on score"""
        if risk_score >= 10:
            return 'high'
        elif risk_score >= 5:
            return 'medium'
        else:
            return 'low'
    
    def _estimate_effort(self, risk_score, lines_of_code):
        """Estimate migration effort in days"""
        base_effort = (lines_of_code / 10000) * 2
        risk_multiplier = 1 + (risk_score / 10)
        return round(base_effort * risk_multiplier, 1)
    
    def generate_report(self):
        """Generate assessment report"""
        logger.info("Generating assessment report...")
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("JAVA UPGRADE ASSESSMENT REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        report_lines.append(f"Total Applications Analyzed: {len(self.assessment_results)}")
        
        high_risk = sum(1 for r in self.assessment_results if r['risk_level'] == 'high')
        medium_risk = sum(1 for r in self.assessment_results if r['risk_level'] == 'medium')
        low_risk = sum(1 for r in self.assessment_results if r['risk_level'] == 'low')
        
        report_lines.append(f"High Risk Applications: {high_risk}")
        report_lines.append(f"Medium Risk Applications: {medium_risk}")
        report_lines.append(f"Low Risk Applications: {low_risk}")
        report_lines.append("")
        
        total_effort = sum(r['estimated_effort_days'] for r in self.assessment_results)
        report_lines.append(f"Total Estimated Effort: {total_effort:.1f} days")
        report_lines.append("")
        
        report_lines.append("-" * 80)
        report_lines.append("DETAILED APPLICATION ANALYSIS")
        report_lines.append("-" * 80)
        report_lines.append("")
        
        for result in sorted(self.assessment_results, key=lambda x: x['risk_score'], reverse=True):
            report_lines.append(f"Application: {result['app_name']}")
            report_lines.append(f"  Risk Level: {result['risk_level'].upper()} (Score: {result['risk_score']})")
            report_lines.append(f"  Criticality: {result['criticality']}")
            report_lines.append(f"  Lines of Code: {result['lines_of_code']:,}")
            report_lines.append(f"  Estimated Effort: {result['estimated_effort_days']} days")
            report_lines.append(f"  Identified Risks:")
            for risk in result['identified_risks']:
                report_lines.append(f"    - {risk}")
            report_lines.append("")
        
        report_lines.append("=" * 80)
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("1. Use OpenRewrite for automated refactoring of javax to jakarta namespaces")
        report_lines.append("2. Upgrade Spring Boot to version 2.5+ before migrating to Java 17")
        report_lines.append("3. Prioritize high-criticality applications with low risk scores")
        report_lines.append("4. Establish comprehensive test coverage before migration")
        report_lines.append("5. Plan for rollback procedures for each application")
        report_lines.append("")
        
        report_text = "\n".join(report_lines)
        print(report_text)
        
        output_file = OUTPUT_DIR / "assessment_report.txt"
        output_file.write_text(report_text)
        logger.success(f"Assessment report saved to {output_file}")
        
        return report_text


class JavaUpgradePlanner:
    """Handles planning phase of Java upgrade"""
    
    def __init__(self, assessment_results):
        self.assessment_results = assessment_results
        self.migration_plan = {}
    
    def generate_migration_plan(self):
        """Generate prioritized migration plan"""
        logger.info("Generating migration plan...")
        
        sorted_apps = sorted(
            self.assessment_results,
            key=lambda x: (
                {'high': 0, 'medium': 1, 'low': 2}[x['risk_level']],
                {'high': 0, 'medium': 1, 'low': 2}[x['criticality']],
                x['risk_score']
            )
        )
        
        waves = []
        current_wave = []
        current_wave_effort = 0
        max_wave_effort = 30
        
        for app in sorted_apps:
            if current_wave_effort + app['estimated_effort_days'] > max_wave_effort and current_wave:
                waves.append(current_wave)
                current_wave = []
                current_wave_effort = 0
            
            current_wave.append(app['app_name'])
            current_wave_effort += app['estimated_effort_days']
        
        if current_wave:
            waves.append(current_wave)
        
        self.migration_plan = {
            'plan_version': '1.0',
            'generated_at': datetime.now().isoformat(),
            'total_applications': len(self.assessment_results),
            'migration_waves': [],
            'recommended_tools': [
                {
                    'name': 'OpenRewrite',
                    'purpose': 'Automated code refactoring for Java upgrades',
                    'url': 'https://docs.openrewrite.org/'
                },
                {
                    'name': 'jdeps',
                    'purpose': 'Java dependency analysis tool',
                    'url': 'https://docs.oracle.com/en/java/javase/17/docs/specs/man/jdeps.html'
                },
                {
                    'name': 'Eclipse Migration Toolkit',
                    'purpose': 'IDE-based migration assistance',
                    'url': 'https://www.eclipse.org/'
                }
            ],
            'applications': []
        }
        
        for idx, wave in enumerate(waves, 1):
            wave_apps = [app for app in sorted_apps if app['app_name'] in wave]
            wave_effort = sum(app['estimated_effort_days'] for app in wave_apps)
            
            self.migration_plan['migration_waves'].append({
                'wave_number': idx,
                'applications': wave,
                'total_effort_days': round(wave_effort, 1),
                'parallel_execution': len(wave) > 1
            })
        
        for app in sorted_apps:
            self.migration_plan['applications'].append({
                'name': app['app_name'],
                'risk_level': app['risk_level'],
                'risk_score': app['risk_score'],
                'criticality': app['criticality'],
                'estimated_effort_days': app['estimated_effort_days'],
                'migration_steps': self._generate_migration_steps(app),
                'rollback_strategy': self._generate_rollback_strategy(app)
            })
        
        plan_file = OUTPUT_DIR / "migration_plan.json"
        with open(plan_file, 'w') as f:
            json.dump(self.migration_plan, f, indent=2)
        
        logger.success(f"Migration plan saved to {plan_file}")
        
        self._print_plan_summary()
        
        return self.migration_plan
    
    def _generate_migration_steps(self, app):
        """Generate specific migration steps for an application"""
        steps = [
            "Create feature branch for Java 17 migration",
            "Update build configuration (pom.xml/build.gradle) to Java 17",
            "Run dependency analysis with jdeps",
        ]
        
        if any('javax' in risk for risk in app['identified_risks']):
            steps.append("Apply OpenRewrite recipes for javax to jakarta migration")
        
        if any('Spring Boot' in risk for risk in app['identified_risks']):
            steps.append("Upgrade Spring Boot to 2.7.x or 3.x")
        
        if any('JAXB' in risk for risk in app['identified_risks']):
            steps.append("Add JAXB runtime dependencies")
        
        steps.extend([
            "Refactor deprecated API usage",
            "Update unit tests for Java 17 compatibility",
            "Run full test suite",
            "Perform integration testing",
            "Code review and security scan",
            "Deploy to staging environment",
            "Performance testing and validation",
            "Production deployment"
        ])
        
        return steps
    
    def _generate_rollback_strategy(self, app):
        """Generate rollback strategy for an application"""
        return {
            'automated_rollback': True,
            'rollback_triggers': [
                'Test failure rate > 5%',
                'Performance degradation > 20%',
                'Critical production errors'
            ],
            'rollback_steps': [
                'Revert to previous Java 8 deployment',
                'Restore previous build artifacts',
                'Verify service health checks',
                'Notify stakeholders'
            ],
            'estimated_rollback_time_minutes': 15
        }
    
    def _print_plan_summary(self):
        """Print migration plan summary to console"""
        print("\n" + "=" * 80)
        print("MIGRATION PLAN SUMMARY")
        print("=" * 80)
        print(f"\nTotal Applications: {self.migration_plan['total_applications']}")
        print(f"Migration Waves: {len(self.migration_plan['migration_waves'])}")
        print("\nWave Breakdown:")
        
        for wave in self.migration_plan['migration_waves']:
            print(f"\n  Wave {wave['wave_number']}:")
            print(f"    Applications: {len(wave['applications'])}")
            print(f"    Estimated Effort: {wave['total_effort_days']} days")
            print(f"    Apps: {', '.join(wave['applications'])}")
        
        print("\nRecommended Tools:")
        for tool in self.migration_plan['recommended_tools']:
            print(f"  - {tool['name']}: {tool['purpose']}")
        
        print("\n" + "=" * 80 + "\n")


class JavaUpgradeMigration:
    """Handles migration simulation phase"""
    
    def __init__(self, migration_plan, selected_apps=None):
        self.migration_plan = migration_plan
        self.selected_apps = selected_apps or []
        self.migration_results = []
    
    def simulate_migration(self):
        """Simulate migration for selected applications"""
        logger.info(f"Starting migration simulation for {len(self.selected_apps)} applications...")
        
        apps_to_migrate = [
            app for app in self.migration_plan['applications']
            if app['name'] in self.selected_apps
        ]
        
        if not apps_to_migrate:
            logger.warning("No matching applications found for migration")
            return []
        
        for app in apps_to_migrate:
            logger.info(f"Migrating {app['name']}...")
            result = self._migrate_application(app)
            self.migration_results.append(result)
        
        self._print_migration_summary()
        
        return self.migration_results
    
    def _migrate_application(self, app):
        """Simulate migration of a single application"""
        result = {
            'app_name': app['name'],
            'started_at': datetime.now().isoformat(),
            'steps_completed': [],
            'refactoring_changes': [],
            'build_status': 'pending',
            'build_output': ''
        }
        
        print(f"\n{'='*60}")
        print(f"Migrating: {app['name']}")
        print(f"{'='*60}")
        
        for step in app['migration_steps'][:7]:
            print(f"  ✓ {step}")
            result['steps_completed'].append(step)
            logger.info(f"  Completed: {step}")
        
        refactoring_changes = self._simulate_code_refactoring(app)
        result['refactoring_changes'] = refactoring_changes
        
        for change in refactoring_changes:
            print(f"  ✓ {change}")
        
        build_result = self._simulate_build(app)
        result['build_status'] = build_result['status']
        result['build_output'] = build_result['output']
        
        if build_result['status'] == 'success':
            print(f"  ✓ Build: SUCCESS")
            logger.success(f"Build successful for {app['name']}")
        else:
            print(f"  ✗ Build: FAILED")
            logger.error(f"Build failed for {app['name']}")
        
        result['completed_at'] = datetime.now().isoformat()
        
        return result
    
    def _simulate_code_refactoring(self, app):
        """Simulate code refactoring changes"""
        changes = []
        
        if any('javax' in risk for risk in app.get('identified_risks', [])):
            changes.append("Refactored: javax.servlet → jakarta.servlet (45 files)")
            changes.append("Refactored: javax.persistence → jakarta.persistence (32 files)")
            changes.append("Refactored: javax.validation → jakarta.validation (18 files)")
        
        if any('Date API' in str(risk) for risk in app.get('identified_risks', [])):
            changes.append("Refactored: java.util.Date → java.time.LocalDateTime (23 files)")
        
        if any('JAXB' in str(risk) for risk in app.get('identified_risks', [])):
            changes.append("Added dependency: jakarta.xml.bind-api:3.0.1")
        
        changes.append(f"Updated build configuration for Java 17")
        changes.append(f"Updated module-info.java with required modules")
        
        return changes
    
    def _simulate_build(self, app):
        """Simulate build process"""
        logger.info(f"Simulating build for {app['name']}...")
        
        build_script = OUTPUT_DIR / f"build_{app['name']}.sh"
        build_script.write_text(f"""#!/bin/bash
echo "Building {app['name']} with Java 17..."
echo "Compiling source files..."
echo "Running static analysis..."
echo "Packaging application..."
echo "Build completed successfully!"
exit 0
""")
        build_script.chmod(0o755)
        
        try:
            result = subprocess.run(
                [str(build_script)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return {
                    'status': 'success',
                    'output': result.stdout
                }
            else:
                return {
                    'status': 'failed',
                    'output': result.stderr
                }
        except Exception as e:
            logger.error(f"Build simulation error: {e}")
            return {
                'status': 'failed',
                'output': str(e)
            }
    
    def _print_migration_summary(self):
        """Print migration summary"""
        print("\n" + "=" * 80)
        print("MIGRATION SUMMARY")
        print("=" * 80)
        
        successful = sum(1 for r in self.migration_results if r['build_status'] == 'success')
        failed = len(self.migration_results) - successful
        
        print(f"\nTotal Applications Migrated: {len(self.migration_results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(successful/len(self.migration_results)*100):.1f}%")
        
        print("\nDetailed Results:")
        for result in self.migration_results:
            status_icon = "✓" if result['build_status'] == 'success' else "✗"
            print(f"  {status_icon} {result['app_name']}: {result['build_status'].upper()}")
        
        print("\n" + "=" * 80 + "\n")


class JavaUpgradeTesting:
    """Handles testing phase with rollback simulation"""
    
    def __init__(self, migration_results):
        self.migration_results = migration_results
        self.test_results = []
    
    def run_tests(self):
        """Run mock unit and integration tests"""
        logger.info("Starting test execution...")
        
        for migration in self.migration_results:
            if migration['build_status'] != 'success':
                logger.warning(f"Skipping tests for {migration['app_name']} - build failed")
                continue
            
            logger.info(f"Testing {migration['app_name']}...")
            result = self._run_application_tests(migration)
            self.test_results.append(result)
        
        self._print_test_summary()
        
        return self.test_results
    
    def _run_application_tests(self, migration):
        """Run tests for a single application"""
        import random
        
        app_name = migration['app_name']
        
        print(f"\n{'='*60}")
        print(f"Testing: {app_name}")
        print(f"{'='*60}")
        
        unit_tests_total = random.randint(150, 300)
        unit_tests_passed = int(unit_tests_total * random.uniform(0.96, 0.99))
        unit_tests_failed = unit_tests_total - unit_tests_passed
        
        integration_tests_total = random.randint(30, 60)
        integration_tests_passed = int(integration_tests_total * random.uniform(0.95, 0.98))
        integration_tests_failed = integration_tests_total - integration_tests_passed
        
        print(f"\n  Unit Tests:")
        print(f"    Total: {unit_tests_total}")
        print(f"    Passed: {unit_tests_passed}")
        print(f"    Failed: {unit_tests_failed}")
        print(f"    Pass Rate: {(unit_tests_passed/unit_tests_total*100):.1f}%")
        
        print(f"\n  Integration Tests:")
        print(f"    Total: {integration_tests_total}")
        print(f"    Passed: {integration_tests_passed}")
        print(f"    Failed: {integration_tests_failed}")
        print(f"    Pass Rate: {(integration_tests_passed/integration_tests_total*100):.1f}%")
        
        total_tests = unit_tests_total + integration_tests_total
        total_passed = unit_tests_passed + integration_tests_passed
        overall_pass_rate = (total_passed / total_tests) * 100
        
        print(f"\n  Overall Pass Rate: {overall_pass_rate:.1f}%")
        
        result = {
            'app_name': app_name,
            'unit_tests': {
                'total': unit_tests_total,
                'passed': unit_tests_passed,
                'failed': unit_tests_failed,
                'pass_rate': round((unit_tests_passed/unit_tests_total*100), 2)
            },
            'integration_tests': {
                'total': integration_tests_total,
                'passed': integration_tests_passed,
                'failed': integration_tests_failed,
                'pass_rate': round((integration_tests_passed/integration_tests_total*100), 2)
            },
            'overall_pass_rate': round(overall_pass_rate, 2),
            'status': 'passed' if overall_pass_rate >= 95 else 'failed'
        }
        
        if result['status'] == 'failed':
            print(f"\n  ⚠ ROLLBACK TRIGGERED - Pass rate below 95% threshold")
            rollback_result = self._simulate_rollback(app_name)
            result['rollback'] = rollback_result
        else:
            print(f"\n  ✓ All tests passed - Migration successful")
            result['rollback'] = None
        
        logger.info(f"Testing completed for {app_name}: {result['status']}")
        
        return result
    
    def _simulate_rollback(self, app_name):
        """Simulate rollback procedure"""
        logger.warning(f"Initiating rollback for {app_name}")
        
        print(f"\n  Rollback Procedure:")
        print(f"    → Reverting to Java 8 deployment...")
        print(f"    → Restoring previous build artifacts...")
        print(f"    → Verifying service health checks...")
        print(f"    → Notifying stakeholders...")
        print(f"    ✓ Rollback completed successfully")
        
        return {
            'triggered': True,
            'reason': 'Test pass rate below 95% threshold',
            'completed_at': datetime.now().isoformat(),
            'status': 'success'
        }
    
    def _print_test_summary(self):
        """Print testing summary"""
        print("\n" + "=" * 80)
        print("TESTING SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'passed')
        failed = len(self.test_results) - passed
        
        total_unit_tests = sum(r['unit_tests']['total'] for r in self.test_results)
        total_unit_passed = sum(r['unit_tests']['passed'] for r in self.test_results)
        
        total_integration_tests = sum(r['integration_tests']['total'] for r in self.test_results)
        total_integration_passed = sum(r['integration_tests']['passed'] for r in self.test_results)
        
        print(f"\nApplications Tested: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed (Rolled Back): {failed}")
        
        print(f"\nTotal Unit Tests: {total_unit_tests}")
        print(f"Unit Tests Passed: {total_unit_passed}")
        print(f"Unit Test Pass Rate: {(total_unit_passed/total_unit_tests*100):.1f}%")
        
        print(f"\nTotal Integration Tests: {total_integration_tests}")
        print(f"Integration Tests Passed: {total_integration_passed}")
        print(f"Integration Test Pass Rate: {(total_integration_passed/total_integration_tests*100):.1f}%")
        
        print("\nApplication Status:")
        for result in self.test_results:
            status_icon = "✓" if result['status'] == 'passed' else "✗"
            rollback_note = " (ROLLED BACK)" if result.get('rollback') else ""
            print(f"  {status_icon} {result['app_name']}: {result['overall_pass_rate']:.1f}% pass rate{rollback_note}")
        
        print("\n" + "=" * 80 + "\n")


class ReportGenerator:
    """Generates PDF reports"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=1
        )
    
    def generate_pdf_report(self, assessment_results, migration_plan, migration_results=None, test_results=None):
        """Generate comprehensive PDF report"""
        logger.info("Generating PDF report...")
        
        pdf_file = OUTPUT_DIR / f"java_upgrade_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(str(pdf_file), pagesize=letter)
        story = []
        
        story.append(Paragraph("Java 17 Upgrade Report", self.title_style))
        story.append(Paragraph(f"American Express Enterprise Migration", self.styles['Heading2']))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        story.append(Paragraph("Executive Summary", self.styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Applications', str(len(assessment_results))],
            ['High Risk Apps', str(sum(1 for r in assessment_results if r['risk_level'] == 'high'))],
            ['Medium Risk Apps', str(sum(1 for r in assessment_results if r['risk_level'] == 'medium'))],
            ['Low Risk Apps', str(sum(1 for r in assessment_results if r['risk_level'] == 'low'))],
            ['Total Estimated Effort', f"{sum(r['estimated_effort_days'] for r in assessment_results):.1f} days"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(PageBreak())
        
        story.append(Paragraph("Application Risk Assessment", self.styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        risk_data = [['Application', 'Risk Level', 'Risk Score', 'Effort (days)']]
        for app in sorted(assessment_results, key=lambda x: x['risk_score'], reverse=True)[:10]:
            risk_data.append([
                app['app_name'],
                app['risk_level'].upper(),
                str(app['risk_score']),
                str(app['estimated_effort_days'])
            ])
        
        risk_table = Table(risk_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(risk_table)
        story.append(PageBreak())
        
        if migration_results:
            story.append(Paragraph("Migration Results", self.styles['Heading2']))
            story.append(Spacer(1, 0.2*inch))
            
            successful = sum(1 for r in migration_results if r['build_status'] == 'success')
            migration_summary = [
                ['Metric', 'Value'],
                ['Applications Migrated', str(len(migration_results))],
                ['Successful Builds', str(successful)],
                ['Failed Builds', str(len(migration_results) - successful)],
                ['Success Rate', f"{(successful/len(migration_results)*100):.1f}%"]
            ]
            
            migration_table = Table(migration_summary, colWidths=[3*inch, 2*inch])
            migration_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(migration_table)
            story.append(PageBreak())
        
        if test_results:
            story.append(Paragraph("Testing Results", self.styles['Heading2']))
            story.append(Spacer(1, 0.2*inch))
            
            passed = sum(1 for r in test_results if r['status'] == 'passed')
            total_tests = sum(r['unit_tests']['total'] + r['integration_tests']['total'] for r in test_results)
            total_passed = sum(r['unit_tests']['passed'] + r['integration_tests']['passed'] for r in test_results)
            
            test_summary = [
                ['Metric', 'Value'],
                ['Applications Tested', str(len(test_results))],
                ['Tests Passed', str(passed)],
                ['Tests Failed (Rolled Back)', str(len(test_results) - passed)],
                ['Total Test Cases', str(total_tests)],
                ['Test Cases Passed', str(total_passed)],
                ['Overall Pass Rate', f"{(total_passed/total_tests*100):.1f}%"]
            ]
            
            test_table = Table(test_summary, colWidths=[3*inch, 2*inch])
            test_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(test_table)
        
        doc.build(story)
        logger.success(f"PDF report generated: {pdf_file}")
        print(f"\n✓ PDF Report: {pdf_file}")
        
        return pdf_file


@click.command()
@click.option('--stage', type=click.Choice(['assessment', 'planning', 'migration', 'testing', 'all']), 
              required=True, help='Stage to execute')
@click.option('--apps', help='Comma-separated list of apps for migration/testing')
def main(stage, apps):
    """
    AmEx Java Upgrade CLI Tool
    
    Simulates Java 8 to Java 17 upgrade process for enterprise applications
    """
    
    logger.info(f"Starting AmEx Java Upgrade Tool - Stage: {stage}")
    
    inventory_file = DATA_DIR / "app_inventory.csv"
    
    if not inventory_file.exists():
        logger.error(f"Inventory file not found: {inventory_file}")
        sys.exit(1)
    
    assessment_results = None
    migration_plan = None
    migration_results = None
    test_results = None
    
    if stage in ['assessment', 'all']:
        logger.info("=" * 80)
        logger.info("PHASE 1: ASSESSMENT")
        logger.info("=" * 80)
        
        assessor = JavaUpgradeAssessment(inventory_file)
        if not assessor.load_inventory():
            sys.exit(1)
        
        assessment_results = assessor.analyze_compatibility_risks()
        assessor.generate_report()
    
    if stage in ['planning', 'all']:
        logger.info("=" * 80)
        logger.info("PHASE 2: PLANNING")
        logger.info("=" * 80)
        
        if not assessment_results:
            assessor = JavaUpgradeAssessment(inventory_file)
            assessor.load_inventory()
            assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        migration_plan = planner.generate_migration_plan()
    
    if stage in ['migration', 'all']:
        logger.info("=" * 80)
        logger.info("PHASE 3: MIGRATION SIMULATION")
        logger.info("=" * 80)
        
        if not migration_plan:
            if not assessment_results:
                assessor = JavaUpgradeAssessment(inventory_file)
                assessor.load_inventory()
                assessment_results = assessor.analyze_compatibility_risks()
            
            planner = JavaUpgradePlanner(assessment_results)
            migration_plan = planner.generate_migration_plan()
        
        if stage == 'migration' and apps:
            selected_apps = [app.strip() for app in apps.split(',')]
        else:
            selected_apps = [app['name'] for app in migration_plan['applications'][:3]]
        
        migrator = JavaUpgradeMigration(migration_plan, selected_apps)
        migration_results = migrator.simulate_migration()
    
    if stage in ['testing', 'all']:
        logger.info("=" * 80)
        logger.info("PHASE 4: TESTING")
        logger.info("=" * 80)
        
        if not migration_results:
            if not migration_plan:
                if not assessment_results:
                    assessor = JavaUpgradeAssessment(inventory_file)
                    assessor.load_inventory()
                    assessment_results = assessor.analyze_compatibility_risks()
                
                planner = JavaUpgradePlanner(assessment_results)
                migration_plan = planner.generate_migration_plan()
            
            if stage == 'testing' and apps:
                selected_apps = [app.strip() for app in apps.split(',')]
            else:
                selected_apps = [app['name'] for app in migration_plan['applications'][:3]]
            
            migrator = JavaUpgradeMigration(migration_plan, selected_apps)
            migration_results = migrator.simulate_migration()
        
        tester = JavaUpgradeTesting(migration_results)
        test_results = tester.run_tests()
    
    if stage == 'all':
        logger.info("=" * 80)
        logger.info("GENERATING COMPREHENSIVE PDF REPORT")
        logger.info("=" * 80)
        
        report_gen = ReportGenerator()
        report_gen.generate_pdf_report(assessment_results, migration_plan, migration_results, test_results)
    
    logger.success("AmEx Java Upgrade Tool completed successfully!")


if __name__ == '__main__':
    main()
