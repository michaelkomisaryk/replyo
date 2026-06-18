from pathlib import Path

from django.test import SimpleTestCase

REPO_ROOT = Path(__file__).resolve().parents[4]


class DeploymentConfigTests(SimpleTestCase):
    def test_dockerfile_exists(self):
        self.assertTrue((REPO_ROOT / "Dockerfile").is_file())

    def test_start_script_exists_and_is_executable(self):
        start_script = REPO_ROOT / "backend" / "scripts" / "start.sh"
        self.assertTrue(start_script.is_file())
        self.assertTrue(start_script.stat().st_mode & 0o111)

    def test_render_blueprint_exists(self):
        self.assertTrue((REPO_ROOT / "render.yaml").is_file())

    def test_railway_config_exists(self):
        self.assertTrue((REPO_ROOT / "railway.toml").is_file())

    def test_vercel_config_exists(self):
        self.assertTrue((REPO_ROOT / "frontend" / "vercel.json").is_file())

    def test_deployment_docs_exist(self):
        self.assertTrue((REPO_ROOT / "docs" / "deployment.md").is_file())

    def test_smoke_test_script_exists(self):
        self.assertTrue((REPO_ROOT / "scripts" / "smoke_test_production.py").is_file())
