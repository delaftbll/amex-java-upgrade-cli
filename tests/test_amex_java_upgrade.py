"""
Unit tests for AmEx Java Upgrade CLI Tool
"""

import pytest
import pandas as pd
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from amex_java_upgrade import (
    JavaUpgradeAssessment,
    JavaUpgradePlanner,
    JavaUpgradeMigration,
    JavaUpgradeTesting,
    ReportGenerator
)


@pytest.fixture
def sample_inventory_file(tmp_path):
    """Create a sample inventory CSV file for testing"""
    csv_content = """app_name,current_java_version,dependencies,known_issues,lines_of_code,criticality
TestApp1,8,Spring Boot 2.3.0;javax.validation,javax namespace,10000,high
TestApp2,8,Spring Boot 2.5.0;javax.ws.rs,javax to jakarta migration needed,20000,medium
TestApp3,8,Spring Boot 2.1.0;javax.xml,Uses sun.misc.Unsafe,15000,low"""
    
    csv_file = tmp_path / "test_inventory.csv"
    csv_file.write_text(csv_content)
    return csv_file


class TestJavaUpgradeAssessment:
    """Test cases for JavaUpgradeAssessment class"""
    
    def test_load_inventory_success(self, sample_inventory_file):
        """Test successful loading of inventory file"""
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        result = assessor.load_inventory()
        
        assert result is True
        assert assessor.df is not None
        assert len(assessor.df) == 3
        assert 'app_name' in assessor.df.columns
    
    def test_load_inventory_failure(self):
        """Test loading of non-existent inventory file"""
        assessor = JavaUpgradeAssessment(Path("/nonexistent/file.csv"))
        result = assessor.load_inventory()
        
        assert result is False
        assert assessor.df is None
    
    def test_analyze_compatibility_risks(self, sample_inventory_file):
        """Test compatibility risk analysis"""
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        results = assessor.analyze_compatibility_risks()
        
        assert len(results) == 3
        assert all('app_name' in r for r in results)
        assert all('risk_level' in r for r in results)
        assert all('risk_score' in r for r in results)
        assert all('identified_risks' in r for r in results)
        assert all('estimated_effort_days' in r for r in results)
    
    def test_risk_level_calculation(self, sample_inventory_file):
        """Test risk level calculation logic"""
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        results = assessor.analyze_compatibility_risks()
        
        for result in results:
            if result['risk_score'] >= 10:
                assert result['risk_level'] == 'high'
            elif result['risk_score'] >= 5:
                assert result['risk_level'] == 'medium'
            else:
                assert result['risk_level'] == 'low'
    
    def test_javax_namespace_detection(self, sample_inventory_file):
        """Test detection of javax namespace issues"""
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        results = assessor.analyze_compatibility_risks()
        
        for result in results:
            if 'javax' in result['app_name'].lower() or any('javax' in str(risk) for risk in result['identified_risks']):
                assert any('javax' in str(risk).lower() for risk in result['identified_risks'])
    
    def test_spring_boot_version_extraction(self, sample_inventory_file):
        """Test Spring Boot version extraction"""
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        
        version = assessor._extract_spring_boot_version("Spring Boot 2.3.0;Hibernate")
        assert version == "2.3.0"
        
        version = assessor._extract_spring_boot_version("No Spring Boot here")
        assert version is None
    
    def test_spring_boot_compatibility_check(self, sample_inventory_file):
        """Test Spring Boot compatibility checking"""
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        
        assert assessor._is_spring_boot_incompatible("2.3.0") is True
        assert assessor._is_spring_boot_incompatible("2.5.0") is False
        assert assessor._is_spring_boot_incompatible("2.7.0") is False
        assert assessor._is_spring_boot_incompatible("3.0.0") is False
    
    def test_effort_estimation(self, sample_inventory_file):
        """Test effort estimation calculation"""
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        
        effort = assessor._estimate_effort(5, 10000)
        assert effort > 0
        assert isinstance(effort, float)
        
        effort_high_risk = assessor._estimate_effort(10, 10000)
        effort_low_risk = assessor._estimate_effort(5, 10000)
        assert effort_high_risk > effort_low_risk
    
    def test_generate_report(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test report generation"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessor.analyze_compatibility_risks()
        report = assessor.generate_report()
        
        assert report is not None
        assert "JAVA UPGRADE ASSESSMENT REPORT" in report
        assert "Total Applications Analyzed" in report
        assert "RECOMMENDATIONS" in report


class TestJavaUpgradePlanner:
    """Test cases for JavaUpgradePlanner class"""
    
    def test_generate_migration_plan(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test migration plan generation"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        assert plan is not None
        assert 'plan_version' in plan
        assert 'total_applications' in plan
        assert 'migration_waves' in plan
        assert 'recommended_tools' in plan
        assert 'applications' in plan
        
        assert plan['total_applications'] == 3
        assert len(plan['applications']) == 3
    
    def test_migration_waves_creation(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test migration waves are created properly"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        assert len(plan['migration_waves']) > 0
        for wave in plan['migration_waves']:
            assert 'wave_number' in wave
            assert 'applications' in wave
            assert 'total_effort_days' in wave
            assert 'parallel_execution' in wave
    
    def test_recommended_tools_included(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test that recommended tools are included in plan"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        assert len(plan['recommended_tools']) > 0
        tool_names = [tool['name'] for tool in plan['recommended_tools']]
        assert 'OpenRewrite' in tool_names
        assert 'jdeps' in tool_names
    
    def test_migration_steps_generation(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test migration steps are generated for each app"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        for app in plan['applications']:
            assert 'migration_steps' in app
            assert len(app['migration_steps']) > 0
            assert 'rollback_strategy' in app
    
    def test_rollback_strategy_generation(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test rollback strategy is generated for each app"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        for app in plan['applications']:
            rollback = app['rollback_strategy']
            assert 'automated_rollback' in rollback
            assert 'rollback_triggers' in rollback
            assert 'rollback_steps' in rollback
            assert 'estimated_rollback_time_minutes' in rollback


class TestJavaUpgradeMigration:
    """Test cases for JavaUpgradeMigration class"""
    
    def test_simulate_migration(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test migration simulation"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        selected_apps = ['TestApp1']
        migrator = JavaUpgradeMigration(plan, selected_apps)
        results = migrator.simulate_migration()
        
        assert len(results) == 1
        assert results[0]['app_name'] == 'TestApp1'
        assert 'build_status' in results[0]
        assert 'steps_completed' in results[0]
        assert 'refactoring_changes' in results[0]
    
    def test_migration_with_multiple_apps(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test migration with multiple applications"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        selected_apps = ['TestApp1', 'TestApp2']
        migrator = JavaUpgradeMigration(plan, selected_apps)
        results = migrator.simulate_migration()
        
        assert len(results) == 2
        assert results[0]['app_name'] == 'TestApp1'
        assert results[1]['app_name'] == 'TestApp2'
    
    def test_migration_with_no_matching_apps(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test migration with non-existent apps"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        selected_apps = ['NonExistentApp']
        migrator = JavaUpgradeMigration(plan, selected_apps)
        results = migrator.simulate_migration()
        
        assert len(results) == 0
    
    def test_build_simulation(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test build simulation"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        migrator = JavaUpgradeMigration(plan, [])
        app = {'name': 'TestApp'}
        result = migrator._simulate_build(app)
        
        assert 'status' in result
        assert 'output' in result
        assert result['status'] in ['success', 'failed']


class TestJavaUpgradeTesting:
    """Test cases for JavaUpgradeTesting class"""
    
    def test_run_tests(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test running tests on migrated applications"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        selected_apps = ['TestApp1']
        migrator = JavaUpgradeMigration(plan, selected_apps)
        migration_results = migrator.simulate_migration()
        
        tester = JavaUpgradeTesting(migration_results)
        test_results = tester.run_tests()
        
        assert len(test_results) > 0
        for result in test_results:
            assert 'app_name' in result
            assert 'unit_tests' in result
            assert 'integration_tests' in result
            assert 'overall_pass_rate' in result
            assert 'status' in result
    
    def test_test_results_structure(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test structure of test results"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        selected_apps = ['TestApp1']
        migrator = JavaUpgradeMigration(plan, selected_apps)
        migration_results = migrator.simulate_migration()
        
        tester = JavaUpgradeTesting(migration_results)
        test_results = tester.run_tests()
        
        for result in test_results:
            assert 'total' in result['unit_tests']
            assert 'passed' in result['unit_tests']
            assert 'failed' in result['unit_tests']
            assert 'pass_rate' in result['unit_tests']
            
            assert 'total' in result['integration_tests']
            assert 'passed' in result['integration_tests']
            assert 'failed' in result['integration_tests']
            assert 'pass_rate' in result['integration_tests']
    
    def test_rollback_simulation(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test rollback simulation when tests fail"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        tester = JavaUpgradeTesting([])
        rollback = tester._simulate_rollback('TestApp')
        
        assert rollback is not None
        assert 'triggered' in rollback
        assert 'reason' in rollback
        assert 'completed_at' in rollback
        assert 'status' in rollback
        assert rollback['triggered'] is True


class TestReportGenerator:
    """Test cases for ReportGenerator class"""
    
    def test_generate_pdf_report(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test PDF report generation"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        report_gen = ReportGenerator()
        pdf_file = report_gen.generate_pdf_report(assessment_results, plan)
        
        assert pdf_file is not None
        assert pdf_file.exists()
        assert pdf_file.suffix == '.pdf'
    
    def test_pdf_report_with_migration_results(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test PDF report generation with migration results"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        selected_apps = ['TestApp1']
        migrator = JavaUpgradeMigration(plan, selected_apps)
        migration_results = migrator.simulate_migration()
        
        report_gen = ReportGenerator()
        pdf_file = report_gen.generate_pdf_report(assessment_results, plan, migration_results)
        
        assert pdf_file is not None
        assert pdf_file.exists()
    
    def test_pdf_report_with_test_results(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test PDF report generation with test results"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        selected_apps = ['TestApp1']
        migrator = JavaUpgradeMigration(plan, selected_apps)
        migration_results = migrator.simulate_migration()
        
        tester = JavaUpgradeTesting(migration_results)
        test_results = tester.run_tests()
        
        report_gen = ReportGenerator()
        pdf_file = report_gen.generate_pdf_report(assessment_results, plan, migration_results, test_results)
        
        assert pdf_file is not None
        assert pdf_file.exists()


class TestIntegration:
    """Integration tests for end-to-end workflows"""
    
    def test_full_workflow(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test complete workflow from assessment to testing"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assert assessor.load_inventory() is True
        
        assessment_results = assessor.analyze_compatibility_risks()
        assert len(assessment_results) == 3
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        assert plan is not None
        
        selected_apps = ['TestApp1']
        migrator = JavaUpgradeMigration(plan, selected_apps)
        migration_results = migrator.simulate_migration()
        assert len(migration_results) == 1
        
        tester = JavaUpgradeTesting(migration_results)
        test_results = tester.run_tests()
        assert len(test_results) > 0
        
        report_gen = ReportGenerator()
        pdf_file = report_gen.generate_pdf_report(assessment_results, plan, migration_results, test_results)
        assert pdf_file.exists()
    
    def test_assessment_to_planning(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test workflow from assessment to planning"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        assert len(plan['applications']) == len(assessment_results)
        
        assessment_names = {r['app_name'] for r in assessment_results}
        plan_names = {app['name'] for app in plan['applications']}
        assert assessment_names == plan_names
        
        for app in plan['applications']:
            matching_assessment = next(r for r in assessment_results if r['app_name'] == app['name'])
            assert app['risk_level'] == matching_assessment['risk_level']
    
    def test_planning_to_migration(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test workflow from planning to migration"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        app_names = [app['name'] for app in plan['applications']]
        migrator = JavaUpgradeMigration(plan, app_names[:2])
        migration_results = migrator.simulate_migration()
        
        assert len(migration_results) == 2
        for result in migration_results:
            assert result['app_name'] in app_names
    
    def test_migration_to_testing(self, sample_inventory_file, tmp_path, monkeypatch):
        """Test workflow from migration to testing"""
        monkeypatch.setattr('amex_java_upgrade.OUTPUT_DIR', tmp_path)
        
        assessor = JavaUpgradeAssessment(sample_inventory_file)
        assessor.load_inventory()
        assessment_results = assessor.analyze_compatibility_risks()
        
        planner = JavaUpgradePlanner(assessment_results)
        plan = planner.generate_migration_plan()
        
        selected_apps = ['TestApp1', 'TestApp2']
        migrator = JavaUpgradeMigration(plan, selected_apps)
        migration_results = migrator.simulate_migration()
        
        tester = JavaUpgradeTesting(migration_results)
        test_results = tester.run_tests()
        
        assert len(test_results) == len([r for r in migration_results if r['build_status'] == 'success'])
